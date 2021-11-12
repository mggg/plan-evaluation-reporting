from plotting_class import *
import pandas as pd
import argparse

parser = argparse.ArgumentParser(description="Proposed Plans Summarizer",
                                 prog="summarize_proposed_plans.py")
parser.add_argument("st", metavar="state", type=str,
                    help="Which state to do")
parser.add_argument("map", type=str,
                    help="Which districting level to use")
# parser.add_argument("input", metavar="proposed_plans_file", type=str,
#                     help="Which json to use to populate?")
args = parser.parse_args()

state = args.st
map = args.map

HOMEDIR = os.path.expanduser("~")
with open(f"{HOMEDIR}/Dropbox/PlanAnalysis/ensemble_analysis/ensemble_paths.json") as fin:
    dropbox_default_paths = json.load(fin)

ensemble_subdir = dropbox_default_paths[state]["recom"]
proposed_plans_file = f"{HOMEDIR}/Dropbox/PlanAnalysis/proposed_plans/{state}/{map}/proposed_plans.jsonl"

def initialize_df(proposed_list):
    proposed_summary = json.loads(proposed_list[0])
    proposed_plans = [json.loads(j) for j in proposed_list if json.loads(j)["type"] == "proposed_plan"]
    proposed_names = [proposed_plan["name"] for proposed_plan in proposed_plans]
    elections = [d["name"] for d in proposed_summary["elections"]]
    
    plan_scores = set()
    election_scores = set()
    district_scores = []
    
    for metric_dict in proposed_summary["metrics"]:
        metric = metric_dict["id"]
        metric_type = metric_dict["type"]
        if metric == "num_party_wins_by_district":
            continue
        if metric_type == "plan_wide":
            plan_scores.add(metric)
        elif metric_type == "election_level":
            for election in elections:
                election_scores.add(f"{metric}-{election}")
        elif metric_type == "district_level" and "BVAP" in metric or "HVAP" in metric:
            for district in range(1, proposed_summary["num_districts"] + 1):
                district_scores.append(f"{metric}-{district}")
    df = pd.DataFrame(index=sorted(plan_scores) + sorted(election_scores) + district_scores, columns=proposed_names + ["Ensemble-Mean", "Ensemble-Median"])
    return df

def fill_df(proposed_list, df):
    proposed_summary = json.loads(proposed_list[0])
    proposed_plans = [json.loads(j) for j in proposed_list if json.loads(j)["type"] == "proposed_plan"]

    try:
        factory = PlotFactory(state, map)
    except:
        factory = None
    
    for plan in proposed_plans:
        for metric in df.index:
            if "-" not in metric:
                df[plan["name"]].loc[metric] = plan[metric]
                if factory:
                    scores = factory.aggregate_score(metric)
                    df["Ensemble-Mean"].loc[metric] = np.mean(scores)
                    df["Ensemble-Median"].loc[metric] = np.median(scores)
            else:
                first = metric.split("-")[0]
                second = metric.split("-")[1]
                if "VAP" in metric:
                    sorted_group = sorted([plan[first][str(d)] / plan["VAP"][str(d)] for d in range(1, proposed_summary["num_districts"] + 1)])
                    for d in range(1, proposed_summary["num_districts"] + 1):
                        df[plan["name"]].loc[f"{first}-{str(d)}"] = sorted_group[d-1]
                else:
                    df[plan["name"]].loc[metric] = plan[first][second]
                    if factory:
                        scores = factory.aggregate_score(first)
                        df["Ensemble-Mean"].loc[metric] = np.mean(scores[second])
                        df["Ensemble-Median"].loc[metric] = np.median(scores[second])
    return df

def summarize_plans(proposed_plans_file):
    output_dir = "/".join(proposed_plans_file.split("/")[:-1])
    with open(proposed_plans_file, "rb") as fp:
        proposed_list = list(fp)
    fp.close()
    
    df = initialize_df(proposed_list)
    df = fill_df(proposed_list, df)
    df.to_csv(f"{output_dir}/{map}_proposed_plans_summary.csv")

print(f"Summarizing {proposed_plans_file}")
summarize_plans(proposed_plans_file)