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
import os

SUPPORTED_METRIC_IDS = list(SUPPORTED_METRICS.keys())
HOMEDIR = os.path.expanduser('~')

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
parser.add_argument("--citizen_plans_files", type=str, nargs="*", metavar="citzen plan files",
                    help="list of files with citizen plan CSVs", default=[])
parser.add_argument("--dropbox", action="store_const", const=True, default=False, 
                    help="Save the output files to dropbox folder? (default: save in this repo)")
args = parser.parse_args()

STATE = args.st
PLAN_TYPE = args.map
DROPBOX = args.dropbox
proposed_dirs = args.proposed_plan_dirs
citizen_paths = args.citizen_plans_files


with open("{}/{}.json".format(STATE_SPECS_DIR, STATE)) as fin:
    state_specification = json.load(fin)

k = state_specification["districts"][PLAN_TYPE]
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
municipality_col = state_specification["municipal_col"] if "num_municipal_pieces" in state_metric_ids or "num_split_municipalities" in state_metric_ids else None

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
                     county_col=county_col, demographic_cols=demographic_cols, municipality_col=municipality_col)

if DROPBOX:
    output_path_proposed = f"{HOMEDIR}/Dropbox/PlanAnalysis/proposed_plans/{STATE}/{PLAN_TYPE}/proposed_plans.jsonl"
    output_path_citizen = f"{STATE}/plan_stats/{STATE.lower()}_{PLAN_TYPE}_citizen_plans.jsonl"
else:
    output_path_proposed = f"{STATE}/plan_stats/{PLAN_TYPE}_proposed_plans.jsonl"
    output_path_citizen = f"{STATE}/plan_stats/{PLAN_TYPE}_citizen_plans.jsonl"

if proposed_dirs != []:
    with open(output_path_proposed, "w") as fout:
        print(json.dumps(scores.summary_data(elections, num_districts=k, ensemble=False)), file=fout)
        plans = reduce(lambda acc, proposed_dir: acc + glob(f"{proposed_dir}/*.csv"), proposed_dirs, [])
        for plan_path in tqdm(plans):
            name = plan_path.split("/")[-1].split(".csv")[0]
            plan = pd.read_csv(plan_path, dtype={"GEOID20": "str", "assignment": int}).set_index("GEOID20").to_dict()['assignment']
            ddict = {n: plan[graph.nodes()[n]["GEOID20"]] for n in graph.nodes()}
            part = Partition(graph, ddict, {**election_updaters, **demographic_updaters})
            print(json.dumps(scores.plan_summary(part, plan_type="proposed_plan", 
                                            plan_name=name)), file=fout)

if citizen_paths != []:
    with open(output_path_citizen, "w") as fout:
        print(json.dumps(scores.summary_data(elections, num_districts=k, ensemble=False)), file=fout)
        citizen_ens = reduce(lambda acc, citizen_ens: pd.merge(left=acc, right=citizen_ens, on="GEOID20"),
                            [pd.read_csv(citizen_ens, dtype={"GEOID20": "str"}).set_index("GEOID20") 
                                for citizen_ens in citizen_paths])
        
        plans = citizen_ens.to_dict()
        for plan_id, plan in tqdm(plans.items()):
            # try:
            ddict = {n: int(plan[graph.nodes()[n]["GEOID20"]]) for n in graph.nodes()}
            part = Partition(graph, ddict, {**election_updaters, **demographic_updaters})
            print(json.dumps(scores.plan_summary(part, plan_type="citizen_plan", plan_name=plan_id)), file=fout)
            # except:
            #     pass