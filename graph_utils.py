from gerrychain.updaters import Tally
from gerrychain import Election, Partition
from score_functions import *
from info import info
import pandas as pd

def node_unit_mappings(state, graph):
    """
    Returns the graph node (int) <-> Districtr unit column (str) mappings, helpful
    for transitioning from a GerryChain Partition to a Districtr CSV
    """
    UNIT_COL = info[state]["UNIT_COL"]
    node_to_unit = {n: str(graph.nodes[n][UNIT_COL]) for n in graph.nodes}
    unit_to_node = {node_to_unit[n]: n for n in graph.nodes}
    return node_to_unit, unit_to_node

def get_assignment(state, graph, dists, file):
    """
    Returns the node -> district assignment dictionary that corresponds to the partition of the graph specified
    by the Districtr csv at `file`.
    """
    _, unit_to_node = node_unit_mappings(state, graph)
    UNIT_COL = info[state]["UNIT_COL"]
    assignment_path = f"assignments/{state}/{dists}"
    df = pd.read_csv(f"{assignment_path}/{file}.csv", converters={0: lambda x: str(x)}).astype(str)
    df.columns = [UNIT_COL, "assignment"]
    unit_assignment = dict(zip(df[UNIT_COL], df["assignment"]))
    node_assignment = {unit_to_node[unit]:unit_assignment[unit] for unit in unit_assignment.keys()}
    return node_assignment

def add_updaters(state, graph):
    """
    Creates the updaters we'll want to call for each partition in the chain.
    """
    
    elections = info[state]["elections"]
    POP_COL = info[state]["POP_COL"]
    COUNTY_COL = info[state]["COUNTY_COL"]
    counties, nodes_by_county = get_regions(graph, COUNTY_COL)

    updaters = {"population": Tally(POP_COL, alias="population")}
    election_list = []
    for election, election_info in elections.items():
        election_cols = election_info["columns"]
        updaters[election] = Election(election, {election_cols[col]["party"]:col for col in election_cols.keys()})
        election_list.append(election)
    updaters["elections"] = lambda part: election_list # store a list of the elections for swinginess updater to use
    updaters["county_splits"] = lambda part: num_region_splits(part, counties, nodes_by_county)
    updaters["swing_districts"] = lambda part: swing_districts(part)
    return updaters

def make_partition(state, graph, dists, file):
    """
    Create the partition of the graph specified by the Districtr file at `file`.
    """
    node_assignment = get_assignment(state, graph, dists, file)
    updaters = add_updaters(state, graph)
    return Partition(graph, node_assignment, updaters)