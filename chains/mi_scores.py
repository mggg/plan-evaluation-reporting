from gerrychain import Graph, Partition, Election
from gerrychain import updaters, metrics
from gerrychain.updaters.cut_edges import cut_edges
import numpy as np
from tqdm import tqdm
from pcompress import Replay
import networkx as nx
import matplotlib.pyplot as plt


ELECTS = [{"name": "2018 Governor Election", "candidates": [{"name": "Democratic", "key": "GOV18D"}, {"name": "Republican", "key": "GOV18R"}]},
          {"name": "2018 Senate Election", "candidates": [{"name": "Democratic", "key": "SEN18D"}, {"name": "Republican", "key": "SEN18R"}]},
          {"name": "2018 Secretary of State Election", "candidates": [{"name": "Democratic", "key": "SOS18D"}, {"name": "Republican", "key": "SOS18R"}]},
          {"name": "2018 Attorney General Election", "candidates": [{"name": "Democratic", "key": "AG18D"}, {"name": "Republican", "key": "AG18R"}]},
          {"name": "2016 Presidential Election", "candidates": [{"name": "Democratic", "key": "PRES16D"}, {"name": "Republican", "key": "PRES16R"}]}]

election_names = [e["name"] for e in ELECTS]
## sort candidates alphabetically so that the "first" party is consistent.
election_updaters = {e["name"]: Election(e["name"], {c["name"]: c["key"] for c in sorted(e["candidates"], 
                                                                                         key=lambda c: c["name"])})
                    for e in ELECTS}

graph = Graph.from_json("../dual_graphs/mi_vtds_0_indexed.json")

# path_long = "mi_chains/mi_cong_0.01_bal_10000_steps_non_county_aware.chain"
path = "mi_chains/mi_congress_0.01_bal_100_steps_neutral.chain"

cutedges = []
for part in tqdm(Replay(graph, path, election_updaters)):
    cutedges.append(len(part["cut_edges"]))

plt.hist(cutedges)