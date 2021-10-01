from plan_metrics import PlanMetrics
from gerrychain import Graph, Election
from gerrychain.updaters import Tally
from tqdm import tqdm
from pcompress import Replay
import argparse
import json
from configuration import *


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
args = parser.parse_args()

## Read in args and state specifications
state = args.st
plan_type = args.map
steps = args.n
county_aware = args.county_aware
method = "county_aware" if county_aware else "neutral"
how_verbose = args.verbose

with open("{}/{}.json".format(STATE_SPECS_DIR, state)) as fin:
    state_specification = json.load(fin)

k = state_specification["districts"][plan_type]
eps = state_specification["epsilons"][plan_type]
dual_graph_file = "{}/{}".format(DUAL_GRAPH_DIR, state_specification["dual_graph"])
pop_col = state_specification["pop_col"]
county_col = state_specification["county_col"]
party = state_specification["pov_party"]
elections = state_specification["elections"]
demographic_cols = state_specification["demographic_cols"]


# path_long = "mi_chains/mi_cong_0.01_bal_10000_steps_non_county_aware.chain"
chain_path = "{}/{}/{}_{}_{}_bal_{}_steps_{}.chain".format(state, CHAIN_DIR, state.lower(), plan_type,
                                                           eps, steps, method)
output_path = "{}/{}/{}_{}_{}_bal_{}_steps_{}.jsonl".format(state, STATS_DIR, state.lower(), plan_type,
                                                           eps, steps, method)



election_names = [e["name"] for e in elections]
## sort candidates alphabetically so that the "first" party is consistent.
election_updaters = {e["name"]: Election(e["name"], {c["name"]: c["key"] for c in sorted(e["candidates"], 
                                                                                         key=lambda c: c["name"])})
                    for e in elections}
demographic_updaters = {demo_col: Tally(demo_col, alias=demo_col) for demo_col in demographic_cols}

graph = Graph.from_json(dual_graph_file)

scores = PlanMetrics(graph, election_names, party, pop_col, updaters=election_updaters, county_col=county_col)


with open(output_path, "w") as fout:
    plan_generator = Replay(graph, chain_path, {**demographic_updaters, **election_updaters})
    part = next(plan_generator)

    header = json.dumps(scores.summary_data(elections, part.parts.keys(), eps, method))
    plan_details = json.dumps(scores.plan_summary(part))
    print(header, file=fout)
    print(plan_details, file=fout)

    if how_verbose >= 2:
        for part in tqdm(plan_generator):
            plan_details = json.dumps(scores.plan_summary(part))
            print(plan_details, file=fout)
    else:
        for i, part in enumerate(plan_generator):
            if how_verbose > 0 and i % 100 == 100 - 1:
                print("*", end="", flush=True)
            plan_details = json.dumps(scores.plan_summary(part))
            print(plan_details, file=fout)
