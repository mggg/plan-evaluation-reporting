from gerrychain import Graph
from record_chains import ChainRecorder
import argparse


parser = argparse.ArgumentParser(description="VTD Ensembles for MI", 
                                 prog="run_mi_chain.py")
parser.add_argument("map", metavar="map", type=str,
                    choices=["congress", "state_senate", "state_house"],
                    help="the map to redistrict")
parser.add_argument("n", metavar="iterations", type=int,
                    help="the number of steps to take")
parser.add_argument("--county_aware", action='store_const', const=True, default=False,
                    dest="county_aware",
                    help="Chain builds districts with awareness of counties? (default Flase)")
args = parser.parse_args()

## Read in MI
graph = Graph.from_json("../dual_graphs/mi_vtds_0_indexed.json")
rec = ChainRecorder(graph, "mi_chains", "TOTPOP", "COUNTY", verbose_freq=100)

plan_type = args.map
districts = {"congress": 13, "state_senate": 38, "state_house": 110}
epsilons = {"congress": 0.01, "state_senate": 0.02, "state_house": 0.05}
k = districts[plan_type]
eps = epsilons[plan_type]
steps = args.n
county_aware = args.county_aware
county_aware_str = "county_aware" if county_aware else "neutral"

rec.record_chain(k, eps, steps,"mi_{}_{}_bal_{}_steps_{}.chain".format(plan_type, eps, steps,
                                                                       county_aware_str),
                         county_aware=county_aware)