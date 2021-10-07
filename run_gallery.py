from plotting_class import *


print("Loading jsonl...")
scores = PlotFactory("Virginia", "state_senate", 0.02, 100000, "county_aware")

scores.sea_level_plot(save=True)
for score in scores.metrics.keys():
    print(f"Plotting {score}")
    if scores.metrics[score]["type"] == "district_level":
        continue
    if scores.metrics[score]["type"] == "plan_wide":
        if score == "num_party_wins_by_district":
            continue
        scores.plot(score, save=True)
    elif scores.metrics[score]["type"] == "election_level":
        scores.plot(score, save=True)
        for election in scores.election_names:
            scores.plot(score, election=election, save=True)
    # if scores.metrics[score]["type"] == "district_level":
    #     # continue
    #     # if "VAP" not in score or score == "VAP20":
    #     #     continue
    #     for boxplot in [True, False]:
    #         for raw in [True, False]:
    #             scores.plot(score, boxplot=boxplot, raw=raw, save=True)

