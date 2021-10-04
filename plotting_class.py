from plotting_configuration import *
import matplotlib.pyplot as plt
import numpy as np
import json
import re

class PlotFactory:
    def __init__(self, state, plan_type, eps, steps, method):
        DEMO_COLS = ['TOTPOP', 'WHITE', 'BLACK', 'AMIN', 'ASIAN', 'NHPI', 'OTHER', '2MORE', 'HISP',
                 'VAP', 'WVAP', 'BVAP', 'AMINVAP', 'ASIANVAP', 'NHPIVAP', 'OTHERVAP', '2MOREVAP', 'HVAP']

        with open(f"{state}/ensemble_stats/{state.lower()}_{plan_type}_{eps}_bal_{steps}_steps_{method}.jsonl", "r") as fin:
            json_list = list(fin)
        summary = json.loads(json_list[0])
        
        def sort_elections(elec_list):
            tuplified_elecs = list(map(lambda x: re.findall(r"[^\W\d_]+|\d+",x), elec_list))
            sorted_tuples = sorted(tuplified_elecs, key=lambda x: x[1])
            return [tup[0] + tup[1] for tup in sorted_tuples]

        self.party = summary["pov_party"]
        self.elections = summary["elections"]
        self.election_names = sort_elections([election["name"] for election in summary["elections"]])
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
        """
        Cycle through the plans and aggregate together the specified score.
        If the score is by plan, this will return a simple list as long as the chain. If the score is
        by district or by election, we'll return a dictionary with keys as districts or elections, values
        being the list of scores as long as the chain.
        """
        if score not in self.scores.keys():
            raise ValueError(f"Score '{score}' is not in self.scores!")
            
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
    
    def get_bins_and_labels(self, 
                            val_range, 
                            unique_vals,
                            num_labels=8,
                           ):
        if type(val_range[1]) is not int and len(unique_vals) <= num_labels:
            _, hist_bins = np.histogram(list(unique_vals), bins=len(unique_vals))
            bin_width = hist_bins[1] - hist_bins[0]
        else:
            bin_width = 10 ** (np.floor(np.log10(val_range[1] - val_range[0])) - 1)
            if bin_width == 0.1:
                bin_width = 1
            if bin_width >= 1:
                bin_width = int(bin_width)
            hist_bins = np.arange(val_range[0], val_range[1] + bin_width, bin_width)
        label_interval = max(int(len(hist_bins) / num_labels), 1)
        tick_bins = []
        tick_labels = []
        for i, x in enumerate(hist_bins[:-1]):
            if i % label_interval == 0:
                tick_labels.append(x)
                tick_bins.append(x + bin_width / 2)
        for i, label in enumerate(tick_labels):
            if type(label) == np.float64:
                tick_labels[i] = round(label, 2)
        return hist_bins, tick_bins, tick_labels
    
    def plot_histogram(self, 
                       scores, 
                       score_range,
                       unique_scores,
                       figsize=FIG_SIZE, 
                      ):
        fig, ax = plt.subplots(figsize=figsize)
        hist_bins, tick_bins, tick_labels = self.get_bins_and_labels(score_range, unique_scores)
        ax.set_xticks(tick_bins)
        ax.set_xticklabels(tick_labels, fontsize=TICK_SIZE)
        ax.hist(scores,
                bins=hist_bins,
                color=DEFAULT_COLOR,
               )
        ax.get_yaxis().set_visible(False)
        return ax
    
    def plot_plan_score(self, 
                        score, 
                        labels=True, 
                        figsize=FIG_SIZE,
                       ):
        scores = self.aggregate_score(score)
        ax = self.plot_histogram(scores,
                                 (min(scores), max(scores)),
                                 set(scores),
                                 figsize=figsize)
        if labels:
            ax.set_xlabel(score, fontsize=LABEL_SIZE)
        return
    
    def plot_election_score(self, 
                            score, 
                            election=None,
                            labels=True, 
                            figsize=FIG_SIZE,
                           ):
        if election:
            scores = self.aggregate_score(score)[election]
            ax = self.plot_histogram(scores,
                                     (min(scores), max(scores)),
                                     set(scores),
                                     figsize=figsize,
                                     )
            if labels:
                ax.set_xlabel(f"{election} {self.party} {score}", fontsize=LABEL_SIZE)
        else:
            scores_by_election = self.aggregate_score(score)
            all_scores = [score for score_list in scores_by_election.values() for score in score_list]
            for election, scores in scores_by_election.items():
                ax = self.plot_histogram(scores, 
                                         (min(all_scores), max(all_scores)),
                                         set(all_scores),
                                         figsize=figsize, 
                                        )
                if labels:
                    ax.set_xlabel(f"{election} {self.party} {score}", fontsize=LABEL_SIZE)
        return
    
    def plot_demographics(self,
                          score,
                          labels=True,
                          figsize=FIG_SIZE,
                         ):
        POP_COL = self.pop_col if "VAP" not in score else "VAP"
        demographics_by_district = self.aggregate_score(score)
        totpop_by_district = self.aggregate_score(POP_COL)
        sorted_districts = {d: [] for d in range(1, self.num_districts + 1)}
        for i in range(self.len):
            scores = sorted([demographics_by_district[d][i] / totpop_by_district[d][i] for d in demographics_by_district.keys()])
            for j, value in enumerate(scores):
                sorted_districts[j+1].append(value)
        
        fig, ax = plt.subplots(figsize=figsize)
        boxstyle = {
           "lw": 2, 
        }
        ax.boxplot(sorted_districts.values(),
                   whis=(1,99),
                   showfliers=False,
                   boxprops=boxstyle,
                   whiskerprops=boxstyle,
                   capprops=boxstyle,
                   medianprops={
                       **boxstyle,
                       "color":DEFAULT_COLOR,
                   },
                  )
        ax.set_ylim(0,1)
        if labels:
            ax.set_xlabel(f"Districts sorted by {score} share", fontsize=LABEL_SIZE)
        return
    
    def plot_sea_level(self,
                      labels=True,
                       figsize=FIG_SIZE,
                      ):
        seats = self.aggregate_score("seats")
        
        fig, ax = plt.subplots(figsize=figsize)
        boxstyle = {
           "lw": 2, 
        }
        ax.boxplot([seats[e] for e in self.election_names],
                   whis=(1,99),
                   showfliers=False,
                   boxprops=boxstyle,
                   whiskerprops=boxstyle,
                   capprops=boxstyle,
                   medianprops={
                       **boxstyle,
                       "color":DEFAULT_COLOR,
                   },
                  )
        ax.set_ylim(0,self.num_districts)
        ax.set_xticklabels(self.election_names, fontsize=TICK_SIZE)
        if labels:
            ax.set_ylabel("Democratic seats", fontsize=LABEL_SIZE)
        return
        
        