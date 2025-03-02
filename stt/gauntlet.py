import requests
from pprint import pprint
import pandas as pd
import itertools

SKILL_MAP = {
    "command_skill": "CMD",
    "diplomacy_skill": "DIP",
    "engineering_skill": "ENG",
    "medicine_skill": "MED",
    "science_skill": "SCI",
    "security_skill": "SEC"
}

def get_dc_data(url="https://beta.datacore.app/structured/crew.json"):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to download data: {e}")

def get_gauntlet_data(data):
    records = []
    for item in data:
        record = {"name": item["name"]}
        base_skills = item.get("base_skills", {})
        for skill, abbrev in SKILL_MAP.items():
            if skill in base_skills:
                skill_data = base_skills[skill]
                record[f"{abbrev}_range_max"] = skill_data.get("range_max")
                record[f"{abbrev}_range_min"] = skill_data.get("range_min")
                record[f"{abbrev}_core"] = skill_data.get("core")
                record[f"{abbrev}_roll"] = (skill_data.get("range_max") + skill_data.get("range_min")) / 2
        records.append(record)
    df = pd.DataFrame(records)
    return df

def add_gauntlet_pairs(df):
    pairs = list(itertools.combinations(SKILL_MAP.values(), 2))
    for skill1, skill2 in pairs:
        col_name = f"{skill1}_{skill2}_roll"
        df[col_name] = df[f"{skill1}_roll"].fillna(0) + df[f"{skill2}_roll"].fillna(0)
    return df

def add_gauntlet_ranks(df):
    pairs = list(itertools.combinations(SKILL_MAP.values(), 2))
    for skill1, skill2 in pairs:
        col_name = f"{skill1}_{skill2}_roll"
        rank_col_name = f"{col_name}_rank"
        df[rank_col_name] = df[col_name].rank(ascending=False, method='min').astype(int)
    return df

def normalize_rolls(df):
    pairs = list(itertools.combinations(SKILL_MAP.values(), 2))
    for skill1, skill2 in pairs:
        col_name = f"{skill1}_{skill2}_roll"
        norm_col_name = f"{col_name}_norm"
        max_value = df[col_name].max()
        df[norm_col_name] = (df[col_name] / max_value) * 100
    return df

def add_gauntlet_score(df, pair_calc=3):
    norm_cols = [f"{skill1}_{skill2}_roll_norm" for skill1, skill2 in itertools.combinations(SKILL_MAP.values(), 2)]
    df['gauntlet_score'] = df[norm_cols].apply(lambda row: row.nlargest(pair_calc).mean(), axis=1)
    max_score = df['gauntlet_score'].max()
    df['gauntlet_score_norm'] = (df['gauntlet_score'] / max_score) * 100
    df['gauntlet_rank'] = df['gauntlet_score'].rank(ascending=False, method='min').astype(int)
    return df

def print_top_crew(df, num_rows=50, filename=None):
    df_sorted = df.sort_values(by='gauntlet_rank')
    columns_to_display = ['name', 'gauntlet_score_norm', 'gauntlet_rank'] + [f"{skill1}_{skill2}_roll_rank" for skill1, skill2 in itertools.combinations(SKILL_MAP.values(), 2)]
    top_crew = df_sorted[columns_to_display].head(num_rows)
    if filename:
        top_crew.to_csv(filename, index=False)
    else:
        print(top_crew)

data = get_dc_data()
df = get_gauntlet_data(data)
df = add_gauntlet_pairs(df)
df = add_gauntlet_ranks(df)
df = normalize_rolls(df)
df = add_gauntlet_score(df)
print_top_crew(df, 50, "top_crew.csv")