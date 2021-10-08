from gerrychain import Graph
import argparse
import json
from plan_evaluation import ChainRecorder
from plan_evaluation.configuration import *


parser = argparse.ArgumentParser(description="VTD Ensemble Recorder", 
                                 prog="run_ensemble.py")
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
parser.add_argument("--quiet", dest="verbosity", action="store_const", const=None, default=100,
                    help="Silence * tracker of chain position?")
args = parser.parse_args()

## Read in args and state specifications
state = args.st
plan_type = args.map
steps = args.n
county_aware = args.county_aware
county_aware_str = "county_aware" if county_aware else "neutral"
output_dir = "{}/{}".format(state, CHAIN_DIR)
verbose_freq = args.verbosity

with open("{}/{}.json".format(STATE_SPECS_DIR, state)) as fin:
    state_specification = json.load(fin)

k = state_specification["districts"][plan_type]
eps = state_specification["epsilons"][plan_type]
dual_graph_file = "{}/{}".format(DUAL_GRAPH_DIR, state_specification["dual_graph"])
pop_col = state_specification["pop_col"]
county_col = state_specification["county_col"]


## Run and Record Chain
graph = Graph.from_json(dual_graph_file)
rec = ChainRecorder(graph, output_dir, pop_col, county_col, verbose_freq=verbose_freq)

rec.record_chain(k, eps, steps,"{}_{}_{}_bal_{}_steps_{}.chain".format(state.lower(), plan_type,
                                                                       eps, steps, county_aware_str),
                         county_aware=county_aware)