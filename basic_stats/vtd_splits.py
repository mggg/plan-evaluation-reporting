import json
import pandas as pd


def vtd_splits(json_mapping_file, block_assignment_csv) -> int:
    """
        Uses a block to vtd mapping file to calculate and output the number of VTDs that are split by a plan. The plan must be on blocks.

        Args: 
            json_mapping_file: The mapping file from vtds to blocks. 
            block_assignment_csv: The block assignment csv file for the plan.

        Returns: 
            num_splits: The number of VTDs split by the plan.
    """

    f =  open(json_mapping_file, "r") 
    state_vtd_to_block_mapping = json.load(f) 

    plan_df = pd.read_csv(block_assignment_csv, dtype={"GEOID20": 'str', "assignment": int}).set_index("GEOID20").to_dict()['assignment']
    vtd_to_districts = {}

    for vtd, blocks in tqdm.tqdm(state_vtd_to_block_mapping.items()):
        block_mapping = [plan[str(block)] for block in blocks] 

        if len(set(block_mapping)) > 1: 
            vtd_to_districts[vtd] = set(block_mapping)

        num_splits = len(vtd_to_districts.keys())

  return num_splits 


