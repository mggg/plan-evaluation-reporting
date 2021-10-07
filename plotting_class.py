from plotting_configuration import *
import matplotlib.pyplot as plt
import numpy as np
import random
import json
import gzip
import re
import os

class PlotFactory:
    def __init__(self, state, plan_type, eps, steps, method):
        
        with gzip.open(f"{state}/ensemble_stats/{state.lower()}_{plan_type}_{eps}_bal_{steps}_steps_{method}.jsonl.gz", "rb") as fin:
            json_list = list(fin)
        summary = json.loads(json_list[0])
        
        def sort_elections(elec_list):
            tuplified_elecs = list(map(lambda x: re.findall(r"[^\W\d_]+|\d+",x), elec_list))
            sorted_tuples = sorted(tuplified_elecs, key=lambda x: x[1])
            return [tup[0] + tup[1] for tup in sorted_tuples]

        self.party = summary["pov_party"]
        self.parties = [candidate["name"] for candidate in summary["elections"][0]["candidates"]]
        self.op_party = [party for party in self.parties if party != self.party][0]
        self.elections = summary["elections"]
        self.election_names = sort_elections([election["name"] for election in summary["elections"]])
        self.num_districts = summary["num_districts"]
        self.districts = list(map(lambda x: str(x), summary["district_ids"])) # ints or strs?
        self.epsilon = summary["epsilon"]
        self.chain_type = summary["chain_type"]
        self.map_type = plan_type
        self.pop_col = summary["pop_col"]
        self.plans = [json.loads(j) for j in json_list if json.loads(j)["type"] == "ensemble_plan"]
        self.len = len(self.plans)
        self.default_color = "#4693b3" if summary["chain_type"] == "neutral" else "#5c676f"
        self.proposal_colors = ["#f3c042", "#96b237", "#bc2f45", "#f2bbc4", "#c26d2b"]
        self.metrics = {metric["id"]: {
            "name": metric["name"],
            "type": metric["type"],
        } for metric in summary["metrics"]
        }
        self.output_folder = f"{state}/plots"

    def aggregate_score(self, score):
        """
        Cycle through the plans and aggregate together the specified score.
        If the score is by plan, this will return a simple list as long as the chain. If the score is
        by district or by election, we'll return a dictionary with keys as districts or elections, values
        being the list of scores as long as the chain.
        """
        if score not in self.metrics.keys():
            raise ValueError(f"Score '{score}' is not in self.metrics!")
            
        if self.metrics[score]["type"] == "plan_wide":
            aggregation = []
            for plan in self.plans:
                aggregation.append(plan[score])
        elif self.metrics[score]["type"] == "election_level":
            aggregation = {e["name"]: [] for e in self.elections}
            for plan in self.plans:
                for e in aggregation.keys():
                    aggregation[e].append(plan[score][e])
        elif self.metrics[score]["type"] == "district_level":
            aggregation = {district: [] for district in self.districts}
            for plan in self.plans:
                for district in aggregation.keys():
                    aggregation[district].append(plan[score][district])
        return aggregation
    
    def get_bins_and_labels(self, 
                            val_range, 
                            unique_vals,
                            num_labels=8,
                           ):
#         if type(val_range[1]) is not int and len(unique_vals) <= num_labels:
#             _, hist_bins = np.histogram(list(unique_vals), bins=len(unique_vals))
#             bin_width = hist_bins[1] - hist_bins[0]
#         else:
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
                       figsize=FIG_SIZE, 
                      ):
        fig, ax = plt.subplots(figsize=figsize)
        score_range = (min(scores), max(scores))
        hist_bins, tick_bins, tick_labels, bin_width = self.get_bins_and_labels(score_range, set(scores))
        ax.set_xticks(tick_bins)
        ax.set_xticklabels(tick_labels, fontsize=TICK_SIZE)
        if len(set(scores)) < 20:
            rwidth = 0.8
            edgecolor = "black"
        else:
            rwidth = 1
            edgecolor = "white"
        ax.hist(scores,
                bins=hist_bins,
                color=self.default_color,
                rwidth=rwidth,
                edgecolor=edgecolor,
               )
        ax.get_yaxis().set_visible(False)
        return ax, bin_width
    
    def plot_violin(self,
                    scores,
                    labels,
                    figsize=FIG_SIZE,
                   ):
        fig, ax = plt.subplots(figsize=figsize)
        trimmed_scores = []
        for score in scores:
            low = np.percentile(score, 1)
            high = np.percentile(score, 99)
            trimmed_scores.append([s for s in score if s >= low and s <= high])
        parts = ax.violinplot(trimmed_scores,
                              showextrema=False,
#                               quantiles=[[0.01, 0.25, 0.5, 0.75, 0.99] for score_list in trimmed_scores],
                             )
        for pc in parts['bodies']:
            pc.set_facecolor(self.default_color)
            pc.set_edgecolor("black")
            pc.set_alpha(1)
        ax.set_xticklabels([""] + list(labels) + [""], fontsize=TICK_SIZE)
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
    
    def draw_arrow(self, ax, orientation):
        if orientation == "horizontal":
            x = sum(ax.get_xlim())/2
            y = ax.get_ylim()[1]
            rotation = 0
        elif orientation == "vertical":
            x = ax.get_xlim()[0]
            y = sum(ax.get_ylim())/2
            rotation = 90
            ax.tick_params(axis='y', pad=10)
        ax.text(x, 
                y,
                f"{self.party} advantage",
                ha="center",
                va="center",
                color="white",
                rotation=rotation,
                size=10,
                bbox=dict(
                    boxstyle="rarrow,pad=0.3",
                    fc=self.default_color,
                    ec="black",
                    )
               )
        return
    
    def add_ideal_band(self, ax, orientation):
        if orientation == "horizontal":
            orig_xlims = ax.get_xlim()
            xlims = [max(-0.08, ax.get_xlim()[0]), min(0.08, ax.get_xlim()[1])]
            ylims1 = [0,0]
            ylims2 = [ax.get_ylim()[1], ax.get_ylim()[1]]
        elif orientation == "vertical":
            orig_ylims = ax.get_ylim()
            xlims = ax.get_xlim()
            ylims1 = [-0.08, -0.08]
            ylims2 = [0.08, 0.08]
        ax.fill_between(xlims,
                        ylims1,
                        ylims2,
                        color=self.default_color,
                        alpha=0.1,
                        label="Theoretical Ideal"
                       )
        if orientation == "vertical":
            ax.set_xlim(xlims)
            ax.set_ylim(orig_ylims)
        else:
            ax.set_xlim(orig_xlims)
        ax.legend()
        return
    
    def plot(self,
             score,
             election=None,
             boxplot=False,
             raw=False,
             labels=True,
             save=False,
             figsize=FIG_SIZE,
            ):
        scores = self.aggregate_score(score)
        if self.metrics[score]["type"] == "plan_wide":
            if score == "num_split_counties" or score == "num_county_pieces":
                scores = scores[1000:]
            ax, bin_width = self.plot_histogram(scores,
                                                figsize=figsize,
                                               )
        elif self.metrics[score]["type"] == "election_level":
            if election:
                ax, bin_width = self.plot_histogram(scores[election],
                                                    figsize=figsize,
                                                   )
                self.draw_arrow(ax, "horizontal")
                if score == "efficiency_gap":
                    self.add_ideal_band(ax, "horizontal")
            else:
                ax = self.plot_violin([scores[e] for e in self.election_names], 
                                      self.election_names,
                                      figsize=FIG_SIZE,
                                     )
                self.draw_arrow(ax, "vertical")
                if score == "efficiency_gap":
                    self.add_ideal_band(ax, "vertical")
        elif self.metrics[score]["type"] == "district_level":
            POP_COL = self.pop_col if "VAP" not in score else "VAP"
            totpop_by_district = self.aggregate_score(POP_COL)
            sorted_districts = {d: [] for d in range(1, self.num_districts + 1)}
            for i in range(self.len):
                if raw:
                    sorted_scores = sorted([scores[d][i] for d in scores.keys()])
                else:
                    sorted_scores = sorted([scores[d][i] / totpop_by_district[d][i] for d in scores.keys()])
                for j, value in enumerate(sorted_scores):
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
        else:
            raise ValueError()
        if labels:
            label = self.metrics[score]["name"]
            if score == "num_party_districts":
                label = f"# Safe {self.party} Districts"
            elif score == "num_op_party_districts":
                label = f"# Safe {self.op_party} Districts"
            elif score == "num_competitive_districts":
                total_possible_districts = len(self.election_names) * self.num_districts
                label += f" (out of {total_possible_districts})"
            if election:
                label = f"{election} {label}"
            ax.set_xlabel(label, fontsize=LABEL_SIZE)
        if save:
            os.makedirs(self.output_folder, exist_ok=True)
            e = f"_{election}" if election else ""
            b = "_boxplot" if boxplot else ""
            r = "_raw" if raw else ""
            filename = f"{self.map_type}_{score}{e}{b}{r}_{self.chain_type}"
            plt.savefig(f"{self.output_folder}/{filename}.png", dpi=300, bbox_inches='tight')  
        return