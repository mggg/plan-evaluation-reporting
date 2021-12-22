import pandas as pd
import geopandas as gpd
from math import pi

def polsby_per_dist(plan_on_blocks, block_shp):
    """
    Takes a plan on blocks, dissolves the geometries down to the district level, and computes the polsby popper score.

    Args:
        plan_on_blocks: Assignment csv for a plan on blocks. Assumes that columns are named "GEOID20" and "assignment".
        block_shp: Shapefile for the state on blocks.

    Returns: 
         Dictionary mapping each district in the plan to its polsby popper score.
    """
    plan = pd.read_csv(plan_on_blocks, dtype={"GEOID20":"str"})
    state_shp = gpd.read_file(block_shp, dtype={"GEOID20":"str"})
  
    plan = plan.merge(state_shp, on = "GEOID20") 
    dissolved_plan = plan.dissolve(by="assignment")
 
    polsby_dict = {row.assignment: (4*pi*row.geometry.area)/(row.geometry.length**2)) for idx, row in dissolved_plan.iterrows()}
    return polsby_dict
 


