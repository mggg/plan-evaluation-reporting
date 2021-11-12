## Constants
"""
In this context the supported states will just be for NC. NC is listed as a supported state for congress, the others are all county clusters.
County clusters are named with S or H for senate or house, the first number describes which assignment scheme this cluster is using, the second 
number is the assignment it was given, and the final number is the number of districts that should be created from this cluster.

The assignment schemes for senate are 0-15 and for house are 0-7.
"""

SUPPORTED_STATES = ["NorthCarolina", 'S_14_0_2', 'S_14_13_2', 'S_14_15_2', 'S_14_6_2', 'S_14_9_2', 'S_15_0_2', 'S_15_13_4', 'S_15_15_2', 'S_15_16_2', 'S_15_17_2', 'S_15_1_3', 'S_15_21_6', 'S_15_22_3', 'S_15_23_6', 'S_15_5_3', 'S_15_9_2', 'H_0_18_6', 'H_0_25_13', 'H_0_26_2', 'H_0_34_3', 'H_0_36_2', 'H_0_39_2', 'H_0_3_4', 'H_0_7_13', 'H_5_17_2', 'H_5_34_3', 'H_5_8_2', 'H_6_11_2', 'H_6_21_2', 'H_7_0_2', 'H_7_10_4', 'H_7_11_5', 'H_7_13_2', 'H_7_14_7', 'H_7_15_3', 'H_7_16_5', 'H_7_19_2', 'H_7_20_2', 'H_7_22_2', 'H_7_23_2', 'H_7_24_5', 'H_7_30_4', 'H_7_31_2', 'H_7_32_2', 'H_7_35_2', 'H_7_37_4', 'H_7_3_4', 'H_7_9_3']
SUPPORTED_PLAN_TYPES = ["congress", "state_senate", "state_house"]

DUAL_GRAPH_DIR = "dual_graphs"
STATE_SPECS_DIR = "state_specifications"
CHAIN_DIR = "raw_chains"
STATS_DIR = "ensemble_stats"

SUPPORTED_METRICS = {
    "col_tally": "district_level",
    "num_cut_edges": "plan_wide",
    "num_county_pieces": "plan_wide",
    "num_split_counties": "plan_wide",
    "seats": "election_level",
    "efficiency_gap": "election_level",
    "mean_median": "election_level",
    "partisan_bias": "election_level",
    "eguia_county": "election_level",
    "num_swing_districts": "plan_wide",
    "num_competitive_districts": "plan_wide",
    "num_party_districts": "plan_wide",
    "num_op_party_districts": "plan_wide",
    "num_party_wins_by_district": "plan_wide", 
    "num_traversals": "plan_wide"

}

SUPPORTED_MAP_TYPES = ["ensemble_plan", "citizen_plan", "proposed_plan"]
