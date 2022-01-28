from gerrychain import Graph
from pcompress import Replay
import pandas as pd
import os
import glob
import argparse
import json
from configuration import *

parser = argparse.ArgumentParser(description="Chain Saving", 
                                 prog="save_chains.py")
parser.add_argument("state", metavar="state", type=str,
                    choices=SUPPORTED_STATES, 
                    help="Which state do you want to save chains from?")
parser.add_argument("map", metavar="map", type=str,
                    choices=SUPPORTED_PLAN_TYPES,
                    help="the map to redistrict")
parser.add_argument("steps", metavar="steps", type=int, 
                    help="How many steps were in the chain?")
parser.add_argument("epsilon", metavar="epsilon", type=float, 
                    help="Population deviation percentage range?")
parser.add_argument("--county_aware", action='store_const', const=True, default=False,
                    dest="county_aware",
                    help="Chain builds districts with awareness of counties? (default False)")
parser.add_argument("--muni_aware", action='store_const', const=True, default=False,
                    dest="muni_aware",
                    help="Chain builds districts with awareness of munis? (default False)")
args = parser.parse_args()
steps = args.steps
state = args.state
map = args.map
epsilon = args.epsilon
county_aware = args.county_aware
muni_aware = args.muni_aware
county_aware_str = "county_aware" if county_aware else "neutral"
muni_aware_str = "muni_aware" if muni_aware else "neutral"

with open("{}/{}.json".format(STATE_SPECS_DIR, state)) as fin:
    state_specification = json.load(fin)

dual_graph = state_specification["dual_graph"]

graph = Graph.from_json(f"dual_graphs/{dual_graph}")
output_dir = f"{state}/chain_assignments/{steps}"
if not os.path.isdir(output_dir):
  os.makedirs(output_dir)


for i, partition in enumerate(Replay(graph, f"{state}/raw_chains/{state.lower()}_{map}_{epsilon}_bal_{steps}_steps_{county_aware_str}_{muni_aware_str}.chain", updaters=None)):
    if i%(steps/10) == 0:
      parts_dict = {partition.graph.nodes[n]["GEOID20"]: partition.assignment[n] for n in partition.graph.nodes}
      part = pd.DataFrame.from_dict(parts_dict, orient="index", columns=["assignment"]).reset_index()
      part = part.rename(columns={"index":"GEOID20"})
      p_name = f"{output_dir}/{state}_{steps}_{i}.csv"
      part.to_csv(p_name, index=False)
    
