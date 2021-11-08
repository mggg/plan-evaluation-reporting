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
parser.add_argument("--ensemble_dir", type=str, metavar="ensemble directory")
parser.add_argument("--citizen_dir", type=str, metavar="citizen directory")
parser.add_argument("--proposed_plans_file", type=str, metavar="proposed plans file")
parser.add_argument("--proposed_winnow", type=str, nargs="*", metavar="proposed plans to remove", default=[])
args = parser.parse_args()

STATE = args.st
PLAN_TYPE = args.map
output_dir = args.output_dir
proposed_plans_file = args.proposed_plans_file
proposed_winnow = args.proposed_winnow
ensemble_dir = args.ensemble_dir
citizen_dir = args.citizen_dir


print(f"Loading {STATE} {PLAN_TYPE} scores...")
scores = PlotFactory(STATE, PLAN_TYPE, ensemble_dir=ensemble_dir, citizen_dir=citizen_dir, 
                     proposed_plans_file=proposed_plans_file, output_dir=output_dir, proposed_winnow=proposed_winnow)
print(f"num proposed plans: {len(scores.proposed_plans)}")
scores.plot_sea_level(save=True)

all_kinds = []
for kind in ["ensemble"]: # add/remove citizen if we have it/don't have it
    plans = getattr(scores, f"{kind}_plans")
    if len(plans) > 0:
        all_kinds.append(kind)

kind_types = []
for kind in ["ensemble"]: # add/remove citizen if we have it/don't have it
    if kind in all_kinds:
        if "proposed" in all_kinds:
            kind_types.append([kind, "proposed"]) 
        else:
            kind_types.append([kind])

for score in scores.ensemble_metrics.keys():
    if scores.ensemble_metrics[score]["type"] == "plan_wide":
        # continue
        print(f"Plotting {score}")
        if score == "num_party_wins_by_district" or score == "cut_edges":
            continue
        try:
            scores.plot(score, kinds=all_kinds, save=True)
        except:
            print(f"COULD NOT PLOT {score}")
            continue
    elif scores.ensemble_metrics[score]["type"] == "election_level":
        # continue
        print(f"Plotting {score}")
        for kind in kind_types:
            scores.plot(score, kinds=kind, save=True)
        for election in scores.election_names:
            # if score == "partisan_bias" or score == "eguia_county":
            #    continue
            try:
                scores.plot(score, election=election, kinds=all_kinds, save=True)
            except:
                print(f"COULD NOT PLOT {score} {election}")
                continue
    elif scores.ensemble_metrics[score]["type"] == "district_level":
        print(f"Plotting {score}")
        if not ("BVAP" in score or "HVAP" in score or "WVAP" in score):
            continue
        for boxplot in [True]:
            for raw in [False]:
                for kind in kind_types:
                    scores.plot(score, kinds=kind, boxplot=boxplot, raw=raw, save=True)

