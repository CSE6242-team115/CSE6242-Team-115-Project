import os
import pandas as pd
import json

# Load Data
script_dir = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(script_dir, "MetObjects.csv"), low_memory = False)
df.columns = df.columns.str.replace(" ", "_")
df = df.sample(n=5000, random_state=42)

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

# find indices of similar pieces for each piece
index_list = []
all_indices = dict()
for row in df.itertuples():
    idx= row.Index
    single_index = set()
    for col in attr_cols:
        val = getattr(row, col)
        if col in piped_cols:
            if len(val) == 0:
                continue
            for v in val:
                single_index.update(attr_dict[col][v])
        else:
            if pd.notna(val):
                single_index.update(attr_dict[col][val])
    single_index.discard(idx)
    all_indices[idx] = list(single_index)

output_data = []
for idx, row in df.iterrows():
    output_data.append({
        "index": idx,
        "title": row.Title,
        "artist": row.Artist_Display_Name,
        "medium": row.Medium,
        "culture": row.Culture,
        "object_date": row.Object_Date,
        "similar_indices": all_indices[idx]
    })

# Save to JSON file for web integration
output_path = os.path.join(script_dir, "full_artworks.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)