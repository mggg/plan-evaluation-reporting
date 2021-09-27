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
