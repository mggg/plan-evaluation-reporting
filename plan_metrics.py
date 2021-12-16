from functools import reduce
import numpy as np
import warnings
from gerrychain import Partition, updaters, metrics
from gerrychain.updaters import county_splits
from gerrychain.updaters import Tally
from configuration import SUPPORTED_MAP_TYPES

class PlanMetrics:
    DEMO_COLS = ['TOTPOP', 'WHITE', 'BLACK', 'AMIN', 'ASIAN', 'NHPI', 'OTHER', '2MORE', 'HISP',
                 'VAP', 'WVAP', 'BVAP', 'AMINVAP', 'ASIANVAP', 'NHPIVAP', 'OTHERVAP', '2MOREVAP', 'HVAP']

    def __init__(self, graph, elections, party, pop_col, state_metrics, county_col="COUNTY", 
                 demographic_cols=DEMO_COLS, updaters={}, municipality_col=None, incumbent_col=None) -> None:
        self.graph = graph
        self.elections = elections
        self.pop_col = pop_col
        self.county_col = county_col
        self.party = party
        self.county_part = Partition(self.graph, county_col, 
                                     updaters={"population": Tally(self.pop_col, alias="population"), **updaters})
        self.metrics = state_metrics
        self.metric_ids = set([m["id"] for m in state_metrics])
        self.compute_counties_details = "num_county_pieces" in self.metric_ids or "num_split_counties" in self.metric_ids
        self.compute_municipal_details = "num_municipal_pieces" in self.metric_ids or "num_split_municipalities" in self.metric_ids
        self.demographic_cols = demographic_cols
        self.counties = set(self.county_part.parts.keys())
        self.nodes_by_county = {county:[n for n in self.graph.nodes if self.graph.nodes[n][county_col] == county] for county in self.counties}
        if self.compute_municipal_details:
            self._municipal_precomputation(municipality_col)
        self.incumbent_col = incumbent_col
            
    
    def _municipal_precomputation(self, municipality_col):
        municipalities = set()
        for n in self.graph.nodes():
            muni = self.graph.nodes()[n][municipality_col]
            municipalities.update(muni) if type(muni) == list else municipalities.add(muni)
        self.municipalities = municipalities - set(['99999'])
        node_in_muni = lambda muni, node_data: muni in node_data if type(muni) == list else node_data == muni
        self.nodes_by_municipality = {municipality:[n for n in self.graph.nodes if node_in_muni(municipality, self.graph.nodes[n][municipality_col])] for municipality in self.municipalities}
    
    def summary_data(self, elections, num_districts=0, districts=[], epsilon=None, method=None, ensemble=True):
        header = {
                "type": "ensemble_summary" if ensemble else "summary",
                "pop_col": self.pop_col,
                "metrics": self.metrics,
                "pov_party": self.party,
                "elections": elections,
                "party_statewide_share": {self.county_part[e].election.name: self.county_part[e].percent(self.party) for e in self.elections}
                }
        if ensemble:
            header["epsilon"] = epsilon
            header["chain_type"] = method
            header["district_ids"] = list(districts)
            header["num_districts"] = len(districts)
        else:
            header["num_districts"] = num_districts

        
        return header

    def county_split_details(self,part, municipalities=False):
        """
        Which districts each county is touched by.
        """
        assignment = dict(part.assignment)
        
        if municipalities:
            return {municipality: reduce(lambda districts, node: districts | set([assignment[node]]), self.nodes_by_municipality[municipality], set()) for municipality in self.municipalities}
        else:
            return {county: reduce(lambda districts, node: districts | set([assignment[node]]), self.nodes_by_county[county], set()) for county in self.counties}

    def compactness_metrics(self, part):
        compactness_metrics = {}

        if "num_cut_edges" in self.metric_ids:
            compactness_metrics["num_cut_edges"] = len(part["cut_edges"]) 
        if self.compute_counties_details:
            county_details = self.county_split_details(part)
        if "num_county_pieces" in self.metric_ids:
            compactness_metrics["num_county_pieces"] = reduce(lambda acc, ds: acc + len(ds) if len(ds) > 1 else acc, county_details.values(), 0)
        if "num_split_counties" in self.metric_ids:
            compactness_metrics["num_split_counties"] = reduce(lambda acc, ds: acc + 1 if len(ds) > 1 else acc, county_details.values(), 0)
        if self.compute_municipal_details:
            county_details = self.county_split_details(part, municipalities=True)
        if "num_municipal_pieces" in self.metric_ids:
            compactness_metrics["num_municipal_pieces"] = reduce(lambda acc, ds: acc + len(ds) if len(ds) > 1 else acc, county_details.values(), 0)
        if "num_split_municipalities" in self.metric_ids:
            compactness_metrics["num_split_municipalities"] = reduce(lambda acc, ds: acc + 1 if len(ds) > 1 else acc, county_details.values(), 0)
        if "num_double_bunked" in self.metric_ids:
            compactness_metrics["num_double_bunked"] = reduce(lambda acc, n: acc + 1 if n > 1 else acc, part[self.incumbent_col].values(), 0)
        if "num_zero_bunked" in self.metric_ids:
            compactness_metrics["num_zero_bunked"] = reduce(lambda acc, n: acc + 1 if n == 0 else acc, part[self.incumbent_col].values(), 0)
        if "num_traversals" in self.metric_ids:
            compactness_metrics["num_traversals"] = self.num_traversals(part)
        return compactness_metrics

    def demographic_metrics(self, part):
        return {demo_col: part[demo_col] for demo_col in self.demographic_cols}

    def eguia_metric(self, part, e):
        seat_share = part[e].seats(self.party) / len(part.parts)
        counties = self.county_part.parts
        county_results = np.array([self.county_part[e].won(self.party, c) for c in counties])
        county_pops = np.array([self.county_part["population"][c] for c in counties])
        ideal = np.dot(county_results, county_pops) / county_pops.sum()
        return seat_share - ideal

    def partisan_metrics(self, part):
        election_metrics = {}

        ## Plan wide
        election_results = np.array([np.array(part[e].percents(self.party)) for e in self.elections])
        election_stability = (election_results > 0.5).sum(axis=0)
        if  "num_competitive_districts" in self.metric_ids:
            election_metrics["num_competitive_districts"] = int(np.logical_and(election_results > 0.47, 
                                                                               election_results < 0.53).sum())
        if "num_swing_districts" in self.metric_ids:
            election_metrics["num_swing_districts"] = int(np.logical_and(election_stability != 0, 
                                                      election_stability != len(self.elections)).sum())
        if "num_party_districts" in self.metric_ids:
            election_metrics["num_party_districts"] = int((election_stability == len(self.elections)).sum())
        if "num_op_party_districts" in self.metric_ids:
            election_metrics["num_op_party_districts"] = int((election_stability == 0).sum())
        if "num_party_wins_by_district" in self.metric_ids:
            election_metrics["num_party_wins_by_district"] = [int(d_wins) for d_wins in election_stability]
        # Election level
        if "seats" in self.metric_ids:
            election_metrics["seats"] = {part[e].election.name: part[e].seats(self.party) for e in self.elections}
        if "efficiency_gap" in self.metric_ids:
            election_metrics["efficiency_gap"] = {part[e].election.name: part[e].efficiency_gap() for e in self.elections}
        if "mean_median" in self.metric_ids:
            election_metrics["mean_median"] = {part[e].election.name: part[e].mean_median() for e in self.elections}
        if "partisan_bias" in self.metric_ids:
            election_metrics["partisan_bias"] = {part[e].election.name: part[e].partisan_bias() for e in self.elections}
        if "eguia_county" in self.metric_ids:
            election_metrics["eguia_county"] = {part[e].election.name: self.eguia_metric(part, e) for e in self.elections}

        return election_metrics
    
    def num_traversals(self, part):
        unique_county_pairs = {district: set() for district in part.assignment.values()}
        for (n1, n2) in part.graph.edges:
            if (n1, n2) not in part.cut_edges:
                district = part.assignment[n1]
                county1 = part.graph.nodes[n1][self.county_col]
                county2 = part.graph.nodes[n2][self.county_col]
                if county1 != county2: 
                    county_pair = tuple(sorted([county1, county2]))
                    unique_county_pairs[district].add(county_pair)
        num_traversals = sum([len(pair_set) for district, pair_set in unique_county_pairs.items()])
        return num_traversals

    def plan_summary(self, plan, plan_type="ensemble_plan", plan_name=""):
        """
        Returns Json object with the metrics for the passed plan.
        `plan_type` specifies what type of plan the passed plan is.  Should be one of
        `ensemble_plan`, `citizen_plan`, or `proposed_plan`.
        """
        if plan_type not in SUPPORTED_MAP_TYPES:
            warnings.warn("Plan type ({}) is not one of the supported plan types: {}".format(plan_type, str(SUPPORTED_MAP_TYPES)))

        plan_metrics = {
            "type": plan_type,
            **self.demographic_metrics(plan),
            **self.partisan_metrics(plan),
            **self.compactness_metrics(plan)
        }
        if plan_type == "proposed_plan":
            plan_metrics["name"] = plan_name
        if plan_type == "citizen_plan":
            plan_metrics["plan_id"] = plan_name
        return plan_metrics

