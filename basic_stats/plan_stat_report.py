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
  
  #print(assignment)
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
  

block_graph = Graph.from_json("al_block.json")
#vtd_graph = Graph.from_json("NC_block.json")

files = glob.glob("al_plans/*.csv")
print(files)

c_plan_df = pd.DataFrame()
plans = []
contig_blocks = []
contig_vtds = []
cut_edges_blocks = []
total_edges_blocks = []
polsby_blocks = []
cut_edges_vtds = []
total_edges_vtds = []
polsby_vtds = []
pos_dev = []
pos_dev_district = []
neg_dev = []
neg_dev_district = []
vtds = []
avg_density_blocks = []
max_min_density_blocks = []
contig = []

polsby_df = pd.DataFrame(columns=files)
for file in files:
  f = pd.read_csv(file)
  polsby = plan_stat_report(file, block_graph, "TOTPOP20")
  print(file, polsby)

"""
for file in files:
    if "_block" not in file: 
        print(file)
        f = pd.read_csv(file)
        f.to_csv(file, index=False)
        p_number = file.split(".csv")[0]
        p_number = p_number.split("/")[-1]
        plans.append(p_number)
        plan_dict = plan_stat_report(file, block_graph, "TOTPOP20")
        print(plan_dict)
        cut_edges_blocks.append(plan_dict["Cut Edges"])
        total_edges_blocks.append(plan_dict["Total Edges"])
        polsby_blocks.append(round(plan_dict["Polsby popper"], 3))
        pos_dev.append(plan_dict["Max Pop Deviation"])
        pos_dev_district.append(plan_dict["Max District"])
        neg_dev.append(plan_dict["Min Pop Deviation"])
        neg_dev_district.append(plan_dict["Min District"])
#         avg_density_blocks.append(round(plan_dict["Average Density"]*2589988.1103, 3))
#         max_min_density_blocks.append(round(plan_dict["Max/Min Density"], 3))
#        contig_blocks.append(plan_dict["Contiguous"])
#        vtd_file = file.split("_block.csv")[0]+ ".csv"
#        plan_dict_vtd = psr(vtd_file, vtd_graph, "TOTPOP")
#        cut_edges_vtds.append(plan_dict_vtd["Cut Edges"])
#        total_edges_vtds.append(plan_dict_vtd["Total Edges"])
#        polsby_vtds.append(round(plan_dict_vtd["Polsby popper"], 3))
#        contig_vtds.append(plan_dict_vtd["Contiguous"])
    
        plan = pd.read_csv(file, dtype={"GEOID20": "str", "assignment": int}).set_index("GEOID20").to_dict()['assignment']

        with open("al_blocks_to_vtds.json", "r") as f:
             ut_vtd_block_mapping = json.load(f)

    
        vtd_to_districts = {}
        vtd_num_districts = {}
        for vtd, blocks in ut_vtd_block_mapping.items():
            block_mapping = [plan[block] for block in blocks]

            if len(set(block_mapping)) > 1: 
                 vtd_to_districts[vtd] = set(block_mapping)


        print(len(vtd_to_districts.keys()))
        vtds.append(len(vtd_to_districts.keys()))
    
c_plan_df["Plan"] = plans

c_plan_df["Total Edges on Blocks"] = total_edges_blocks
c_plan_df["Cut Edges on Blocks"] = cut_edges_blocks
c_plan_df["Polsby Popper on Blocks"] = polsby_blocks
c_plan_df["Max Positive Dev"] = pos_dev
c_plan_df["Max Positive Dev District"] = pos_dev_district
c_plan_df["Max Negative Dev"] = neg_dev
c_plan_df["Max Negative Dev District"] = neg_dev_district
#c_plan_df["Total Edges on VTDs"] = total_edges_vtds
#c_plan_df["Cut Edges on VTDs"] = cut_edges_vtds
#c_plan_df["Polsby Popper on VTDs"] = polsby_vtds
c_plan_df["VTD Splits"] = vtds
# c_plan_df["Average Density"] = avg_density_blocks
# c_plan_df["Max Min Density"] = max_min_density_blocks

c_plan_df.to_csv("AL_CCC_basic_stats_1128.csv", index=False)
"""
