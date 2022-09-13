import os
import pandas as pd
import numpy as np
import plotly.express as px

# Directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Blindly accepting data without any verification for speed purposes
df = pd.read_excel(
    os.path.join(BASE_DIR, "MLS_Soccer_Analytics_Takehome.xlsx"),
    sheet_name="soccer18_results",
)

# parity -->
## Number of champions in past 10 years - not available in dataset, small sample of years likely isn't representative
## Points per season & points per game (should be same since each team played same number of games amd cross season variability in number of games doesn't matter)

# Summarize each division, season, team --> calculating ending points
## Generate points in game and attribute to each home and away team --> assume each league uses same points scores (3,1,0)
def calc_points(row):
    if row["FullTimeHomeGoals"] > row["FullTimeAwayGoals"]:
        home_points = 3
        away_points = 0
    elif row["FullTimeHomeGoals"] == row["FullTimeAwayGoals"]:
        home_points = 1
        away_points = 1
    else:
        home_points = 0
        away_points = 3

    # Should do try/except here but no time
    row["home_team_points"] = home_points
    row["away_team_points"] = away_points

    return row


df = df.apply(calc_points, axis=1, result_type="expand")

## Need to convert 2 col format (home/away) to single format
### First idea and running with for sake of time
### Take one copy of the dataset and sum home points and use home team id as team_id
cols_to_keep = ["Division", "Season", "home_team_id", "home_team_points"]
df_home = df[cols_to_keep].copy()
df_home.rename(
    columns={"home_team_id": "team_id", "home_team_points": "team_points"}, inplace=True
)

cols_to_keep = ["Division", "Season", "away_team_id", "away_team_points"]
df_away = df[cols_to_keep].copy()
df_away.rename(
    columns={"away_team_id": "team_id", "away_team_points": "team_points"}, inplace=True
)

df2 = df_home.append(df_away)
df2.reset_index(drop=True, inplace=True)

## Actually summarize now
df_sum = df2.groupby(by=["Division", "Season", "team_id"], as_index=False)[
    "team_points"
].sum()
### Ignoring ties in sorting - sake of time and I don't think it affects GINI
df_sum.sort_values(
    by=["Division", "Season", "team_points", "team_id"],
    ascending=[True, True, False, True],
    inplace=True,
)
df_sum.reset_index(drop=True, inplace=True)


# Calculate Gini Coefficient per year
## Gini coefficient is a 1 per season per league value (i.e. 20 teams points spread gets summarized to a single value)
## So we should end up with 5 seasons * 5 leagues = 25 values

### Literally copying from here to save time: https://github.com/oliviaguest/gini/blob/master/gini.py
def gini(array):
    """Calculate the Gini coefficient of a numpy array."""
    # based on bottom eq:
    # http://www.statsdirect.com/help/generatedimages/equations/equation154.svg
    # from:
    # http://www.statsdirect.com/help/default.htm#nonparametric_methods/gini.htm
    # All values are treated equally, arrays must be 1d:
    array = array.flatten()
    if np.amin(array) < 0:
        # Values cannot be negative:
        array -= np.amin(array)
    # Values cannot be 0:
    array += 0.0000001
    # Values must be sorted:
    array = np.sort(array)
    # Index per array element:
    index = np.arange(1, array.shape[0] + 1)
    # Number of array elements:
    n = array.shape[0]
    # Gini coefficient:
    return (np.sum((2 * index - n - 1) * array)) / (n * np.sum(array))


## So we need to separate each season & league, and convert the points to an numpy array
## Probably a better way but speed wins right now
seasons = df_sum["Season"].unique()
divisions = df_sum["Division"].unique()

# Initiate results df --> each season/league is a dictionary, convert list of dictionaries to DF
df_gini = pd.DataFrame(columns=["Division", "Season", "Gini"])

# Fix int/float issue in gini
df_sum["team_points"] = df_sum["team_points"].astype("float64")

for division in divisions:
    for season in seasons:
        df_local = df_sum[
            (df_sum["Season"] == season) & (df_sum["Division"] == division)
        ].copy()
        a = df_local["team_points"].to_numpy()
        b = gini(a)
        df_gini.loc[len(df_gini.index)] = [division, season, b]

### Should stop here and match to other article's results, but no time

# Now make this pretty, no time for super fancies here
fig = px.line(df_gini, x="Season", y="Gini", color="Division")
fig.show()
fig.write_image(os.path.join(BASE_DIR, "gini.png"))
