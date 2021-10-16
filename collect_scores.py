from os import stat
from plan_metrics import PlanMetrics
from gerrychain import Graph, Election
from gerrychain.updaters import Tally
from tqdm import tqdm
from pcompress import Replay
import argparse
import json
import gzip
import warnings
from configuration import *
from coi_updater import coi_updater

SUPPORTED_METRIC_IDS = list(SUPPORTED_METRICS.keys())

parser = argparse.ArgumentParser(description="VTD Ensemble Scorer", 
                                 prog="collect_scores.py")
parser.add_argument("st", metavar="state", type=str,
                    choices=SUPPORTED_STATES,
                    help="Which state to run the ensemble on?")
parser.add_argument("map", metavar="map", type=str,
                    choices=SUPPORTED_PLAN_TYPES,
                    help="the map to redistrict")
parser.add_argument("n", metavar="iterations", type=int,
                    help="the number of steps to take")
parser.add_argument("--county_aware", action='store_const', const=True, default=False,
                    dest="county_aware",
                    help="Chain builds districts with awareness of counties? (default False)")
parser.add_argument('--verbose', '-v', action='count', default=0)
parser.add_argument("--sub_sample", metavar="stride length", default=1, type=int, 
                    help="Stride length for sub-sampling the plan. Default is not to sub-sample.")
args = parser.parse_args()

## Read in args and state specifications
state = args.st
plan_type = args.map
steps = args.n
county_aware = args.county_aware
method = "county_aware" if county_aware else "neutral"
how_verbose = args.verbose
stride_len = args.sub_sample

with open("{}/{}.json".format(STATE_SPECS_DIR, state)) as fin:
    state_specification = json.load(fin)

k = state_specification["districts"][plan_type]
eps = state_specification["epsilons"][plan_type]
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

# path_long = "mi_chains/mi_cong_0.01_bal_10000_steps_non_county_aware.chain"
chain_path = "{}/{}/{}_{}_{}_bal_{}_steps_{}.chain".format(state, CHAIN_DIR, state.lower(), plan_type,
                                                           eps, steps, method)
output_path = "{}/{}/{}_{}_{}_bal_{}_steps_{}.jsonl.gz".format(state, STATS_DIR, state.lower(), plan_type,
                                                           eps, steps, method)

election_names = [e["name"] for e in elections]
## sort candidates alphabetically so that the "first" party is consistent.
election_updaters = {e["name"]: Election(e["name"], {c["name"]: c["key"] for c in sorted(e["candidates"], 
                                                                                         key=lambda c: c["name"])})
                    for e in elections}
demographic_updaters = {demo_col: Tally(demo_col, alias=demo_col) for demo_col in demographic_cols}

graph = Graph.from_json(dual_graph_file)

totpop = sum([graph.nodes[x][pop_col] for x in graph.nodes])
coi_updaters = {}
if state_specification.get("cois"):
    cluster_sizes = {}
    cluster_pops = [x for x in graph.nodes[0].keys() if "cluster" in x and "_pop" in x]

    for cluster_pop_col in cluster_pops:
        coi_updaters[cluster_pop_col] = Tally(cluster_pop_col)
        cluster_sizes[cluster_pop_col] = sum([graph.nodes[x][cluster_pop_col] for x in graph.nodes])
    coi_updaters["coi_metrics"] = coi_updater(cluster_pops, cluster_sizes, totpop)
    demographic_cols.append("coi_metrics")


scores = PlanMetrics(graph, election_names, party, pop_col, state_metrics, updaters=election_updaters, 
                     county_col=county_col, demographic_cols=demographic_cols)

with gzip.open(output_path, "wt") as fout:
    plan_generator = Replay(graph, chain_path, {**demographic_updaters, **election_updaters, **coi_updaters})
    part = next(plan_generator)

    header = json.dumps(scores.summary_data(elections, part.parts.keys(), eps, method)) + "\n"
    plan_details = json.dumps(scores.plan_summary(part)) + "\n"
    fout.write(header)
    fout.write(plan_details)

    if how_verbose >= 2:
        for i, part in enumerate(tqdm(plan_generator)):
            if i % stride_len == stride_len - 1:
                plan_details = json.dumps(scores.plan_summary(part)) + "\n"
                fout.write(plan_details)
    else:
        for i, part in enumerate(plan_generator):
            if i % stride_len == stride_len - 1:
                if how_verbose > 0 and i % 100 == 100 - 1:
                    print("*", end="", flush=True)
                plan_details = json.dumps(scores.plan_summary(part)) + "\n"
                fout.write(plan_details)
