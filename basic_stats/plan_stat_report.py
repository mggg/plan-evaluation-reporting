import geopandas as gpd 
import pandas as pd
import math
import tqdm
import glob
import os
import json

from gerrychain import Partition, Graph, GeographicPartition
from gerrychain.updaters import cut_edges, Tally, compactness, Election
import gerrychain
import warnings; warnings.filterwarnings('ignore', 'GeoSeries.isna', UserWarning)
from statistics import mean

def plan_stat_report(assignment_csv, graph, pop_key): 
  '''
  assignment_csv: Can contain the plan assignment on VTDs or blocks.
  state_shapefile: Shapefile for the state on blocks or VTDs.
  graph: Graph from json file of block dual graph or vtd dual graph. 
  '''
  assignment = pd.read_csv(assignment_csv, dtype={"GEOID20": "str", "assignment": int})
  assignment["GEOID20"] = "0" + assignment["GEOID20"]
  assignment = assignment.set_index("GEOID20").to_dict()['assignment']
  
  
  ddict = {n: assignment[graph.nodes()[n]["GEOID20"]] for n in graph.nodes()}
  total_population = sum([graph.nodes()[n][pop_key] for n in graph.nodes()])
  ideal_population = round(total_population/len(set(assignment.values())))
  state_partition = Partition(
    graph,
    assignment= ddict,
    updaters={
        "population": Tally(pop_key), 
        "area": Tally("area"), 
        "population_deviation": lambda part: {district: population-ideal_population for district, population in part["population"].items()},
        "pop_density": lambda part: {district: part["population"][district]/area for district, area in part["area"].items()} 
    }
  )
    

  state_geo_partition = GeographicPartition(
      graph, 
      assignment = ddict, 
      updaters={
          "cut_edges": cut_edges
      }
  )

  min_density = min(state_partition.pop_density.values())
  max_density = max(state_partition.pop_density.values())
  avg_density = mean(state_partition.pop_density.values())
  min_district, min_pop_deviation = min(state_partition.population_deviation.items(), key=lambda x: x[1])
  max_district, max_pop_deviation =max(state_partition.population_deviation.items(), key=lambda x: x[1])
  
  polsby = sum(gerrychain.metrics.polsby_popper(state_geo_partition).values()) / len(state_geo_partition.parts)
  return {"Contiguous": gerrychain.constraints.contiguous(state_partition), "Cut Edges": len(state_partition.cut_edges), "Total Edges": len(state_partition.graph.edges), "Polsby popper": polsby, "Max/Min Density": (max_density/min_density), "Average Density": avg_density, "Min Pop Deviation": round(min_pop_deviation), "Min District": min_district, "Max Pop Deviation": round(max_pop_deviation), "Max District": max_district}
  

