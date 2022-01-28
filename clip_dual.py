from gerrychain import Graph
import pandas as pd

def clip_dual_graph(assignment_csv, dual_graph):
  plan = pd.read_csv(assignment_csv, dtype={"GEOID20":"str"})

  graph = Graph.from_json(dual_graph)

  ids_to_keep = [id for id, n in enumerate(graph.nodes()) if graph.nodes()[n]["GEOID20"] in list(plan.GEOID20.unique())]

  id_dict = {ids_to_keep[i]: i for i in range(len(ids_to_keep))}
  
  new_adjacencies = []
  for node, adj in enumerate(graph.adjacency()):
    if node in ids_to_keep:
      new_node_adj = []
      for shared_perim in adj:
        if shared_perim["id"] not in ids_to_keep:
          if "boundary_perim" in graph.nodes()[node].keys():
            graph.nodes()[node]["boundary_perim"] += shared_perim["shared_perim"]
          else:
            graph.nodes()[node]["boundary_perim"] = shared_perim["shared_perim"]
          if graph.nodes()[node]["boundary_node"] == False:
            graph.nodes()[node]["boundary_node"] = True   
        else:
          shared_perim["id"] = id_dict[shared_perim["id"]]
          new_node_adj.append(shared_perim)
      new_adjacencies.append(new_node_adj)
  
  nodes_to_keep = [graph.nodes()[n] for n in graph.nodes() if graph.nodes()[n]["GEOID20"] in list(plan.GEOID20.unique())]
  for id, node in enumerate(nodes_to_keep):
    node["id"] = id

  dual_dict = {"directed": json_f["directed"], "multigraph": json_f["multigraph"], "graph": json_f["graph"], "nodes":nodes_to_keep, "adjacency":new_adjacencies}
  return dual_dict

