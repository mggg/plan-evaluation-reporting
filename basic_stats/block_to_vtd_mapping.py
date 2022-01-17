import pandas as pd
import geopandas as gpd
import json
import glob
import tqdm

def block_to_vtd_csv(vtd_shp, block_shp, state_blocks_to_vtds, csv_directory):
	"""
	Uses a json file mapping blocks to vtds to do a conversion from a block assignment file to a vtd assignment file. 
	If a vtd is assigned to multiple districts, then it is put in the district with the maximum population overlap.
        Outputs the vtd assignment file in the passed csv directory.

        Args:
            vtd_shp: Shapefile for the state on vtds
	    block_shp: Shapefile for the state on blocks
	    state_blocks_to_vtds: Json file outlining the mapping for vtds to blocks. VTD GEOIDs are keys, blocks are values
	    csv_directory: Directory containing plans as block assignment files
	"""
	json_f = open(state_blocks_to_vtds)
	vtds_to_blocks = json.load(json_f)

	files = glob.glob(csv_directory + "/*.csv")
	state_vtd = gpd.read_file(vtd_shp)
	state_block = gpd.read_file(block_shp, dtype={"GEOID20": "str"})
	
	pop_key = [key for key in state_block.columns if "TOTPOP" in key][0]

	for file in files:
		plan = pd.read_csv(file, dtype={"GEOID20": "str", "assignment":int})

		plan = plan.merge(state_block, on="GEOID20")
		vtds = []
		vtd_assignment = [] 
	 
		for vtd in tqdm.tqdm(vtds_to_blocks.keys()):
			blocks = [str(x) for x in vtds_to_blocks[vtd]]
			vtd_assignment.extend(plan["assignment"][plan["GEOID20"].isin(blocks)].values)
			vtds.extend(len(plan["assignment"][plan["GEOID20"].isin(blocks)].values)*[vtd])
		vtd_df = pd.DataFrame(columns =  ["GEOID20", "assignment"])
		vtd_df["GEOID20"] = vtds
		vtd_df["assignment"] = vtd_assignment
	 
		vtd_df = vtd_df.drop_duplicates()
	 
		geoids = vtd_df["GEOID20"]
		vtd_dups = vtd_df[geoids.isin(geoids[geoids.duplicated()])]
		vtd_splits = len(vtd_dups["GEOID20"].unique())
		tot_reassigned_pop = 0 
		tot_impacted_pop = 0
		
		split_cousubs = vtd_dups.GEOID20.unique()
		p = pd.DataFrame(split_cousubs, columns=["GEOID20"])
		p.to_csv("pa_split_cousubs.csv", index=False)
		for vtd in tqdm.tqdm(vtd_dups.GEOID20.unique()):
			assignments = vtd_dups["assignment"][vtd_dups["GEOID20"] == vtd].values
			max_pop = 0
			max_district = 0
			pop_list = []
	  
			for district in assignments:
				pop = sum(plan[pop_key][(plan["assignment"] == district) & (plan["GEOID20"].isin(vtds_to_blocks[vtd]))])
				pop_list.append(pop)
	   
				if pop >= max_pop:
					max_pop = pop
					max_district = district
			tot_reassigned_pop = tot_reassigned_pop + sum(pop_list) - max_pop
			tot_impacted_pop = tot_impacted_pop + sum(pop_list)
			vtd_df = vtd_df[vtd_df.GEOID20 != vtd]
			vtd_df = vtd_df.append({"GEOID20": vtd, "assignment": max_district}, ignore_index = True)
		
		vtd_df = vtd_df[["GEOID20", "assignment"]]
		fname = file.split(".csv")[0] + "_vtd.csv"
		vtd_df.to_csv(fname, index=False)

