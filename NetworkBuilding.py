import os
import pandas as pd
from collections import defaultdict
import networkx as nx
from itertools import combinations

#Load data
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "MetObjects.csv")
df = pd.read_csv(csv_path, low_memory=False)

#Filter subset of data for testing, 5000 pieces
df_sample = df.sample(n=5000, random_state=42)

#Data Cleaning to separate piped text
piped_cols = [
    'Artist Display Name', 'Artist Nationality', 'City', 'State',
    'County', 'Country', 'Region', 'Subregion', 'Locale', 'Tags'
]

for col in piped_cols:
    if col in df_sample.columns:
        df_sample[col] = (
            df_sample[col]
            .fillna('')
            .apply(lambda x: [v.strip() for v in str(x).split('|') if v.strip()])
        )
    
#Function to build network, Needed to update this to handle lists from pipe data cleaning
#max_apps = max appearances of a single connector/value. Skips over potential connectors to keep the size of graph feasible. 
def buildNetwork(col_name: str, df, max_apps=5000):
    #Initialize network
    network = nx.MultiGraph()
    value_to_objects = defaultdict(list)

    col_idx = df.columns.get_loc(col_name)
    obj_idx = df.columns.get_loc("Object Number")
    
    for row in df.itertuples(index=False):
        obj = row[obj_idx]
        values = row[col_idx]
        if not isinstance(values, list):
            values = [str(values).strip()] if str(values).strip() else []
        for v in values:
            value_to_objects[v].append(obj)
    
    # Build edges
    for objs in value_to_objects.values():
        if len(objs) > 1 and len(objs) <= max_apps:
            network.add_edges_from(
                ((a, b, {'layer': col_name}) for a, b in combinations(objs, 2))
            )
        elif len(objs) > max_apps:
            continue
    
    return network

# build networks for each column/category

colNets = {}
cols = ["Artist Display Name", "Object Date", "Medium", "Culture","Object Number","Department",
        "Object Name", "Title", "Period", "Dynasty", "Reign", "Portfolio", "Artist Nationality",
        "Object Begin Date", "Object End Date", "City", "State", "County", "Country", "Region",
        "Subregion", "Locale", "Classification", "Tags"]

for col in cols:
    #remove space in category
    col_no_space = col.replace(" ", "")

    #build network for all categories in the following format: 
        # ArtistNet = buildNetwork("Artist Display Name", df_sample)
    colNets[f"{col_no_space}Net"] = buildNetwork(col, df_sample)


#mlNetwork = nx.MultiGraph()
mlNetwork = nx.compose_all(list(colNets.values()))

#add node attributes for all selected columns
for _, row in df_sample.iterrows():
    node_id = row["Object Number"]
    attrs = {col.replace(" ", "_").lower(): row[col] for col in cols if col in df_sample.columns}
    mlNetwork.add_node(node_id, **attrs)

node, degree = max(mlNetwork.degree(), key=lambda x: x[1])

#tester code
node_id = node
print(f"Node: {node_id}")
print("Attributes:", mlNetwork.nodes[node_id])
print("Degree:", mlNetwork.degree(node_id))
print("Neighbors:", list(mlNetwork.neighbors(node_id))[:10])
edges = mlNetwork.edges(node_id, data=True)
#for u, v, data in edges:
#    print(f"{u} -- {v}, layer: {data.get('layer')}")
