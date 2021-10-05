from plotting_configuration import *
import matplotlib.pyplot as plt
import numpy as np
import random
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
        self.default_color = "#4693b3" if summary["chain_type"] == "neutral" else "#5c676f"
        self.proposal_colors = ["#f3c042", "#96b237", "#bc2f45", "#f2bbc4", "#c26d2b"]

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
            hist_bins = np.arange(val_range[0], val_range[1] + 2 * bin_width, bin_width)
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
        return hist_bins, tick_bins, tick_labels, bin_width
    
    def plot_histogram(self, 
                       scores, 
                       score_range,
                       unique_scores,
                       figsize=FIG_SIZE, 
                      ):
        fig, ax = plt.subplots(figsize=figsize)
        hist_bins, tick_bins, tick_labels, bin_width = self.get_bins_and_labels(score_range, unique_scores)
        ax.set_xticks(tick_bins)
        ax.set_xticklabels(tick_labels, fontsize=TICK_SIZE)
        ax.hist(scores,
                bins=hist_bins,
                color=self.default_color,
                rwidth=0.8,
                edgecolor='black',
               )
        ax.get_yaxis().set_visible(False)
        return ax, bin_width
    
    def plot_violin(self,
                    scores,
                    labels,
                    figsize=FIG_SIZE,
                   ):
        fig, ax = plt.subplots(figsize=figsize)
        parts = ax.violinplot(scores,
                              showextrema=False,
#                               quantiles=[[0.01, 0.25, 0.5, 0.75, 0.99] for score_list in scores],
                             )
        for pc in parts['bodies']:
            pc.set_facecolor(self.default_color)
            pc.set_edgecolor("black")
            pc.set_alpha(1)
        ax.set_xticks(range(len(labels) + 1))
        ax.set_xticklabels([""] + list(labels), fontsize=TICK_SIZE)
        return ax
    
    def plot_boxplot(self,
                     scores,
                     labels,
                     figsize=FIG_SIZE,
                    ):
        fig, ax = plt.subplots(figsize=figsize)
        boxstyle = {
           "lw": 2,
            "color": self.default_color,
        }
        ax.boxplot(scores,
                   whis=(1,99),
                   showfliers=False,
                   boxprops=boxstyle,
                   whiskerprops=boxstyle,
                   capprops=boxstyle,
                   medianprops=boxstyle,
                  )
        return ax
    
    def plot_plan_score(self, 
                        score, 
                        hypotheticals=False,
                        labels=True, 
                        figsize=FIG_SIZE,
                        save=False,
                       ):
        scores = self.aggregate_score(score)
        if score == "num_split_counties" or score == "num_county_pieces":
            scores = scores[1000:]
        ax, bin_width = self.plot_histogram(scores,
                                            (min(scores), max(scores)),
                                            set(scores),
                                            figsize=figsize)
        if labels:
            ax.set_xlabel(score, fontsize=LABEL_SIZE)
        if hypotheticals:
            for i in range(hypotheticals):
                rand_idx = random.randrange(0,len(scores))
                hypothetical_score = scores[rand_idx]
                ax.axvline(hypothetical_score + bin_width / 2,
                           lw=5,
                           alpha=0.8,
                           color=self.proposal_colors[i],
                           label=f"Plan {rand_idx}: {round(hypothetical_score, 2)}",
                          )
            ax.legend()
        if save:
            plt.savefig(f"gallery/{score}_{self.chain_type}.png", dpi=300, bbox_inches='tight')
            plt.close()
        return
    
    def plot_election_score(self, 
                            score, 
                            election=None,
                            hypotheticals=False,
                            labels=True, 
                            figsize=FIG_SIZE,
                            save=False,
                           ):
        if election:
            scores = self.aggregate_score(score)[election]
            ax, bin_width = self.plot_histogram(scores,
                                                (min(scores), max(scores)),
                                                set(scores),
                                                figsize=figsize,
                                                )
            if labels:
                ax.set_xlabel(f"{election} {self.party} {score}", fontsize=LABEL_SIZE)
            if hypotheticals:
                for i in range(hypotheticals):
                    rand_idx = random.randrange(0,self.len)
                    hypothetical_score = scores[rand_idx]
                    ax.axvline(hypothetical_score + bin_width / 2,
                               lw=5,
                               alpha=0.8,
                               color=self.proposal_colors[i],
                               label=f"Plan {rand_idx}: {round(hypothetical_score, 2)}",
                              )
                ax.legend()
        else:
            scores_by_election = self.aggregate_score(score)
            ax = self.plot_violin([scores_by_election[e] for e in self.election_names], 
                                  self.election_names,
                                  figsize=FIG_SIZE)
            if labels:
                ax.set_xlabel(f"{self.party} {score}", fontsize=LABEL_SIZE)
            if hypotheticals:
                for i in range(hypotheticals):
                    rand_idx = random.randrange(0, self.len)
                    hypothetical_scores = [scores_by_election[e][rand_idx] for e in self.election_names]
                    for j, election in enumerate(self.election_names):
                        ax.scatter(j+1, hypothetical_scores[j],
                                   color=self.proposal_colors[i],
                                   edgecolor='black',
                                   s=100,
                                   alpha=0.8,
                                  )
                        if j == 0:
                            ax.scatter(j+1, hypothetical_scores[j],
                                       color=self.proposal_colors[i],
                                       edgecolor='black',
                                       s=100,
                                       alpha=0.8,
                                       label=f"Plan {rand_idx}",
                                      )
                ax.legend()
        if save:
            is_election = f"_{election}" if election else "_"
            plt.savefig(f"gallery/{score}{is_election}_{self.chain_type}.png", dpi=300, bbox_inches='tight')
            plt.close()
        return
    
    def plot_demographics(self,
                          score,
                          boxplot=False,
                          raw=False,
                          hypotheticals=False,
                          labels=True,
                          figsize=FIG_SIZE,
                          save=False,
                         ):
        POP_COL = self.pop_col if "VAP" not in score else "VAP"
        demographics_by_district = self.aggregate_score(score)
        totpop_by_district = self.aggregate_score(POP_COL)
        sorted_districts = {d: [] for d in range(1, self.num_districts + 1)}
        for i in range(self.len):
            if raw:
                scores = sorted([demographics_by_district[d][i] for d in demographics_by_district.keys()])
            else:
                scores = sorted([demographics_by_district[d][i] / totpop_by_district[d][i] for d in demographics_by_district.keys()])
            for j, value in enumerate(scores):
                sorted_districts[j+1].append(value)
        if boxplot:
            ax = self.plot_boxplot(sorted_districts.values(),
                                   sorted_districts.keys(),
                                   figsize=FIG_SIZE,
                                  )
        else:
            ax = self.plot_violin(sorted_districts.values(),
                                  sorted_districts.keys(),
                                  figsize=FIG_SIZE,
                                 )
        
        if not raw and max(sorted_districts[max(sorted_districts.keys())]) > 0.4:
            ax.set_ylim(0,1)
            ax.axhline(0.5,
                       color=self.default_color,
                       alpha=1,
                       label=f"50% {score}")
            ax.legend()
        if hypotheticals:
            for i in range(hypotheticals):
                rand_idx = random.randrange(0, self.len)
                hypothetical_scores = [sorted_districts[int(d)][rand_idx] for d in demographics_by_district.keys()]
                for j, district in enumerate(demographics_by_district.keys()):
                    ax.scatter(j+1, hypothetical_scores[j],
                               color=self.proposal_colors[i],
                               edgecolor='black',
                               s=100,
                               alpha=0.8,
                              )
                    if j == 0:
                        ax.scatter(j+1, hypothetical_scores[j],
                                   color=self.proposal_colors[i],
                                   edgecolor='black',
                                   s=100,
                                   alpha=0.8,
                                   label=f"Plan {rand_idx}",
                                  )
            ax.legend()
        if labels:
            suffix = "" if raw else " share"
            ax.set_xlabel(f"Districts sorted by {score}{suffix}", fontsize=LABEL_SIZE)
        if save:
            shape = 'boxplot' if boxplot else 'violin'
            raw_title = 'counts' if raw else 'percents'
            plt.savefig(f"gallery/{score}_{shape}_{raw_title}_{self.chain_type}.png", dpi=300, bbox_inches='tight')
            plt.close()
        return
    
#     def plot_sea_level(self,
#                       labels=True,
#                        figsize=FIG_SIZE,
#                       ):
#         seats = self.aggregate_score("seats")
        
#         fig, ax = plt.subplots(figsize=figsize)
#         boxstyle = {
#            "lw": 2, 
#         }
#         ax.boxplot([seats[e] for e in self.election_names],
#                    whis=(1,99),
#                    showfliers=False,
#                    boxprops=boxstyle,
#                    whiskerprops=boxstyle,
#                    capprops=boxstyle,
#                    medianprops={
#                        **boxstyle,
#                        "color":self.default_color,
#                    },
#                   )
#         ax.set_ylim(0,self.num_districts)
#         ax.set_xticklabels(self.election_names, fontsize=TICK_SIZE)
#         if labels:
#             ax.set_ylabel("Democratic seats", fontsize=LABEL_SIZE)
#         return
        
        