from networkx.algorithms import tree
from collections import deque
import random
from gerrychain.tree import (
    PopulatedGraph,
    predecessors,
    successors,
    Cut
)


def division_random_spanning_tree(graph, division_tuples=[("COUNTYFP10", 1)]):
    """
    Generates a spanning tree that discourages edges that cross divisions (counties, municipalities, etc).
    We probabilistically assign weights to every edge, and then draw a minumum spanning
    tree over the graph. This means that edges with lower weights will be preferred as the tree is drawn.

    Parameters:
    ----------
    graph: GerryChain Graph object
        The region upon which to draw the spanning tree (usually two districts merged together)
    division_tuples: list of (str, float)
        A list of tuples where the first element is the division column and the second element is
        the weight penalty added to any edge that spans two divisions of that type.
    """
    weights = {edge:0 for edge in graph.edges}
    for edge in graph.edges:
        for (division_col, penalty) in division_tuples:
            if graph.nodes[edge[0]][division_col] != graph.nodes[edge[1]][division_col]:
                weights[edge] += penalty
        graph.edges[edge]["weight"] = weights[edge] + random.random()

    spanning_tree = tree.minimum_spanning_tree(
        graph, algorithm="kruskal", weight="weight"
    )
    return spanning_tree

def division_find_balanced_edge_cuts_memoization(h, choice=random.choice, division_tuples=None):
    root = choice([x for x in h if h.degree(x) > 1])
    pred = predecessors(h.graph, root)
    succ = successors(h.graph, root)
    total_pop = h.tot_pop
    subtree_pops = {}
    stack = deque(n for n in succ[root])
    while stack:
        next_node = stack.pop()
        if next_node not in subtree_pops:
            if next_node in succ:
                children = succ[next_node]
                if all(c in subtree_pops for c in children):
                    subtree_pops[next_node] = sum(subtree_pops[c] for c in children)
                    subtree_pops[next_node] += h.population[next_node]
                else:
                    stack.append(next_node)
                    for c in children:
                        if c not in subtree_pops:
                            stack.append(c)
            else:
                subtree_pops[next_node] = h.population[next_node]
    cuts = []
    
    best_split_score = 0 
    for node, tree_pop in subtree_pops.items():
        def part_nodes(start):
            nodes = set()
            queue = deque([start])
            while queue:
                next_node = queue.pop()
                if next_node not in nodes:
                    nodes.add(next_node)
                    if next_node in succ:
                        for c in succ[next_node]:
                            if c not in nodes:
                                queue.append(c)
            return nodes

        is_balanced_A = abs(tree_pop - h.ideal_pop) <= h.ideal_pop * h.epsilon
        is_balanced_B = abs((total_pop - tree_pop) - h.ideal_pop) <= h.ideal_pop * h.epsilon

        parent = pred[node]
        if division_tuples is not None:
            division_cols = [tup[0] for tup in division_tuples]
            # score function to prefer higher ranked divisions:
            # [8, 4, 2, 1] — example with 4 divisions
            split_score = 0
            for i, division_col in enumerate(division_cols):
                if h.graph.nodes[parent][division_col] != h.graph.nodes[node][division_col]:
                    split_score += 2 ** (len(division_cols) - i - 1) # descending powers starting at len(division_cols) - 1
            if split_score > best_split_score and (is_balanced_A or is_balanced_B):
                best_split_score = split_score
                cuts = []
                part_subset = part_nodes(node) if is_balanced_A else set(h.graph.nodes) - part_nodes(node)
                cuts.append(Cut(edge=(node, pred[node]), subset=part_subset))
            elif split_score == best_split_score and (is_balanced_A or is_balanced_B):
                part_subset = part_nodes(node) if is_balanced_A else set(h.graph.nodes) - part_nodes(node)
                cuts.append(Cut(edge=(node, pred[node]), subset=part_subset))
        else:
            if is_balanced_A:
                cuts.append(Cut(edge=(node, pred[node]), subset=part_nodes(node)))
            elif is_balanced_B:
                cuts.append(Cut(edge=(node, pred[node]), subset=set(h.graph.nodes) - part_nodes(node)))

    return cuts

def division_bipartition_tree(
    graph,
    pop_col,
    pop_target,
    epsilon,
    division_tuples=[("COUNTYFP10", 1)],
    first_check_division=False,
    node_repeats=1,
    spanning_tree=None,
    choice=random.choice,
    attempts_before_giveup = 100):

    if first_check_division and len(division_tuples) == 0:
        raise ValueError("first_check_division is True but no divisions are provided in division_tuples.")

    populations = {node: graph.nodes[node][pop_col] for node in graph}

    possible_cuts = []
    if spanning_tree is None:
        spanning_tree = division_random_spanning_tree(graph, division_tuples=division_tuples)
    restarts = 0
    counter = 0
    while len(possible_cuts) == 0 and counter < attempts_before_giveup:
        # print(counter)
        if restarts == node_repeats:
            spanning_tree = division_random_spanning_tree(graph, division_tuples=division_tuples)
            restarts = 0
            counter +=1
        h = PopulatedGraph(spanning_tree, populations, pop_target, epsilon)
        if len(division_tuples) > 0 and first_check_division and restarts == 0:
            sorted_division_tuples = sorted(division_tuples, key=lambda x:x[1], reverse=True)
            possible_cuts = division_find_balanced_edge_cuts_memoization(h, choice=choice, division_tuples=sorted_division_tuples)
        if len(possible_cuts) == 0:
            h = PopulatedGraph(spanning_tree, populations, pop_target, epsilon)
            possible_cuts = division_find_balanced_edge_cuts_memoization(h, choice=choice)
        restarts += 1

    if counter >= attempts_before_giveup:
        return set()
    return choice(possible_cuts).subset

def get_regions(graph, region_col):
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