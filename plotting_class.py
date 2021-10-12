from plotting_configuration import *
import matplotlib.pyplot as plt
import numpy as np
import random
import json
import gzip
import re
import os

def sort_elections(elec_list):
    tuplified_elecs = list(map(lambda x: re.findall(r"[^\W\d_]+|\d+",x), elec_list))
    sorted_tuples = sorted(tuplified_elecs, key=lambda x: x[1])
    return [tup[0] + tup[1] for tup in sorted_tuples]

class PlotFactory:
    def __init__(self, 
                 state, 
                 plan_type, 
                 eps, 
                 steps, 
                 method, 
                 ensemble_dir=None,
                 citizen_dir=None,
                 proposed_plans_file=None,
                 ):
        
        # make these parameters, ensemble_folder = None (if None, use JN's json, otherwise use path)
        # make a Dropbox relative path parameter, default to "~/Dropbox"
        HOMEDIR = os.path.expanduser("~")
        with open(f"{HOMEDIR}/Dropbox/PlanAnalysis/ensemble_analysis/ensemble_paths.json") as fin:
            dropbox_default_paths = json.load(fin)
        
        if ensemble_dir is None:
            ensemble_subdir = dropbox_default_paths[state]["recom"]
            ensemble_dir = f"{HOMEDIR}/Dropbox/PlanAnalysis/ensemble_analysis/{ensemble_subdir}"
        if citizen_dir is None:
            citizen_subdir = dropbox_default_paths[state]["citizen"]
            citizen_dir = f"{HOMEDIR}/Dropbox/PlanAnalysis/ensemble_analysis/{citizen_subdir}"
        if proposed_plans_file is None:
            proposed_plans = f"{HOMEDIR}/Dropbox/PlanAnalysis/proposed_plans/{state}/{plan_type}/proposed_plans.jsonl"

        with gzip.open(f"{ensemble_dir}/{state.lower()}_{plan_type}_{eps}_bal_{steps}_steps_{method}.jsonl.gz", "rb") as fe:
            ensemble_list = list(fe)
        ensemble_summary = json.loads(ensemble_list[0])
        self.ensemble_plans = [json.loads(j) for j in ensemble_list if json.loads(j)["type"] == "ensemble_plan"]
        self.ensemble_metrics = {metric["id"]: {
                            "name": metric["name"],
                            "type": metric["type"],
                        } for metric in ensemble_summary["metrics"]
                        }
        if os.path.exists(citizen_dir):
            with open(f"{citizen_dir}/{state.lower()}_{plan_type}_citizen_plans.jsonl", "rb") as fc:
                citizen_list = list(fc)
        else:
            citizen_list = []
        self.citizen_plans = [json.loads(j) for j in citizen_list if json.loads(j)["type"] == "citizen_plan"]

        if os.path.exists(proposed_plans):
            with open(proposed_plans, "rb") as fp:
                proposed_list = list(fp)
        else:
            proposed_list = []
        self.proposed_plans = [json.loads(j) for j in proposed_list if json.loads(j)["type"] == "proposed_plan"]
        self.proposed_names = [proposed_plan["name"] for proposed_plan in self.proposed_plans]

        self.party = ensemble_summary["pov_party"]
        self.parties = [candidate["name"] for candidate in ensemble_summary["elections"][0]["candidates"]]
        self.op_party = [party for party in self.parties if party != self.party][0]
        self.elections = ensemble_summary["elections"]
        self.election_names = sort_elections([election["name"] for election in ensemble_summary["elections"]])
        self.statewide_share = ensemble_summary["party_statewide_share"]

        self.num_districts = ensemble_summary["num_districts"]
        self.epsilon = ensemble_summary["epsilon"]
        self.chain_type = ensemble_summary["chain_type"]
        self.map_type = plan_type
        self.pop_col = ensemble_summary["pop_col"]

        self.default_color = "#5c676f"
        self.proposed_colors = ["#f3c042", "#96b237", "#bc2f45", "#8ca1c5", "#f2bbc4", "#c26d2b"]
        self.citizen_color = "#4693b3"
        self.output_folder = f"{state}/plots"
        

    def aggregate_score(self, score, kind="ensemble"):
        """
        Cycle through the plans and aggregate together the specified score.
        If the score is by plan, this will return a simple list as long as the chain. If the score is
        by district or by election, we'll return a dictionary with keys as districts or elections, values
        being the list of scores as long as the chain.
        """
        if score not in self.ensemble_metrics.keys():
            raise ValueError(f"Score '{score}' is not in self.ensemble_metrics: {list(self.ensemble_metrics.keys())}")
        
        plans = getattr(self, f"{kind}_plans")
        if self.ensemble_metrics[score]["type"] == "plan_wide":
            aggregation = []
            for plan in plans:
                aggregation.append(plan[score])
        elif self.ensemble_metrics[score]["type"] == "election_level":
            aggregation = {e["name"]: [] for e in self.elections}
            for plan in plans:
                for e in aggregation.keys():
                    aggregation[e].append(plan[score][e])
        elif self.ensemble_metrics[score]["type"] == "district_level":
            aggregation = {district: [] for district in plans[0][score].keys()}
            for plan in plans:
                for district in aggregation.keys():
                    aggregation[district].append(plan[score][district])
        return aggregation
    
    def get_bins_and_labels(self, val_range, unique_vals,num_labels=8):
        """
        Get necessary information for histograms. If we're working with only a few discrete, floating point values, then
        set the bin width to be relatively thin, Otherwise, adaptively set the bin width to the scale of our data. In
        both cases, shift the tick labels over to be in the center of the bins (shift by bin_width / 2).
        """
        if type(val_range[1]) is not int and len(unique_vals) <= 20:
            sorted_vals = sorted(unique_vals)
            bin_width = 0.2*(sorted_vals[1] - sorted_vals[0])
            hist_bins = []
            tick_bins = []
            tick_labels = []
            for val in sorted_vals:
                hist_bins.append(val - bin_width/2)
                hist_bins.append(val + 3*bin_width/2)
                tick_bins.append(val + bin_width/2)
                num = round(val * self.num_districts)
                tick_labels.append(f"{num}/{self.num_districts}")
        else:
            bin_width = 10 ** (np.floor(np.log10(val_range[1] - val_range[0])) - 1)
            if bin_width == 0.01: # TODO: is there a cleaner way to do this...
                bin_width /= 10
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
    
    def plot_histogram(self, ax, kind, score, scores, proposed_scores):
        """
        Plot a histogram with the ensemble scores in bins and the proposed plans' scores as vertical lines.
        If there are many unique values, use a white border on the bins to distinguish, otherwise reduce the
        bin width to 80%.
        """
        score_range = (min(scores + proposed_scores), max(scores + proposed_scores))
        hist_bins, tick_bins, tick_labels, bin_width = self.get_bins_and_labels(score_range, set(scores + proposed_scores)) # did this set mess anything up...
        ax.set_xticks(tick_bins)
        ax.set_xticklabels(tick_labels, fontsize=TICK_SIZE)
        rwidth    = 0.8     if len(set(scores)) < 20 else 1
        edgecolor = "black" if len(set(scores)) < 20 else "white"
        ax.hist(scores,
                bins=hist_bins,
                color=self.default_color if kind == "ensemble" else self.citizen_color,
                rwidth=rwidth,
                edgecolor=edgecolor,
                # alpha=0.5,
                density=True,
               )
        if proposed_scores:
            for i, s in enumerate(proposed_scores):
                jitter = random.uniform(-bin_width/5, bin_width/5) if proposed_scores.count(s) > 1 else 0
                ax.axvline(s + bin_width / 2 + jitter,
                           color=self.proposed_colors[i],
                           lw=2,
                           label=f"{self.proposed_names[i]}: {round(s,2)}",
                          )
            ax.legend()
        if self.ensemble_metrics[score]["type"] == "election_level":
            self.draw_arrow(ax, "horizontal")
        if score == "efficiency_gap":
            self.add_ideal_band(ax, "horizontal")
        ax.get_yaxis().set_visible(False)
        return ax
    
    def plot_violin(self, ax, kind, score, scores, proposed_scores, labels):
        """
        Plot a violin plot, which takes `scores` — a list of lists, where each sublist will be its own violin.
        Trim each sublist to only the values between the 1-99th percentile, to match our boxplits.
        """
        trimmed_scores = []
        for score_list in scores:
            low = np.percentile(score_list, 1)
            high = np.percentile(score_list, 99)
            # print(f"Only including scores between [{low}, {high}]")
            # low = np.percentile(score_list, 0)
            # high = np.percentile(score_list, 100)
            trimmed_scores.append([s for s in score_list if s >= low and s <= high])
        parts = ax.violinplot(trimmed_scores, showextrema=False)
        for pc in parts['bodies']:
            pc.set_facecolor(self.default_color if kind == "ensemble" else self.citizen_color)
            pc.set_edgecolor("black")
            pc.set_alpha(1)
        ax.set_xticks(range(1, len(labels)+1))
        ax.set_xticklabels(list(labels), fontsize=TICK_SIZE)
        ax.set_xlim(0.5, len(labels)+0.5)
        if self.ensemble_metrics[score]["type"] == "election_level":
            self.draw_arrow(ax, "vertical")
        if proposed_scores:
            for i in range(len(proposed_scores)):
                for j, s in enumerate(proposed_scores[i]):
                    jitter = random.uniform(-1/10, 1/10) if proposed_scores[i].count(s) > 1 else 0
                    ax.scatter(i + 1 + jitter,
                                s,
                                color=self.proposed_colors[j],
                                edgecolor='black',
                                s=100,
                                alpha=0.9,
                                label=self.proposed_names[j] if i == 0 else None,
                                )
            ax.legend()
        if score == "efficiency_gap":
            self.add_ideal_band(ax, "vertical")
        if score == "seats":
            for i, e in enumerate(self.election_names):
                proportional = self.statewide_share[e]*self.num_districts
                ax.plot([i+1-0.25, i+1+0.25,],
                        [proportional, proportional],
                        color='lightblue',
                        lw=4,
                        )
            ax.plot([i+1-0.25, i+1+0.25,],
                    [proportional, proportional],
                    color='lightblue',
                    lw=4,
                    label='proportionality',
                    )
            ax.axhline(0.5*self.num_districts,
                       color=self.default_color,
                       alpha=0.5, 
                       label="50%",
                      )
            ax.legend()
        return ax
    
    def plot_boxplot(self, ax, kind, score, scores, proposed_scores, labels):
        """
        Plot boxplots, which takes `scores` — a list of lists, where each sublist will be its own boxplot.
        The whiskers from each box will extend to the 1st and 99th percentiles of the data.
        TODO: labels aren't used here, but they are for the violins. should we standardize?
        """
        boxstyle = {
           "lw": 2,
            "color": self.default_color if kind == "ensemble" else self.citizen_color,
        }
        ax.boxplot(scores,
                   whis=(1,99),
                   showfliers=False,
                   boxprops=boxstyle,
                   whiskerprops=boxstyle,
                   capprops=boxstyle,
                   medianprops=boxstyle,
                  )
        if proposed_scores:
            for i in range(len(proposed_scores)):
                for j, s in enumerate(proposed_scores[i]):
                    jitter = random.uniform(-1/6, 1/6) if proposed_scores[i].count(s) > 1 else 0
                    ax.scatter(i + 1 + jitter,
                                s,
                                color=self.proposed_colors[j],
                                edgecolor='black',
                                s=100,
                                alpha=0.9,
                                label=self.proposed_names[j] if i == 0 else None,
                                )
            ax.legend()
        ax.set_xticklabels(labels)
        return ax
    
    def draw_arrow(self, ax, orientation):
        """
        For some partisan metrics, we want to draw an arrow showing where the POV-party's advantage is.
        TODO: make arrow placement smarter, it doesn't work so well right now.
        """
        if orientation == "horizontal":
            x = ax.get_xlim()[0]
            y = ax.get_ylim()[0] - 0.1*ax.get_ylim()[1]
            ha = "left"
            rotation = 0
        elif orientation == "vertical":
            x = ax.get_xlim()[0] - 0.06*(sum(map(lambda x: abs(x), ax.get_xlim())))
            y = sum(ax.get_ylim())/2
            ha = "center"
            rotation = 90
        ax.text(x, 
                y,
                f"{self.party[:3]}. advantage",
                ha=ha,
                va="center",
                color="white",
                rotation=rotation,
                size=10,
                bbox=dict(
                    boxstyle="rarrow,pad=0.3",
                    fc=self.default_color,
                    alpha=1,
                    ec="black",
                    )
               )
        return
    
    def add_ideal_band(self, ax, orientation):
        """
        Add a band on [-0.08, 0.08] to highlight the desired efficiency gap score.
        TODO: think about generalizing this to ideal value(s) of all partisan metrics
        """
        orig_xlims = ax.get_xlim()
        orig_ylims = ax.get_ylim()
        if orientation == "horizontal":
            xlims = [-0.08, 0.08]
            ylims1 = [orig_ylims[0], orig_ylims[0]]
            ylims2 = [orig_ylims[1], orig_ylims[1]]
        elif orientation == "vertical":
            xlims = orig_xlims
            ylims1 = [-0.08, -0.08]
            ylims2 = [0.08, 0.08]
        ax.fill_between(xlims,
                        ylims1,
                        ylims2,
                        color=self.default_color,
                        alpha=0.1,
                        label="Desirable Range"
                       )
        ax.set_xlim(orig_xlims)
        ax.set_ylim(orig_ylims)
        ax.legend()
        return

    def save_fig(self, score, election, boxplot, raw, save):
        if not save:
            return
        os.makedirs(self.output_folder, exist_ok=True)
        e = f"_{election}" if election else ""
        b = "_boxplot" if boxplot else ""
        r = "_raw" if raw else ""
        filename = f"{self.map_type}_{score}{e}{b}{r}_{self.chain_type}"
        plt.savefig(f"{self.output_folder}/{filename}.png", dpi=300, bbox_inches='tight')  
        plt.close()
        return

    def resort_populations(self, score, scores, raw, plan_type="ensemble"):
        POP_COL = self.pop_col if "VAP" not in score else "VAP" # HARDCODED TO MI
        totpop = self.aggregate_score(POP_COL, type=plan_type)
        sorted_districts = {d: [] for d in range(1, self.num_districts + 1)}
        num_plans = len(self.ensemble_plans) if plan_type == "ensemble" else len(self.proposed_plans)
        for i in range(num_plans):
            if raw:
                sorted_scores = sorted([scores[d][i] for d in scores.keys()])
            else:
                sorted_scores = sorted([scores[d][i] / totpop[d][i] for d in scores.keys()])
            for j, value in enumerate(sorted_scores):
                sorted_districts[j+1].append(value)
        result = list(sorted_districts.values())
        labels = list(sorted_districts.keys())
        if len(result) > 30:
            result = result[-30:]
            labels = labels[-30:]
        return result, labels

    def label_ax(self, ax, score, election):
        label = self.ensemble_metrics[score]["name"]
        if score == "num_party_districts":
            label = label.format(self.party)
        elif score == "num_op_party_districts":
            label = label.format(self.op_party)
        elif score == "num_competitive_districts":
            label += f" (out of {len(self.election_names) * self.num_districts})"
        elif score == "num_swing_districts" or score == "num_party_districts" or score == "num_op_party_districts":
            label += f" (out of {self.num_districts})"
        if election:
            label = f"{election} {label}"
        ax.set_xlabel(label, fontsize=LABEL_SIZE)
        return ax

    def sea_level_plot(self, labels=True, save=False, figsize=FIG_SIZE):
        """
        Make WI-style `sea-level` plot with each proposed plan over each election, compared to the proportional outcome.
        """
        proportional_share = [self.statewide_share[e] for e in self.election_names]
        seats_by_plan = [[self.proposed[i]["seats"][e] / self.num_districts for e in self.election_names] for i in range(len(self.proposed))]
        _, ax = plt.subplots(figsize=figsize)
        ax.plot(proportional_share,
                marker='o',
                markersize=10,
                lw=5,
                label="Proportionality",
                )
        for i, plan in enumerate(self.proposed_names):
            ax.plot(seats_by_plan[i],
                    marker='o',
                    linestyle='--',
                    color=self.proposed_colors[i],
                    label=plan,
                    )
        ax.set_xticks(range(len(self.election_names)))
        ax.set_xticklabels(self.election_names, fontsize=TICK_SIZE)
        ax.set_ylim(0,1)
        ax.legend()
        if labels:
            ax.set_xlabel("Election", fontsize=LABEL_SIZE)
            ax.set_ylabel(f"{self.party[:3]}. Share", fontsize=LABEL_SIZE)
        if save:
            os.makedirs(self.output_folder, exist_ok=True)
            filename = f"{self.map_type}_sea_level_{self.chain_type}"
            plt.savefig(f"{self.output_folder}/{filename}.png", dpi=300, bbox_inches='tight')  
            plt.close()
        return ax

    def plot(self, score, election=None, boxplot=False, raw=False, labels=True, save=False, with_proposed=True, kinds=["ensemble"]):
        fig, ax = plt.subplots(len(kinds), figsize=(12, 6*len(kinds)), sharex=False)
        for i, plan_kind in enumerate(kinds):
            this_ax = ax if len(kinds) == 1 else ax[i]
            scores = self.aggregate_score(score, kind=plan_kind)
            proposed_scores = self.aggregate_score(score, kind="proposed")
            this_ax = self.fill_ax(this_ax, score, scores, proposed_scores, plan_kind, election, boxplot, raw, labels)
        plt.show()
        return

    
    def fill_ax(self, ax, score, scores, proposed_scores, kind, election, boxplot, raw, labels):
        if self.ensemble_metrics[score]["type"] == "plan_wide":
            if kind == "ensemble" and (score == "num_split_counties" or score == "num_county_pieces"):
                scores = scores[1000:]
            ax = self.plot_histogram(ax,
                                     kind,
                                     score,
                                     scores,
                                     proposed_scores,
                                    )
        elif self.ensemble_metrics[score]["type"] == "election_level":
            if election:
                ax = self.plot_histogram(ax,
                                         kind,
                                         score,
                                         scores[election],
                                         proposed_scores[election] if proposed_scores else [],
                                        )
            else:
                ax = self.plot_violin(ax,
                                      kind,
                                      score,
                                      [scores[e] for e in self.election_names], 
                                      [proposed_scores[e] for e in self.election_names] if proposed_scores else [],
                                      self.election_names,
                                     )
        elif self.ensemble_metrics[score]["type"] == "district_level":
            sorted_scores, labels = self.resort_populations(score, scores, raw, plan_type="ensemble")
            sorted_proposed_scores, labels = self.resort_populations(score, proposed_scores, raw, plan_type="proposed") if proposed_scores else []
            plotting_func = getattr(self, "plot_boxplot" if boxplot else "plot_violin")
            ax = plotting_func(ax,
                               kind, 
                               score,
                               sorted_scores,
                               sorted_proposed_scores,
                               labels,
                              )
            if not raw and max(sorted_scores[-1]) > 0.4:
                ax.set_ylim(0,1)
                ax.axhline(0.5,
                           color=self.default_color,
                           alpha=1,
                           label=f"50% {self.metrics[score]['name']}")
                ax.legend()
        if labels:
            ax = self.label_ax(ax, score, election)
        # self.save_fig(score, election, boxplot, raw, save)
        return ax