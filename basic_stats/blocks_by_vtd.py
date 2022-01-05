import pandas as pd

def blocks_by_vtd(baf, state_fips, state) -> dict:
    """
    Uses the census BAF block to vtd mapping to create a dictionary mapping of VTDs to blocks. 
    For each vtd, the file will have the list of blocks it contains. The file used for each state 
    can be downloaded here. https://www.census.gov/geographies/reference-files/time-series/geo/block-assignment-files.html.
    
    The specific file used is BlockAssign_ST{state_fips}_{state}_VTD.txt.
   
    Args:
   	 baf: Block assignment file from census.
    	 state_fips: The FIPS code for the state. i.e. 25.
    	 state: Abbreviation for US state. i.e. `ma`.

    Returns:
        Dictionary with VTDs as keys, and blocks contained within each VTD as values. 

    """

    block_to_VTD = pd.read_csv(baf, sep="|", dtype = {"BLOCKID": "str", "DISTRICT": "str", "COUNTYFP": "str"})
    block_to_VTD["VTD"] = str(state_fips) + block_to_VTD.COUNTYFP.str.cat(block_to_VTD.DISTRICT)

    blocks_by_VTD = {vtd: set() for vtd in block_to_VTD["VTD"]}
    for vtd in tqdm.tqdm(blocks_by_VTD.keys()):
        blocks_by_VTD[vtd] = list(set(block_to_VTD[block_to_VTD.VTD == vtd].BLOCKID.unique().astype('str')))

    return blocks_by_VTD



