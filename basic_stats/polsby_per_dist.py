import pandas as pd
import geopandas as gpd
from math import pi

def polsby_per_dist(plan_on_blocks, block_shp):
  plan = pd.read_file(plan_on_blocks, dtype={"GEOID20":"str"})
  state_shp = gpd.read_file(block_shp, dtype={"GEOID20":"str"})
  plan = plan.merge(state_shp, on = "GEOID20")
  
  dissolved_plan = plan.dissolve(by="assignment")

  
  return [(row.assignment, (4*pi*row.geometry.area)/(row.geometry.length**2)) for idx, row in dissolved_plan.iterrows()]
  



