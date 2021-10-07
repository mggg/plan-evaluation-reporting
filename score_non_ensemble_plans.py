from plan_metrics import PlanMetrics
from gerrychain import Graph, Election, Partition
from gerrychain.updaters import Tally
import pandas as pd
from tqdm import tqdm
import argparse
import json
import warnings
from configuration import *
from glob import glob
from functools import reduce

SUPPORTED_METRIC_IDS = list(SUPPORTED_METRICS.keys())

parser = argparse.ArgumentParser(description="VTD Plan Scorer", 
                                 prog="score_non_ensemble_plans.py")
parser.add_argument("st", metavar="state", type=str,
                    choices=SUPPORTED_STATES,
                    help="Which state to run the ensemble on?")
parser.add_argument("map", metavar="map", type=str,
                    choices=SUPPORTED_PLAN_TYPES,
                    help="the map to redistrict")
parser.add_argument("--proposed_plan_dirs", type=str, nargs="*", metavar="proposed plan directory",
                    help="list of directories with proposed plan CSVs", default=[])
parser.add_argument("--citizen_plans_dirs", type=str, nargs="*", metavar="citzen plan directory",
                    help="list of directories with citizen plan CSVs", default=[])
args = parser.parse_args()

STATE = args.st
PLAN_TYPE = args.map
proposed_dirs = args.proposed_plan_dirs
citizen_dirs = args.citizen_plans_dirs


with open("{}/{}.json".format(STATE_SPECS_DIR, STATE)) as fin:
    state_specification = json.load(fin)

k = state_specification["districts"][PLAN_TYPE]
eps = state_specification["epsilons"][PLAN_TYPE]
dual_graph_file = "{}/{}".format(DUAL_GRAPH_DIR, state_specification["dual_graph"])
pop_col = state_specification["pop_col"]
county_col = state_specification["county_col"]
party = state_specification["pov_party"]
elections = state_specification["elections"]
demographic_cols = [m["id"] for m in state_specification["metrics"] if "type" in m and m["type"] == "col_tally"]
state_metric_ids = set([m["id"] for m in state_specification["metrics"] if "type" not in m or m["type"] != "col_tally"])
state_metrics = [{**m, "type": SUPPORTED_METRICS["col_tally"]} if ("type" in m and m["type"] == "col_tally") \
                                                               else {**m, "type": SUPPORTED_METRICS[m["id"]]} \
                    for m in filter(lambda m: m["id"] in SUPPORTED_METRIC_IDS or ("type" in m and m["type"] == "col_tally"), 
                                    state_specification["metrics"])]


if len(state_metric_ids - set(SUPPORTED_METRIC_IDS)) > 0:
    warnings.warn("Some state metrics are not supported.  Will continue without tracking them.\n.\
                  Unsupported metrics: {}".format(str(state_metric_ids - set(SUPPORTED_METRIC_IDS))))

election_names = [e["name"] for e in elections]
## sort candidates alphabetically so that the "first" party is consistent.
election_updaters = {e["name"]: Election(e["name"], {c["name"]: c["key"] for c in sorted(e["candidates"], 
                                                                                         key=lambda c: c["name"])})
                    for e in elections}
demographic_updaters = {demo_col: Tally(demo_col, alias=demo_col) for demo_col in demographic_cols}

graph = Graph.from_json(dual_graph_file)

scores = PlanMetrics(graph, election_names, party, pop_col, state_metrics, updaters=election_updaters, 
                     county_col=county_col, demographic_cols=demographic_cols)


if proposed_dirs != []:
    with open(f"{STATE}/plan_stats/{PLAN_TYPE}_proposed_plans.jsonl", "w") as fout:
        print(json.dumps(scores.summary_data(elections, num_districts=k, ensemble=False)), file=fout)
        plans = reduce(lambda acc, proposed_dir: acc + glob(f"{proposed_dir}/*.csv"), proposed_dirs, [])
        for plan_path in tqdm(plans):
            name = plan_path.split("/")[-1].split(".csv")[0]
            plan = pd.read_csv(plan_path, header=None,  index_col=0).to_dict()[1]
            ddict = {n: plan[graph.nodes()[n]["GEOID20"]] for n in graph.nodes()}
            part = Partition(graph, ddict, {**election_updaters, **demographic_updaters})
            print(json.dumps(scores.plan_summary(part, plan_type="proposed_plan", 
                                            plan_name=name)), file=fout)

if citizen_dirs != []:
    with open(f"{STATE}/plan_stats/{PLAN_TYPE}_citizen_plans.jsonl", "w") as fout:
        print(json.dumps(scores.summary_data(elections, num_districts=k, ensemble=False)), file=fout)
        plans = reduce(lambda acc, citizen_dir: acc + glob(f"{citizen_dir}/*.csv"), citizen_dirs, [])
        for plan_path in tqdm(plans):
            plan = pd.read_csv(plan_path, header=None,  index_col=0).to_dict()[1]
            ddict = {n: plan[graph.nodes()[n]["GEOID20"]] for n in graph.nodes()}
            part = Partition(graph, ddict, {**election_updaters, **demographic_updaters})
            print(json.dumps(scores.plan_summary(part, plan_type="citizen_plan")), file=fout)