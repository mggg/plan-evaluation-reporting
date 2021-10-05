from plotting_class import *
import random

print("Loading neutral score jsonl...")
neutral_scores = PlotFactory("Michigan", "congress", 0.01, 100000, "neutral")
print("Loading county_aware score jsonl...")
aware_scores = PlotFactory("Michigan", "congress", 0.01, 100000, "county_aware")

for scores in [neutral_scores, aware_scores]:
    print(f"Starting {scores.chain_type}...")
    for score, score_info in scores.scores.items():
        # print(" -- plotting by_district scores")
        if score_info["score_type"] == "by_district" and (score == "BVAP" or score == "HVAP" or score == "TOTPOP"):
            for boxplot in [True, False]:
                for raw in [True, False]:
                    num_hypotheticals = random.randrange(1,6)
                    scores.plot_demographics(score, boxplot=boxplot, raw=raw, hypotheticals=num_hypotheticals, save=True)
        # print(" -- plotting by_election scores")
        if score_info["score_type"] == "by_election":
            num_hypotheticals = random.randrange(1,6)
            scores.plot_election_score(score, hypotheticals=num_hypotheticals, save=True)
            for election in scores.election_names:
                num_hypotheticals = random.randrange(1,6)
                scores.plot_election_score(score, election=election, hypotheticals=num_hypotheticals, save=True)
        # print(" -- plotting by_plan scores")
        if score_info["score_type"] == "by_plan":
            num_hypotheticals = random.randrange(1,6)
            scores.plot_plan_score(score, hypotheticals=num_hypotheticals, save=True)

