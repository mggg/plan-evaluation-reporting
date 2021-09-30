import numpy as np

def get_regions(graph, region_col):
    """
    Helper function for `num_region_splits()`
    """
    regions = set([graph.nodes[n][region_col] for n in graph.nodes])
    nodes_by_region = {
            region:[n for n in graph.nodes if graph.nodes[n][region_col] == region] \
            for region in regions
    }
    return regions, nodes_by_region

def num_region_splits(partition, regions, nodes_by_region):
    """
    How many times a region (county) is touched by multiple districts.
    """
    splits = 0
    assignment = dict(partition.assignment)
    for region in regions:
        districts = set()
        for node in nodes_by_region[region]:
            districts.add(assignment[node])
            if len(districts) > 1:
                splits += 1
                break
    return splits

def swing_districts(partition):
    """
    A swing district is one that has been won by more than one party over all the elections on the partition.
    """
    num_swings = 0
    for district in range(len(partition)):
        party_list = [round(partition[elec].percents("Rep")[district]) for elec in partition.elections] # 0 for Dem, 1 for Rep
        if sum(party_list) in range(1, len(partition.elections)):
            num_swings += 1
    return num_swings

def L1(vec):
    """
    L1 distance from the 0-vector.
    """
    return sum(abs(v) for v in vec)

def agg_prop(partition, elections=None):
    if elections is None:
        elections = partition.elections
    num_R_seats = 0
    for election in elections:
        num_R_seats += partition[election].wins("Rep")
    prop_R_seats = np.sum([partition[election].percent("Rep") * len(partition) for election in elections])
    return round(num_R_seats - prop_R_seats)

def P1(partition, elections=None):
    """
    P1 proportionality score: The distance between the average GOP seat share and the GOP vote share
    across N general elections:
    """
    if elections is None:
        elections = partition.elections
    num_dists = len(partition)
    num_R_seats = 0
    for election in elections:
        num_R_seats += partition[election].wins('Rep')
    average_R_vote_share = np.mean([partition[election].percent('Rep') for election in elections])
    average_R_seat_share = num_R_seats / (num_dists * len(elections))
    return abs(average_R_seat_share - average_R_vote_share)

def P2(partition, elections=None):
    """
    P2 proportionality score: The L1 distance between the GOP seat share and the GOP vote share
    summed over each of N general elections.
    """
    if elections is None:
        elections = partition.elections
    num_dists = len(partition)
    proportionality_vector = []
    for election in elections:
        vote_share = partition[election].percent("Rep")
        seat_share = partition[election].wins("Rep") / num_dists
        proportionality_vector.append(seat_share - vote_share)
    return L1(proportionality_vector)