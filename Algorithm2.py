import os
import pandas as pd
from collections import defaultdict
import json

# Load Data
script_dir = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(script_dir, "MetObjects-Cleaned_Columns-csv_v2.csv"), low_memory = False)
df.columns = df.columns.str.replace(" ", "_")
df = df.sample(n=5000, random_state=42)

#save df as csv file
cleaned_csv_path = os.path.join(script_dir, "MetObjects-Cleaned-5000sample.csv")
df.to_csv(cleaned_csv_path, index=True, encoding="utf-8")

# Filter relevant columns
cols = ["Artist Display Name", "Object Date", "Medium", "Culture", "Object Number", "Department",
        "Object Name", "Title", "Period", "Dynasty", "Reign", "Portfolio", "Artist Nationality",
        "Object Begin Date", "Object End Date", "City", "State", "County", "Country", "Region",
        "Subregion", "Locale", "Classification", "Tags"]
cols = [col.replace(" ", "_") for col in cols]
df = df[cols]

# Split piped strings into list of strings
piped_cols = [
    'Artist Display Name', 'Artist Nationality', 'City', 'State',
    'County', 'Country', 'Region', 'Subregion', 'Locale', 'Tags'
]
piped_cols = [col.replace(" ", "_") for col in piped_cols]
for col in piped_cols:
    df[col] = (
        df[col].fillna('').apply(lambda x: [v.strip() for v in str(x).split('|') if v.strip()])
    )

# Nested Dict
attr_cols = ["Artist Display Name", "Object Date", "Medium", "Culture", "Department",
        "Object Name", "Period", "Dynasty", "Reign", "Portfolio", "Artist Nationality",
        "Object Begin Date", "Object End Date", "City", "State", "County", "Country", "Region",
        "Subregion", "Locale", "Classification", "Tags"]
attr_cols = [col.replace(" ", "_") for col in attr_cols]

attr_dict = dict()
for col in attr_cols:
    attr_dict[col] = dict()
    if col in piped_cols:
        grouped = df.explode(col).groupby(col).groups
    else:
        grouped = df.groupby(col).groups
    for key in grouped:
        attr_dict[col][key] = grouped[key]

# 1) Column weights (matching your DataFrame's underscore names)
COL_WEIGHTS = {
    "Title": 20,
    "Department": 18,
    "Object_Name": 17,
    "Medium": 17,
    "Artist_Display_Name": 15,
    "Culture": 14,
    "Object_Date": 13,
    "Artist_Nationality": 12,
    "Object_Begin_Date": 12,
    "Object_End_Date": 12,
    "Portfolio": 11,
    "Locale": 8,
    "Gallery_Number": 7,
    "City": 7,
    "State": 7,
    "County": 7,
    "Period": 6,
    "Dynasty": 6,
    "Reign": 6,
    "Region": 6,
    "Subregion": 6,
    "Country": 5,
}
DEFAULT_COL_WEIGHT = 1.0
TOP_K = 20  # number of recommendations to keep

def _is_blank(v):
    if v is None:
        return True
    if isinstance(v, float) and pd.isna(v):
        return True
    if isinstance(v, str) and v.strip() == "":
        return True
    if isinstance(v, (list, tuple)) and len(v) == 0:
        return True
    return False

# 2) Compute weighted similarity scores
all_neighbor_scores = {}

for row in df.itertuples():
    idx = row.Index
    scores = defaultdict(float)  # neighbor_idx -> score

    for col in attr_cols:
        col_weight = COL_WEIGHTS.get(col, DEFAULT_COL_WEIGHT)
        val = getattr(row, col)

        def add_value(v):
            if _is_blank(v):
                return
            neighbors = attr_dict[col].get(v, set())
            # Convert to a normal Python set in case it's a pandas Index
            if isinstance(neighbors, pd.Index):
                neighbors = set(neighbors)
            elif not isinstance(neighbors, set):
                neighbors = set(neighbors)
            if len(neighbors) == 0:
                return
            # each match adds the column weight
            for j in neighbors:
                if j != idx:
                    scores[j] += col_weight

        if col in piped_cols:
            if not _is_blank(val):
                for v in val:
                    add_value(v)
        else:
            if not _is_blank(val):
                add_value(val)

    # 3) Rank neighbors by total weighted score
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:TOP_K]
    all_neighbor_scores[idx] = ranked

# 4) Build output records (top-20 indices + scores)
output_dict = {}

for idx, row in df.iterrows():
    ranked = all_neighbor_scores.get(idx, [])
    object_num = str(row.Object_Number).strip()

    if not object_num:
        continue  # skip rows with no object number

    output_dict[object_num] = {
        "index": int(idx),
        "title": row.Title,
        "artist": row.Artist_Display_Name,
        "medium": row.Medium,
        "culture": row.Culture,
        "object_date": row.Object_Date,
        "similar_neighbors_scored": [
            {"index": int(n), "score": float(s)} for (n, s) in ranked
        ],
    }

# Save to JSON file
output_path = os.path.join(script_dir, "full_artworks2.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_dict, f, ensure_ascii=False, indent=2)

