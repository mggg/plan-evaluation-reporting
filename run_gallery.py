from plotting_class import *
import random



print("Loading jsonl...")
scores = PlotFactory("Michigan", "state_senate", 0.02, 100000, "county_aware")

for score in scores.metrics.keys():
    print(f"Plotting {score}")
    if scores.metrics[score]["type"] == "plan_wide":
        if score == "num_party_wins_by_district":
            continue
        scores.plot(score, save=True)
    elif scores.metrics[score]["type"] == "election_level":
        scores.plot(score, save=True)
        for election in scores.election_names:
            scores.plot(score, election=election, save=True)
    elif scores.metrics[score]["type"] == "district_level":
        # continue
        if "VAP" not in score:
            continue
        for boxplot in [True, False]:
            for raw in [True, False]:
                scores.plot(score, boxplot=boxplot, raw=raw, save=True)

