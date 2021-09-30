from plan_metrics import PlanMetrics
from gerrychain import Graph, Partition, Election
from gerrychain import updaters, metrics
from gerrychain.updaters.cut_edges import cut_edges
from gerrychain.updaters import Tally
import numpy as np
from tqdm import tqdm
from pcompress import Replay
import networkx as nx
import matplotlib.pyplot as plt
import json

districts = {"congress": 13, "state_senate": 38, "state_house": 110}
epsilons = {"congress": 0.01, "state_senate": 0.02, "state_house": 0.05}

ELECTS = [{"name": "GOV18", "candidates": [{"name": "Democratic", "key": "GOV18D"}, {"name": "Republican", "key": "GOV18R"}]},
          {"name": "SEN18", "candidates": [{"name": "Democratic", "key": "SEN18D"}, {"name": "Republican", "key": "SEN18R"}]},
          {"name": "SOS18", "candidates": [{"name": "Democratic", "key": "SOS18D"}, {"name": "Republican", "key": "SOS18R"}]},
          {"name": "AG18", "candidates": [{"name": "Democratic", "key": "AG18D"}, {"name": "Republican", "key": "AG18R"}]},
          {"name": "PRES16", "candidates": [{"name": "Democratic", "key": "PRES16D"}, {"name": "Republican", "key": "PRES16R"}]}]

PLAN_TYPE = "congress"
STEPS = 100
METHOD = "neutral"
PARTY = "Democratic"
POP_COL = "TOTPOP"
EPS = epsilons[PLAN_TYPE]

# path_long = "mi_chains/mi_cong_0.01_bal_10000_steps_non_county_aware.chain"
dual_graph_file = "../dual_graphs/mi_vtds_0_indexed.json"
path = "mi_chains/mi_{}_{}_bal_{}_steps_{}.chain".format(PLAN_TYPE, EPS, STEPS, METHOD)
pathout = "mi_chains/mi_{}_{}_bal_{}_steps_{}.jsonl".format(PLAN_TYPE, EPS, STEPS, METHOD)



election_names = [e["name"] for e in ELECTS]
## sort candidates alphabetically so that the "first" party is consistent.
election_updaters = {e["name"]: Election(e["name"], {c["name"]: c["key"] for c in sorted(e["candidates"], 
                                                                                         key=lambda c: c["name"])})
                    for e in ELECTS}
demographic_updaters = {demo_col: Tally(demo_col, alias=demo_col) for demo_col in PlanMetrics.DEMO_COLS}

graph = Graph.from_json(dual_graph_file)

scores = PlanMetrics(graph, election_names, PARTY, POP_COL, updaters=election_updaters)


with open(pathout, "w") as fout:
    header = json.dumps(scores.summary_data(ELECTS, districts[PLAN_TYPE], EPS, METHOD))
    print(header, file=fout)
    for part in tqdm(Replay(graph, path, {**demographic_updaters, **election_updaters})):
        plan_details = json.dumps(scores.plan_summary(part))
        print(plan_details, file=fout)
