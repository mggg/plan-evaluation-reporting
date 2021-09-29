import statistics
import networkx as nx
import numpy as np
from gerrychain import Partition, updaters, metrics
from gerrychain.updaters import Tally

class PlanMetrics:
    def __init__(self, graph, elections, pop_col, county_col="COUNTY") -> None:
        self.graph = graph
        self.county_column = county_col
        self.elections = elections
        self.pop_col = pop_col
        self.county_part = Partition(self.graph, self.county_column, 
                                     updaters={"population": Tally(pop_col, alias="population")})

    def eguia_metric(self, part, e, party):
        seat_share = part[e].seats(party) / len(part.parts)
        counties = self.county_part.parts
        county_results = np.array([self.county_part[e].won(party, c) for c in counties])
        county_pops = np.array([self.county_part["population"][c] for c in counties])
        ideal = np.dot(county_results, county_pops) / county_pops.sum()
        return ideal - seat_share

    def partisan_metrics(self, part):
        """
        Return information about partisanship metric:
        Scores by elections:
            * seats
            * efficiency gap,
            * mean median
            * partisan bias
            * Eugia's metric (by county)

        Scores by plan:
            * # Swing districts
            * # Competitive districts
        """
        party = part[self.elections[0]].election.parties[0]

        ## Plan wide scores
        election_results = np.array([np.array(part[e].percents(party)) for e in self.elections])
        num_competitive_districts = np.logical_and(election_results > 0.47, election_results < 0.53).sum()
        election_stability = (election_results > 0.5).sum(axis=0)
        num_swing_districts = np.logical_and(election_stability != 0, 
                                             election_stability != len(self.elections)).sum()
        num_party_districts = (election_stability == len(self.elections)).sum()
        num_op_party_districts = (election_stability == 0).sum()

        response = {"election_scores": {part[e].election.name: {
                                                    "seats": part[e].seats(party),
                                                    "efficiency_gap": part[e].efficiency_gap(),
                                                    "mean_median": part[e].mean_median(),
                                                    "partisan_bias": part[e].partisan_bias(),
                                                    "eguia_county": self.eguia_metric(part, e, party)
                                                } for e in self.elections},
                    "plan_scores": {
                                        "num_swing_districts": int(num_swing_districts),
                                        "num_competitive_districts": int(num_competitive_districts),
                                        "num_party_districts": int(num_party_districts),
                                        "num_op_party_districts": int(num_op_party_districts)
                                },
                    "party": party}
        return response