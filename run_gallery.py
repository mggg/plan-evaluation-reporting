from plotting_class import *


print("Loading house jsonl...")
house = PlotFactory("Michigan", "state_house", output_dir="Michigan/plots1013")
# print("loading congress jsonl...")
# congress = PlotFactory("Michigan", "congress", 0.01, 100000, "county_aware")

kind_types = [["ensemble", "proposed"]]#, ["citizen", "proposed"]]

for scores in [house]:
    # scores.sea_level_plot(save=True)
    for score in scores.ensemble_metrics.keys():
        print(f"Plotting {score}")
        if scores.ensemble_metrics[score]["type"] == "plan_wide":
            # continue
            if score == "num_party_wins_by_district":
                continue
            scores.plot(score, kinds=["ensemble", "citizen", "proposed"], save=True)
        elif scores.ensemble_metrics[score]["type"] == "election_level":
            # continue
            for kind in kind_types:
                scores.plot(score, kinds=kind, save=True)
            for election in scores.election_names:
                scores.plot(score, election=election, kinds=["ensemble", "citizen", "proposed"], save=True)
        if scores.ensemble_metrics[score]["type"] == "district_level":
            if not (score == "BVAP" or score == "WVAP" or score == "HVAP"):
                continue
            for boxplot in [True, False]:
                for raw in [False]:
                    for kind in kind_types:
                        scores.plot(score, kinds=kind, boxplot=boxplot, raw=raw, save=True)

