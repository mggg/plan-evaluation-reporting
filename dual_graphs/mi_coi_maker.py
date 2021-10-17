import pandas as pd
import networkx as nx
import tqdm

mi_clusters = pd.read_csv("mi_clusters.csv")
graph = gerrychain.Graph.from_json("mi_vtds_0_indexed.json")

for col in tqdm.tqdm([x for x in mi_clusters.columns if "cluster" in x]):
    nx.set_node_attributes(graph, {int(k): int(v) for k, v in dict(mi_clusters[col]).items()}, name=str(col))
graph.to_json("mi_vtds_0_indexed_cois.json")
