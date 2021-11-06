from plotting_configuration import *
import matplotlib.pyplot as plt
import numpy as np
import random
import json
import gzip
import re
import os

def sort_elections(elec_list):
    """
    Helper function to sort elections chronologically for plotting. Assumes the last two characters
    in the election name are the year, e.g. "SEN18"
    """
    tuplified_elecs = list(map(lambda x: re.findall(r"[^\W\d_]+|\d+",x), elec_list))
    sorted_tuples = sorted(tuplified_elecs, key=lambda x: x[1])
    return [tup[0] + tup[1] for tup in sorted_tuples]

class PlotFactory:
    def __init__(self, state, plan_type, steps=100000, method="county_aware", ensemble_dir=None, citizen_dir=None, proposed_plans_file=None, output_dir=None, proposed_winnow=[]):
        """
        The PlotFactory class is initialized with the state and plan type (congress, state_senate, or state_house). By default, we will
        look for ensembles, citizen ensembles, and proposed plans in the PlanAnalysis Dropbox directory, but users can specify their own (local)
        directories for each, if needed. The class stores a list of scores for each kind of plan (ensemble, citizen, proposed), with an
        empty list if there is no citizen ensemble or proposed plan jsonl. If we end up saving the plots, they will be saved by default in the 
        {state}/plans folder in the plan-evaluation-reporting GitHub repo, but we could specify an alternate output directory.
        """
        if plan_type == "congress":
            eps = 0.01
        elif plan_type == "state_senate":
            eps = 0.02
        elif plan_type == "state_house":
            eps = 0.05
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
        else:
            proposed_plans = proposed_plans_file
        if output_dir is None:
            output_dir = f"{state}/plots"

        with gzip.open(f"{ensemble_dir}/{state.lower()}_{plan_type}_{eps}_bal_{steps}_steps_{method}.jsonl.gz", "rb") as fe:
            ensemble_list = list(fe)
        ensemble_summary = json.loads(ensemble_list[0])
        self.ensemble_plans = [json.loads(j) for j in ensemble_list if json.loads(j)["type"] == "ensemble_plan"]
        def get_maxpopdev(plan):
            totpop = plan["TOTPOP"]
            population = sum(totpop.values())
            ideal_pop = population / len(totpop)
            devs = []
            for pop in totpop.values():
                devs.append(abs(pop - ideal_pop))
            return max(devs)
        # self.ensemble_plans = [plan for plan in self.ensemble_plans if get_maxpopdev(plan) < 500]
        # print(f"Winnowed ensemble plans to {len(self.ensemble_plans)}")
        self.ensemble_metrics = {metric["id"]: {
                            "name": metric["name"],
                            "type": metric["type"],
                        } for metric in ensemble_summary["metrics"]
                        }
        
        citizen_list = []
        if os.path.exists(citizen_dir):
            if os.path.exists(f"{citizen_dir}/{state.lower()}_{plan_type}_citizen_plans.jsonl"):
                with open(f"{citizen_dir}/{state.lower()}_{plan_type}_citizen_plans.jsonl", "rb") as fc:
                    citizen_list = list(fc)
        self.citizen_plans = [json.loads(j) for j in citizen_list if json.loads(j)["type"] == "citizen_plan"]
        # del self.citizen_plans[4]

        proposed_list = []
        if os.path.exists(proposed_plans):
            with open(proposed_plans, "rb") as fp:
                proposed_list = list(fp)
            proposed_summary = json.loads(proposed_list[0])
            self.proposed_election_names = sort_elections(election["name"] for election in proposed_summary["elections"])
        self.proposed_plans = [json.loads(j) for j in proposed_list if json.loads(j)["type"] == "proposed_plan" and json.loads(j)["name"] not in proposed_winnow]
        self.proposed_names = [proposed_plan["name"] for proposed_plan in self.proposed_plans]
        # print(self.proposed_names)

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
        self.proposed_colors = ["#f3c042", "#aa99e4", "#96b237", "#bc2f45", "#8cd1c5", "#c26d2b", "#f2bbc4", "#00926a", "#2a4ed8", "#8c644f"]
        # self.proposed_colors = ["#fc4f65", "#f3c042", "#bc2f45", "#8cd1c5", "#c26d2b", "#f2bbc4", "#00926a", "#aa99e4", "#2a4ed8", "#8c644f"]
        # self.proposed_colors = ["#f3c042", "#c26d2b", "purple", "#aa99e4", "#2a4ed8", "#00926a"]
        # self.proposed_colors = ["orange", "red", "purple", "violet", "green"]
        # self.proposed_colors = ["orange", "purple", "violet", "red", "green"]
        # self.proposed_colors = ["orange", "#f2bbc4", "#bc2f45", "#c26d2b", "#8cd1c5", "green"]
        # self.proposed_colors = ["purple", "green", "blue", "orange"]
        self.citizen_color = "#4693b3"
        self.output_folder = output_dir
        

    def aggregate_score(self, score, kind="ensemble"):
        """
        Cycle through the plans (either ensemble, citizen, or proposed) and aggregate together the specified score. 
        If the score is by plan, this will return a simple list as long as the chain. If the score is by district or 
        by election, we'll return a dictionary with keys as districts or elections, values being the list of scores as long as the chain.
        """
        if score not in self.ensemble_metrics.keys():
            raise ValueError(f"Score '{score}' is not in self.ensemble_metrics: {list(self.ensemble_metrics.keys())}")
        
        plans = getattr(self, f"{kind}_plans")

        elections = self.election_names if kind=="ensemble" or kind=="citizen" else self.proposed_election_names
        if self.ensemble_metrics[score]["type"] == "plan_wide":
            aggregation = []
            for plan in plans:
                aggregation.append(plan[score])
        elif self.ensemble_metrics[score]["type"] == "election_level":
            aggregation = {e: [] for e in elections}
            for plan in plans:
                for e in aggregation.keys():
                    aggregation[e].append(plan[score][e])
        elif self.ensemble_metrics[score]["type"] == "district_level":
            # replace UT metric since it doesn't line up with ensemble
            # new_score = score + "20" if kind == "proposed" or kind == "citizen" else score
            new_score = score
            aggregation = {district: [] for district in self.ensemble_plans[0][score].keys()}
            for i, plan in enumerate(plans):
                for district in aggregation.keys():
                    plan_district = str(int(district)-0) if (kind == "proposed" or kind == "citizen") else district
                    # print(new_score)
                    try:
                        aggregation[district].append(plan[new_score][plan_district])
                        # if kind == "proposed":
                        #     print(i, plan[new_score].keys())
                    except:
                        print(kind, i)
                        print(plan_district)
                        print(i, plan[new_score].keys())
                        raise ValueError
        return aggregation

    def summarize(self, score):
        scores = self.aggregate_score(score)
        if type(scores) is dict:
            new_scores = []
            for l in scores.values():
                new_scores += l
            scores = new_scores
        print(f"Mean {score}: {np.mean(scores):.3f}")
        print(f"Median {score}: {np.median(scores):.3f}")
        return
    
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
                bin_width /= 5
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
    
    def plot_histogram(self, ax, score, scores):
        """
        Plot a histogram with the ensemble scores in bins and the proposed plans' scores as vertical lines.
        If there are many unique values, use a white border on the bins to distinguish, otherwise reduce the
        bin width to 80%.
        """
        all_scores = scores["ensemble"] + scores["citizen"] + scores["proposed"]
        score_range = (min(all_scores), max(all_scores))
        hist_bins, tick_bins, tick_labels, bin_width = self.get_bins_and_labels(score_range, set(all_scores))
        ax.set_xticks(tick_bins)
        ax.set_xticklabels(tick_labels, fontsize=TICK_SIZE)
        rwidth    = 0.8     if len(set(scores)) < 20 else 1
        edgecolor = "black" if len(set(scores)) < 20 else "white"
        alpha = 0.7 if scores["ensemble"] and scores["citizen"] else 1
        for kind in ["ensemble", "citizen"]:
            if scores[kind]:
                ax.hist(scores[kind],
                        bins=hist_bins,
                        color=self.default_color if kind == "ensemble" else self.citizen_color,
                        rwidth=rwidth,
                        edgecolor=edgecolor,
                        alpha=alpha,
                        density=True,
                    )
        if scores["proposed"]:
            for i, s in enumerate(scores["proposed"]):
                jitter = random.uniform(-bin_width/5, bin_width/5) if scores["proposed"].count(s) > 1 else 0
                ax.axvline(s + bin_width / 2 + jitter,
                           color=self.proposed_colors[i],
                           lw=2,
                           label=f"{self.proposed_names[i]}: {round(s,2)}",
                          )
            ax.legend()
        if self.ensemble_metrics[score]["type"] == "election_level":
            self.draw_arrow(ax, score, "horizontal")
        if score == "efficiency_gap":
            self.add_ideal_band(ax, "horizontal")
        ax.get_yaxis().set_visible(False)
        return ax
    
    def plot_violin(self, ax, kind, score, scores, proposed_scores, labels):
        """
        Plot a violin plot, which takes `scores` — a list of lists, where each sublist will be its own violin.
        Proposed scores will be plotted as colored circles on their respective violin.
        Color the violins conditioned on the kind of the scores (ensemble or citizen), and if plotting ensemble, then
        trim each sublist to only the values between the 1-99th percentile, to match our boxplits (otherwise don't trim).
        """
        trimmed_scores = []
        for score_list in scores:
            low = np.percentile(score_list, 1 if kind=="ensemble" else 0)
            high = np.percentile(score_list, 99 if kind=="ensemble" else 100)
            # print(f"Only including scores between [{low}, {high}]")
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
            self.draw_arrow(ax, score, "vertical")
        if proposed_scores:
            for i in range(len(proposed_scores)):
                for j, s in enumerate(proposed_scores[i]):
                    # horizontally jitter proposed scores regardless of whether there are multiple scores at the same height
                    jitter = random.uniform(-1/3, 1/3) #if proposed_scores[i].count(s) > 1 else 0
                    ax.scatter(i + 1 + jitter,
                                s,
                                color=self.proposed_colors[j],
                                edgecolor='black',
                                s=100,
                                alpha=0.7,
                                label=self.proposed_names[j] if i == 0 else None,
                                )
            ax.legend()
        if score == "efficiency_gap":
            self.add_ideal_band(ax, "vertical")
        # for the seats plot, add a 50% marker and proportionality bands on each election
        if score == "seats":
            for i, e in enumerate(self.election_names):
                proportional = self.statewide_share[e]*self.num_districts
                ax.plot([i+1-0.25, i+1+0.25,],
                        [proportional, proportional],
                        color='lightblue',
                        lw=4,
                        label='proportionality' if i == 0 else None,
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
        This works the same as the violin plots, but plots boxplots instead of violins.
        Even though `score` is not used, the arguments are kept the same so that the two methods can
        be called with the same arguments.
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
                    jitter = random.uniform(-1/3, 1/3) #if proposed_scores[i].count(s) > 1 else 0
                    ax.scatter(i + 1 + jitter,
                                s,
                                color=self.proposed_colors[j],
                                edgecolor='black',
                                s=100,
                                alpha=0.7,
                                label=self.proposed_names[j] if i == 0 else None,
                                )
            ax.legend()
        ax.set_xticklabels(labels)
        return ax
    
    def draw_arrow(self, ax, score, orientation):
        """
        For some partisan metrics, we want to draw an arrow showing where the POV-party's advantage is.
        Depending on the orientation of the scores (histograms have scores arranged horizontally, violinplots
        have scores arranged vertically), we either place the arrow at the bottom left, pointing rightward,
        or in the middle of the y-axis, pointing up.
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
        term = "seats" if score == "seats" else "advantage"
        ax.text(x, y,
                f"{self.party[:3]}. {term}",
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

    def save_fig(self, kinds, score, election, boxplot, raw, save):
        """
        If `save`, save the figure in the output folder specified in __init__(), named
        according to the score and what kinds of plans are plotted.
        """
        if not save:
            return
        os.makedirs(f"{self.output_folder}/all_plots/", exist_ok=True)
        os.makedirs(f"{self.output_folder}/top_plots/", exist_ok=True)
        e = f"_{election}" if election else ""
        b = "_boxplot" if boxplot else ""
        r = "_raw" if raw else ""
        kinds = "_".join(kinds)
        filename = f"{self.map_type}_{score}{e}{b}{r}_{kinds}"
        if "BVAP" in score or "HVAP" in score or "num" in score or (score == "seats" and not election):
            plt.savefig(f"{self.output_folder}/top_plots/{filename}.png", dpi=300, bbox_inches='tight')
        plt.savefig(f"{self.output_folder}/all_plots/{filename}.png", dpi=300, bbox_inches='tight')  
        plt.close()
        return

    def resort_populations(self, score, scores, raw, kind="ensemble"):
        """
        Helper function for demographic boxplots.
        """
        VAP_COL = "VAP20" if "VAP20" in self.ensemble_metrics.keys() else "VAP"
        POP_COL = self.pop_col if "VAP" not in score else VAP_COL
        totpop = self.aggregate_score(POP_COL, kind=kind)
        sorted_districts = {d: [] for d in range(1, self.num_districts + 1)}
        num_plans = len(getattr(self, f"{kind}_plans"))
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
        """
        Helper function to label the x-axis according to the score we're plotting.
        """
        label = self.ensemble_metrics[score]["name"]
        if score == "num_party_districts":
            label = label.replace("Safe", "Always")
            label = label.format(self.party)
        elif score == "num_op_party_districts":
            label = label.replace("Safe", "Always")
            label = label.format(self.op_party)
        elif score == "num_competitive_districts":
            label = label.replace("Districts", "Contests")
            label += f" (within 6%, out of {len(self.election_names) * self.num_districts})"
        elif score == "num_swing_districts" or score == "num_party_districts" or score == "num_op_party_districts":
            label += f" (out of {self.num_districts})"
        if election:
            label = f"{election} {label}"
        ax.set_xlabel(label, fontsize=LABEL_SIZE)
        return ax

    def plot(self, score, election=None, boxplot=False, raw=False, labels=True, save=False, kinds=["ensemble"]):
        """
        Driver function to actually plot a score. `scores` is a dictionary where the keys are the kinds of plans and the values
        are the aggregated scores across that kind of plan, with an empty list if we haven't specified that we want those kinds.
        We then call the `.fill_ax()` method to actually plot the scores, and then optionally save the figure.
        """
        _, ax = plt.subplots(figsize=FIG_SIZE)
        scores = {kind:self.aggregate_score(score, kind=kind) if kind in kinds else [] for kind in ["ensemble", "citizen", "proposed"]}
        ax = self.fill_ax(ax, kinds, score, scores, election, boxplot, raw, labels)
        self.save_fig(kinds, score, election, boxplot, raw, save)
        return

    
    def fill_ax(self, ax, kinds, score, scores, election, boxplot, raw, labels):
        """
        If your score is by election, you can either not specify an election to get a violinplot of the score over all elections, or 
        choose an election to plot your score as a histogram. If the score is by district (like a demographic group), you can either 
        choose to plot a violinplot (default) or set boxplot=True to get boxplots. Setting raw=True will show demographic groups as 
        counts instead of percents.

        For all plots, x-axis labels are True, and the plot won't save by default. Lastly, you can choose what kinds of plans
        to plot: for histograms, setting kinds = ["ensemble", "citizen", "proposed"] will plot the ensemble and citizen plans on top
        of each other as histograms, with the proposed plans overlaid as vertical lines. For violinplots and boxplots, only the first
        plan kind listed in `kinds` will be plotted as a violin or a box, with "proposed" plans listed as colored circles if "proposed"
        is in `kinds`.
        """
        if self.ensemble_metrics[score]["type"] == "plan_wide":
            if (score == "num_split_counties" or score == "num_county_pieces") and len(self.ensemble_plans) > 1000:
                scores["ensemble"] = scores["ensemble"][1000:]
            ax = self.plot_histogram(ax,
                                     score,
                                     scores,
                                    )
        elif self.ensemble_metrics[score]["type"] == "election_level":
            if election:
                scores = {kind:scores[kind][election] if scores[kind] else [] for kind in scores.keys()}
                ax = self.plot_histogram(ax,
                                         score,
                                         scores,
                                        )
            else:
                ax = self.plot_violin(ax,
                                      kinds[0],
                                      score,
                                      [scores[kinds[0]][e] for e in self.election_names], 
                                      [scores["proposed"][e] for e in self.election_names] if scores["proposed"] else [],
                                      self.election_names,
                                     )
        elif self.ensemble_metrics[score]["type"] == "district_level":
            # scores = {kind:scores[kind][election] if scores[kind] else [] for kind in scores.keys()}
            sorted_scores, labels = self.resort_populations(score, scores[kinds[0]], raw, kind=kinds[0])
            sorted_proposed_scores, _ = self.resort_populations(score, scores["proposed"], raw, kind="proposed") if scores["proposed"] else [], []
            if len(sorted_proposed_scores) > 0:
                sorted_proposed_scores = sorted_proposed_scores[0] # TODO: figure out why we need to index here, seems weird...
            plotting_func = getattr(self, "plot_boxplot" if boxplot else "plot_violin")
            ax = plotting_func(ax,
                               kinds[0], 
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
                           label=f"50% {self.ensemble_metrics[score]['name']}")
                ax.legend()
        if labels:
            ax = self.label_ax(ax, score, election)
        return ax

    def plot_sea_level(self, labels=True, save=False):
        proportional_share = [self.statewide_share[e] for  e in self.election_names]
        seats_by_plan = [[self.proposed_plans[i]["seats"][e] / self.num_districts for e in self.election_names] for i in range(len(self.proposed_plans))]
        _, ax = plt.subplots(figsize=FIG_SIZE)
        ax.plot(proportional_share,
                marker='o',
                markersize=10,
                lw=5,
                label="Proportionality",
                )
        for i, plan in enumerate(self.proposed_names):
            for j in range(len(seats_by_plan[i])):
                jitter = random.uniform(-0.02, 0.02) if len(set([seats_by_plan[k][j] for k in range(len(self.proposed_names))])) > 1 else 0
                seats_by_plan[i][j] = seats_by_plan[i][j] + jitter
            ax.plot(seats_by_plan[i],
                    marker='o',
                    linestyle='--',
                    color=self.proposed_colors[i],
                    label=plan,
                    )
        if self.num_districts <= 16:
            yticks = np.arange(0, 1 + 1/self.num_districts, 1/self.num_districts)
            yticklabels = []
            for i in range(self.num_districts + 1):
                yticklabels.append(f"{i}/{self.num_districts}")
            ax.set_yticks(yticks)
            ax.set_yticklabels(yticklabels)
        ax.axhline(0.5, color=self.default_color, label="50%")
        ax.set_xticks(range(len(self.election_names)))
        ax.set_xticklabels(self.election_names, fontsize=TICK_SIZE)
        ax.set_ylim(-0.02,1)
        ax.legend()
        if labels:
            ax.set_xlabel("Election", fontsize=LABEL_SIZE)
            ax.set_ylabel(f"{self.party[:3]}. Share", fontsize=LABEL_SIZE)
        if save:
            os.makedirs(f"{self.output_folder}/top_plots", exist_ok=True)
            filename = f"{self.map_type}_sea_level"
            plt.savefig(f"{self.output_folder}/top_plots/{filename}.png", dpi=300, bbox_inches='tight')  
            plt.close()
        return ax