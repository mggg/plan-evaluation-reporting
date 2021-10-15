from plotting_class import *
from configuration import *
import argparse

parser = argparse.ArgumentParser(description="Gallery Generator",
                                 prog="run_gallery.py")
parser.add_argument("st", metavar="state", type=str,
                    choices=SUPPORTED_STATES,
                    help="Which state to generate plots for?")
parser.add_argument("map", metavar="map", type=str,
                    choices=SUPPORTED_PLAN_TYPES,
                    help="the map to redistrict")
parser.add_argument("--output_dir", type=str, metavar="output directory")
args = parser.parse_args()

STATE = args.st
PLAN_TYPE = args.map
output_dir = args.output_dir


print(f"Loading {STATE} {PLAN_TYPE} scores...")
scores = PlotFactory(STATE, PLAN_TYPE, output_dir=output_dir)

all_kinds = []
for kind in ["ensemble", "citizen", "proposed"]:
    plans = getattr(scores, f"{kind}_plans")
    if len(plans) > 0:
        all_kinds.append(kind)

kind_types = []
for kind in ["ensemble", "citizen"]:
    if kind in all_kinds:
        if "proposed" in all_kinds:
            kind_types.append([kind, "proposed"])
        else:
            kind_types.append([kind])

for score in scores.ensemble_metrics.keys():
    if scores.ensemble_metrics[score]["type"] == "plan_wide":
        print(f"Plotting {score}")
        if score == "num_party_wins_by_district":
            continue
        scores.plot(score, kinds=all_kinds, save=True)
    elif scores.ensemble_metrics[score]["type"] == "election_level":
        print(f"Plotting {score}")
        for kind in kind_types:
            scores.plot(score, kinds=kind, save=True)
        for election in scores.election_names:
            scores.plot(score, election=election, kinds=all_kinds, save=True)
    elif scores.ensemble_metrics[score]["type"] == "district_level":
        print(f"Plotting {score}")
        if not (score == "BVAP" or score == "WVAP" or score == "HVAP"):
            continue
        for boxplot in [True, False]:
            for raw in [False]:
                for kind in kind_types:
                    scores.plot(score, kinds=kind, boxplot=boxplot, raw=raw, save=True)

