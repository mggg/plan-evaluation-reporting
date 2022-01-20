import click
import warnings
import pandas as pd
from gerrychain import Graph


@click.command()
@click.option('--block-graph-in-file',
              required=True,
              help='Input block-level dual graph (weight source).')
@click.option('--vtd-graph-in-file',
              required=True,
              help='Input VTD-level dual graph (weight target).')
@click.option(
    '--baf-file',
    required=True,
    help='Correspondence between blocks and VTDs (Census BAF format).')
@click.option('--state-fips-code', help='State FIPS code.', required=True)
@click.option('--in-place',
              is_flag=True,
              help='Update dual graphs with edge weights in place.')
@click.option('--block-graph-out-file', help='Output block-level dual graph.')
@click.option('--vtd-graph-out-file', help='Output VTD-level dual graph.')
@click.option('--block-geoid-col', default='GEOID20')
@click.option('--vtd-geoid-col', default='GEOID20')
@click.option('--baf-block-col', default='BLOCKID')
@click.option('--baf-county-col', default='COUNTYFP')
@click.option('--baf-vtd-col', default='DISTRICT')
def augment(block_graph_in_file, vtd_graph_in_file, baf_file, state_fips_code,
            in_place, block_graph_out_file, vtd_graph_out_file,
            block_geoid_col, vtd_geoid_col, baf_block_col, baf_county_col,
            baf_vtd_col):
    block_graph = Graph.from_json(block_graph_in_file)
    vtd_graph = Graph.from_json(vtd_graph_in_file)
    baf_df = pd.read_csv(block_to_vtd_baf_path, sep='|',
                         dtype=str).set_index(baf_block_col)

    # Generate VTD IDs from BAF columns.
    baf_df['vtd_id'] = (state_fips_code +
                        vtd_block_df[baf_county_col].str.zfill(3) +
                        vtd_block_df[baf_vtd_col].str.zfill(6))
    blocks_by_vtd = defaultdict(set)
    for block, vtd in baf_dff['vtd_id'].items():
        blocks_by_vtd[vtd].add(block)
    block_graph_edges_by_geoid = {(block_graph.nodes[a][block_geoid_col],
                                   block_graph.nodes[b][block_geoid_col])
                                  for a, b in block_graph.edges}

    # Update edge weights.
    vtd_edge_weights = defaultdict(int)
    for a, b in vtd_graph.edges:
        for a_block in blocks_by_vtd[vtd_graph.nodes[a][vtd_geoid_col]]:
            for b_block in blocks_by_vtd[vtd_graph.nodes[b][vtd_geoid_col]]:
                if (a_block, b_block) in block_graph_edges_by_geoid or (
                        b_block, a_block) in block_graph_edges_by_geoid:
                    vtd_edge_weights[(a, b)] += 1

    for edge in block_graph.edges:
        block_graph.edges[edge]['weight'] = 1

    for edge, weight in vtd_edge_weights.items():
        vtd_graph.edges[edge]['weight'] = weight

    # Save graphs.
    if in_place:
        block_graph.to_json(block_graph_in_file)
        vtd_graph.to_json(vtd_graph_in_file)
    else:
        if block_graph_out_file:
            block_graph.to_json(block_graph_out_file)
        else:
            warnings.warn('Not saving output block dual graph (no path specified).')

        if vtd_graph_out_file:
            vtd_graph.to_json(vtd_graph_out_file)
        else:
            warnings.warn('Not saving output VTD dual graph (no path specified).')


if __name__ == '__main__':
    augment()
