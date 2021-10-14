# plan-evaluation
A set of tools and resources for evaluating and visualizing proposed districting plans.

## Scripts for Ensemble Generation and Scoring Plans

* `run_ensemble.py`: script used to generate a chain and save it's run.  Arguments: state, map_type, num_steps, --county_aware, and --quite can be passed via the command line.
* `collect_scores.py`: script used to score a pre-generated chain and save the results.  Arguments: state, map_type, num_steps, --county_aware, and --verbosity can be passed via the command line.

The `scripts/` directory contains bash scripts for running this code on the cluster. The `*.slurm` scripts are used with the `sbatch` command to create a new job on the HPC with the right parameters, navigate to the right directory and call the python scripts.  The `*.sh` scripts are used to kick-off multiple cluster jobs for a state across map_types and proposal method types.

Raw chains are stored compressed according to the format in the [pcompress repo](https://github.com/InnovativeInventor/pcompress).

Ensemble statistics are stored as a compressed jsonl file with the following format:
The first line is a summary object describing the ensemble: # districts, 
district ids, the population balance, the proposal method, which metrics are tracked (their id, their prettified name string, and metric type $\in$ {`plan_wide`, `district_level`, `election_level`}), the POV party, and details about the elections used for the partisanship metrics.

```json
{
    "type": "ensemble_summary", 
    "num_districts": 13, 
    "district_ids": [1, 2, 3, ...], 
    "epsilon": 0.01, 
    "chain_type": "neutral", 
    "pop_col": "TOTPOP", 
    "metrics": [
                    {"id": "TOTPOP", "name": "Total Population", "type": "district_level"},
                    {"id": "num_cut_edges", "name": "# Cut Edges", "type": "plan_wide"},
                    {"id": "seats", "name": "# Seats Won", "type": "election_level"},
                    ...
                ], 
    "pov_party": "Democratic", 
    "elections": [{"name": "GOV18", "candidates": [{"name": "Democratic", "key": "GOV18D"},
                                                   {"name": "Republican", "key": "GOV18R"}]},
                   ...], 
    "party_statewide_share": {"GOV18": 0.5493898776942814, ...}
}
```

Each sequential line describes a plan.  It has a type $\in$ {`"ensemble_plan"`, `citizen_plan`, `proposed_plan`}.  In addition it has attributes for each metric described above, where the attribute key matches the metric id, and the attribute body is the corresponding metric data.  For type `'a`: `plan_wide` metrics have type `'a`, `district_level` metrics have type Map<`district_id`, `'a`>, and `election_level` metrics have type Map<`election_name`, `'a`>.

```json
{
    "type": "ensemble_plan", 
    "TOTPOP": {"1": 774357, "2": 775422, "3": 777890, ...},
    "num_cut_edges": 874,
    "seats": {"GOV18": 8, ...},
    ...
}
```

## Adding a new state:

Steps for adding a new state:
* Add its name the list of supported states in `configuration.py`
* Create a dual graph and add it to the `dual_graphs` directory.
* In the `state_specifications` sub-directory add `${State Name}.json`, defining properties about the state, where it's dual graph lives, what columns are in that dual graph and which metrics to track.
* Create a directory for the state to store intermediary outputs.

Once those steps are complete you should be able to run the previous scripts passing the new state as a command line argument.

## Installation
### Use Cases
When installing, it's important to determine your use case: if you want to use
`plan-evaluation` as a _package_ (i.e. for independently writing scripts to
create plots, dissolve geometries, etc.) instead of using it as a _data repository_
(for storing plan evaluation materials).

## Instructions
If you want to use this code _as an `import`-able package_, the recommended way
to install is by running
```
$ pip install git+https://github.com/mggg/plan-evaluation
```
in your favorite CLI. If you want to use this as a _data repository only_, you
can download it like
```
$ git clone https://github.com/mggg/plan-evaluation.git
```
If you want the best of both worlds – the use of the code as a package and a
data repository – install using
```
$ git clone https://github.com/mggg/plan-evaluation.git
```
Then, navigate into the repository and run
```
$ python setup.py develop
```
This allows you to have an easily-accessible local copy of the code, make
changes which are reflected system-wide, and add data to the repository as you see fit.

## Usage
### Mapping
### `mapping.drawplan`
Before creating the plan map, we need geometric data for each district.
Generally, this geometric data is a GeoDataFrame with one row per district;
if we wish to overlay additional shapes (e.g counties) on the districting plan,
we should have geometric data for those as well.

```python
from plan_evaluation.mapping import drawplan
import geopandas as gpd
import matplotlib.pyplot as plt

# Read in geometric data.
districts = gpd.read_file("<path>/<to>/<districts>")
counties = gpd.read_file("<path>/<to>/<counties>")

# Specify the column on the GeoDataFrame which contains the districts' names.
name = "DISTRICTN"

# Plot, overlaying county shapes on top of our district map.
ax = drawplan(districts, name, overlay=counties)
```

Because `drawplan` returns a `matplotlib.Axes` object, it can be manipulated as
typical matplotlib plots are. Additionally, `drawplan` has a `numbers` keyword
argument which, if `True`, plots the name of each district at its centroid:

```python
# Plot, overlaying county shapes and plotting district numbers.
ax = drawplan(districts, name, overlay=counties, numbers=True)
```

Internally, `drawplan` attempts to convert district names to integers and sort
them to get proper color orderings, but the name of the district (as specified
by the `assignment` parameter) is plotted when `numbers` is `True`.
