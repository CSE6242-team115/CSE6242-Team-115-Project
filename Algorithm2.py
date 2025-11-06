import os
import sys
import math
import json
import pandas as pd
from collections import defaultdict

# ---------- JSON safety helpers ----------
def _json_safe_scalar(x):
    # Convert pandas/NumPy NaN/Inf to proper JSON types
    if x is None:
        return None
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    return x

def json_sanitize(obj):
    """Recursively convert any NaN/Inf to None so json.dump with allow_nan=False succeeds."""
    if isinstance(obj, dict):
        return {k: json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_sanitize(v) for v in obj]
    return _json_safe_scalar(obj)

# ---------- Load + prep data ----------
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_source = os.path.join(script_dir, "MetObjects-Cleaned_Columns-csv_v2.csv")

df = pd.read_csv(csv_source, low_memory=False)
df.columns = df.columns.str.replace(" ", "_")
df = df.sample(n=5000, random_state=42)   # keep indices as-is (used in JSON)

# (Optional) also save the sampled CSV (with index) so your HTML can load it
sample_csv_path = os.path.join(script_dir, "MetObjects-Cleaned-5000sample.csv")
df.to_csv(sample_csv_path, index=True, encoding="utf-8")

# Columns used in indexing / scoring
cols = [
    "Artist Display Name", "Object Date", "Medium", "Culture", "Object Number", "Department",
    "Object Name", "Title", "Period", "Dynasty", "Reign", "Portfolio", "Artist Nationality",
    "Object Begin Date", "Object End Date", "City", "State", "County", "Country", "Region",
    "Subregion", "Locale", "Classification", "Tags"
]
cols = [c.replace(" ", "_") for c in cols]
df = df[cols]

# Pipe-split columns
piped_cols = [
    "Artist Display Name", "Artist Nationality", "City", "State",
    "County", "Country", "Region", "Subregion", "Locale", "Tags"
]
piped_cols = [c.replace(" ", "_") for c in piped_cols]

for col in piped_cols:
    df[col] = (
        df[col].fillna('')
              .apply(lambda x: [v.strip() for v in str(x).split('|') if v.strip()])
    )

# Build nested dictionaries: {column -> {value -> set(indexes)}}
attr_cols = [
    "Artist Display Name", "Object Date", "Medium", "Culture", "Department",
    "Object Name", "Period", "Dynasty", "Reign", "Portfolio", "Artist Nationality",
    "Object Begin Date", "Object End Date", "City", "State", "County", "Country", "Region",
    "Subregion", "Locale", "Classification", "Tags"
]
attr_cols = [c.replace(" ", "_") for c in attr_cols]

attr_dict = {}
for col in attr_cols:
    attr_dict[col] = {}
    if col in piped_cols:
        grouped = df.explode(col).groupby(col).groups
    else:
        grouped = df.groupby(col).groups
    for key in grouped:
        attr_dict[col][key] = grouped[key]

# ---------- Column weights ----------
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
TOP_K = 20

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

# ---------- Compute weighted similarity scores for all rows ----------
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
            # ensure plain set
            neighbors = set(neighbors) if not isinstance(neighbors, set) else neighbors
            if not neighbors:
                return
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

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:TOP_K]
    all_neighbor_scores[idx] = ranked

# ---------- Build JSON { object_number -> {..., similar_neighbors_scored: [{index, score}, ...]} } ----------
output_dict = {}

for idx, row in df.iterrows():
    ranked = all_neighbor_scores.get(idx, [])
    object_num = str(row.Object_Number).strip()
    if not object_num:
        continue

    output_dict[object_num] = {
        "index": int(idx),
        "title": row.Title,
        "artist": row.Artist_Display_Name,  # list from piped cols or empty list
        "medium": row.Medium,
        "culture": row.Culture,
        "object_date": row.Object_Date,
        "similar_neighbors_scored": [
            {"index": int(n), "score": float(s)} for (n, s) in ranked
        ],
    }

# Write strict JSON
json_path = os.path.join(script_dir, "full_artworks2.json")
clean_output = json_sanitize(output_dict)
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(clean_output, f, ensure_ascii=False, indent=2, allow_nan=False)

print(f"Wrote recommendations JSON -> {json_path}")
print(f"Wrote sampled CSV         -> {sample_csv_path}")

# ---------- Ask for Object Number and export top-20 CSV ----------
# Accept as CLI arg or interactive input
if len(sys.argv) > 1:
    obj_key = " ".join(sys.argv[1:]).strip()
else:
    obj_key = input("\nEnter Object Number exactly as in JSON (e.g., 2011.604.1.4597): ").strip()

if not obj_key:
    print("No object number provided; exiting.")
    sys.exit(0)

if obj_key not in clean_output:
    # Try trimmed match fallback (in case of accidental whitespace)
    trimmed_map = {k.strip(): k for k in clean_output.keys()}
    if obj_key.strip() in trimmed_map:
        obj_key = trimmed_map[obj_key.strip()]
    else:
        print(f'Object Number "{obj_key}" not found in {os.path.basename(json_path)}')
        sys.exit(1)

rec = clean_output[obj_key]
main_idx = int(rec["index"])

# Build neighbor list (indices + score)
neighbors = rec.get("similar_neighbors_scored", []) or []
neighbor_indices = []
score_map = {}
for item in neighbors:
    try:
        nidx = int(item["index"])
        neighbor_indices.append(nidx)
        score_map[nidx] = float(item.get("score", 0.0))
    except Exception:
        continue

# Filter to indices that actually exist in df
existing_neighbors = [i for i in neighbor_indices if i in df.index]

# Assemble output frame: main first, then neighbors
rows_order = [main_idx] + existing_neighbors
out_df = df.loc[rows_order].copy()

# Add helpful columns
out_df.insert(0, "source_role", ["main"] + ["neighbor"] * len(existing_neighbors))
out_df.insert(1, "similarity_score",
              [None] + [score_map.get(i) for i in existing_neighbors])

# If you prefer pipe-joining list columns for readability in CSV:
for col in piped_cols:
    out_df[col] = out_df[col].apply(lambda x: "|".join(x) if isinstance(x, list) else x)

# Write the CSV next to the script
out_csv = os.path.join(script_dir, f"recommendations.csv")
out_df.to_csv(out_csv, index=True, encoding="utf-8")

print(f'Saved top-20 CSV for "{obj_key}" -> {out_csv}')