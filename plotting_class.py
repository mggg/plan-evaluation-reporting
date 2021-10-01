import json

class PlotFactory:
    def __init__(self, state, plan_type, eps, steps, method):
        DEMO_COLS = ['TOTPOP', 'WHITE', 'BLACK', 'AMIN', 'ASIAN', 'NHPI', 'OTHER', '2MORE', 'HISP',
                 'VAP', 'WVAP', 'BVAP', 'AMINVAP', 'ASIANVAP', 'NHPIVAP', 'OTHERVAP', '2MOREVAP', 'HVAP']

        with open(f"{state}/ensemble_stats/{state.lower()}_{plan_type}_{eps}_bal_{steps}_steps_{method}.jsonl", "r") as fin:
            json_list = list(fin)
        summary = json.loads(json_list[0])

        self.party = summary["pov_party"]
        self.elections = summary["elections"]
        self.num_districts = summary["num_districts"]
        self.epsilon = summary["epsilon"]
        self.chain_type = summary["chain_type"]
        self.pop_col = summary["pop_col"]
        self.plans = [json.loads(j) for j in json_list if json.loads(j)["type"] == "ensemble_plan"]
        self.len = len(self.plans)

        demographics = {
            demo_col:{
                "path": ["demographics"],
                "score_type": "by_district",
            } for demo_col in DEMO_COLS
        }
        partisanship_by_plans = {
            plan_score: {
                "path": ["partisanship", "plan_scores"],
                "score_type": "by_plan",
            } for plan_score in self.plans[0]["partisanship"]["plan_scores"].keys()
        }
        partisanship_by_elections = {
            election_score: {
                "path": ["partisanship", "election_scores"],
                "score_type": "by_election"
            } for election_score in self.plans[0]["partisanship"]["election_scores"][self.elections[0]["name"]]
        }
        compactness = {
            score: {
                "path": ["compactness"],
                "score_type": "by_plan"
            } for score in self.plans[0]["compactness"].keys()
        }
        self.scores = {**demographics, **partisanship_by_plans, **partisanship_by_elections, **compactness}

    def aggregate_score(self, score):
        if score not in self.scores.keys():
            raise ValueError(f"Score {score} is not in self.scores!")
            return

        if self.scores[score]["score_type"] == "by_plan":
            aggregation = []
            for plan in self.plans:
                for path_segment in self.scores[score]["path"]:
                    plan = plan[path_segment]
                aggregation.append(plan[score])
        elif self.scores[score]["score_type"] == "by_election":
            aggregation = {e["name"]: [] for e in self.elections}
            for plan in self.plans:
                for path_segment in self.scores[score]["path"]:
                    plan = plan[path_segment]
                for e in aggregation.keys():
                    aggregation[e].append(plan[e][score])
        elif self.scores[score]["score_type"] == "by_district":
            # TODO: can we change the json summary to also include a list of districts (str)
            aggregation = {district: [] for district in self.plans[0]["demographics"][self.pop_col].keys()}
            for plan in self.plans:
                for path_segment in self.scores[score]["path"]:
                    plan = plan[path_segment]
                for district in aggregation.keys():
                    aggregation[district].append(plan[score][district])
        return aggregation