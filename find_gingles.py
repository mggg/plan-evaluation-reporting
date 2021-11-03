from gerrychain import Graph, Partition
from gerrychain.updaters import Tally
from gerrychain.tree import recursive_tree_part
import pandas as pd
import argparse
import json
from configuration import *
from gingleator import Gingleator
import numpy as np

parser = argparse.ArgumentParser(description="VTD Ensemble Recorder", 
                                 prog="run_ensemble.py")
parser.add_argument("st", metavar="state", type=str,
                    choices=SUPPORTED_STATES,
                    help="Which state to run the ensemble on?")
parser.add_argument("map", metavar="map", type=str,
                    choices=SUPPORTED_PLAN_TYPES,
                    help="the map to redistrict")
parser.add_argument("min_vap_col", metavar="Min VAP", type=str,
                    help="which vap column to gingelate on?")
parser.add_argument("n", metavar="iters", type=int,
                    help="Number of Total steps"),
parser.add_argument("burst_length", metavar="burst_length", type=int,
                    help="length of each burst"),
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
burst_len = args.burst_length
min_vap_col = args.min_vap_col
print(min_vap_col, flush=True)


with open("{}/{}.json".format(STATE_SPECS_DIR, state)) as fin:
    state_specification = json.load(fin)

k = state_specification["districts"][plan_type]
eps = state_specification["epsilons"][plan_type]
dual_graph_file = "{}/{}".format(DUAL_GRAPH_DIR, state_specification["dual_graph"])
pop_col = state_specification["pop_col"]
vap_col = state_specification["vap_col"]
county_col = state_specification["county_col"]


SCORE_FUNC = Gingleator.reward_partial_dist
graph = Graph.from_json(dual_graph_file)

my_updaters = {"population" : Tally(pop_col, alias="population"),
               vap_col: Tally(vap_col),
               min_vap_col: Tally(min_vap_col)}

total_pop = sum([graph.nodes()[n][pop_col] for n in graph.nodes()])
ideal_pop = total_pop / k

cddict = recursive_tree_part(graph, range(k), ideal_pop, pop_col, eps)

init_partition = Partition(graph, assignment=cddict, updaters=my_updaters)


gingles = Gingleator(init_partition, pop_col=pop_col,
                     threshold=0.5, score_funct=SCORE_FUNC, epsilon=eps,
                     minority_perc_col="{}_perc".format(min_vap_col))

gingles.init_minority_perc_col(min_vap_col, vap_col, 
                               "{}_perc".format(min_vap_col))

num_bursts = int(steps/burst_len)

sb_obs = gingles.short_burst_run(num_bursts=num_bursts, num_steps=burst_len,
                                     maximize=True, verbose=True)
np.save("{}/short_bursts/{}_{}_{}_bal_{}_steps_{}_burstlen_{}_{}.npy".format(state, state.lower(), 
                                     plan_type, eps, steps, burst_len, county_aware_str, min_vap_col), sb_obs[1])

with open("{}/short_bursts/{}_{}_{}_bal_{}_steps_{}_burstlen_{}_{}_max_part.json".format(state, state.lower(), plan_type, eps, steps, burst_len, county_aware_str, min_vap_col), "w") as fout:
    json.dump(dict(sb_obs[0][0].assignment), fout)