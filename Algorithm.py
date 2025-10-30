import os
import pandas as pd

# Load Data
script_dir = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(script_dir, "MetObjects.csv"), low_memory = False)
df.columns = df.columns.str.replace(" ", "_")

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
all_indices = set()
for row in df.itertuples():
    print(row)
    for col in attr_cols:
        val = getattr(row, col)
        if col in piped_cols:
            if len(val) == 0:
                continue
            for v in val:
                index_list.append(attr_dict[col][v])
                all_indices.update(attr_dict[col][v])
        else:
            if pd.isna(val):
                continue
            index_list.append(attr_dict[col][val])
            all_indices.update(attr_dict[col][val])
    break
print(index_list)
print()
print(all_indices)