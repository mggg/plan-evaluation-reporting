import json
import pandas as pd
import geopandas as gpd
import time
import tqdm

def get_blocks_by_VTD(baf, state_fips, state):
    """
    Uses the census BAF block to vtd mapping to create a json file of  blocks to vtds. For each vtd, the file will have the list of blocks it contains
    
    :param baf: Block assignment file from census
    :param state_fips: The FIPS code for the state
    :param state: The abbreviation for the state 

    """

    block_to_VTD = pd.read_csv(baf, sep="|", dtype = {"DISTRICT": "str", "COUNTYFP": "str"})
    block_to_VTD["VTD"] = str(state_fips) + block_to_VTD.COUNTYFP.str.cat(block_to_VTD.DISTRICT)

    blocks_by_VTD = {vtd: set() for vtd in block_to_VTD["VTD"]}
    for vtd in tqdm.tqdm(blocks_by_VTD.keys()):
        blocks_by_VTD[vtd] = list(set(block_to_VTD[block_to_VTD.VTD == vtd].BLOCKID.unique().astype('str')))

    with open(f"{state}_blocks_to_vtds.json", "w") as f:
        json.dump(blocks_by_VTD, f)
    return blocks_by_VTD


def vtd_splits(json_mapping_file, block_assignment_csv): 
  """
  Takes the json block to vtd mapping created from get_blocks_by_VTD. 
  :param json_mapping_file: The mapping file from vtds to blocks. 
  :param block_assignment_csv: The block assignment csv file from the state.
  """

  f =  open(json_mapping_file, "r") 
  state_vtd_to_block_mapping = json.load(f) 

  plan_df = pd.read_csv(block_assignment_csv, dtype={"GEOID20": 'str', "assignment": int})
  plan = plan_df.set_index("GEOID20").to_dict()['assignment']
  vtd_to_districts = {}

  for vtd, blocks in state_vtd_to_block_mapping.items():
    block_mapping = [plan[str(block)] for block in blocks] 
    if len(set(block_mapping)) > 1: 
      vtd_to_districts[vtd] = set(block_mapping)

    num_splits = len(vtd_to_districts.keys())

  return num_splits 
print(vtd_splits("nc_blocks_to_vtds.json", "NC_alt/Alt-House_block.csv"))
