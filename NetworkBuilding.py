import os
import pandas as pd
from collections import defaultdict
import networkx as nx
from itertools import combinations

#Load data
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "MetObjects.csv")
df = pd.read_csv(csv_path, low_memory=False)

#Filter rows where "Artist Display Name" is not empty or NaN
#df_filtered = df[df["Artist Display Name"].notna() & (df["Artist Display Name"] != "")]

#Filter subset of data for testing, 5000 pieces
df_sample = df.sample(n=5000, random_state=42)
    
#Function to build network
def buildNetwork(col_name: str, df):
    #Initialize network
    network = nx.MultiGraph()

    for _, group in df.groupby(col_name):
        artworks = list(group['Object Number'])
        if len(artworks) > 1:
            for a, b in combinations(artworks, 2):
                network.add_edge(a, b, layer=col_name)
    return network

ArtistNet = buildNetwork("Artist Display Name", df_sample)
DateNet = buildNetwork("Object Date", df_sample)
MediumNet = buildNetwork("Medium",df_sample)
CultureNet = buildNetwork("Culture",df_sample)


mlNetwork = nx.MultiGraph()
mlNetwork = nx.compose_all([ArtistNet, DateNet, MediumNet, CultureNet])

for _, row in df_sample.iterrows():
    mlNetwork.add_node(row['Object Number'],
                       title=row['Title'],
                       artist=row['Artist Display Name'],
                       date=row['Object Date'],
                       medium=row['Medium'],
                       culture=row['Culture'])

node, degree = max(mlNetwork.degree(), key=lambda x: x[1])

node_id = "C.I.46.28.2"
print(f"Node: {node_id}")
print("Attributes:", mlNetwork.nodes[node_id])
print("Degree:", mlNetwork.degree(node_id))
print("Neighbors:", list(mlNetwork.neighbors(node_id))[:10])
edges = mlNetwork.edges(node_id, data=True)
#for u, v, data in edges:
#    print(f"{u} -- {v}, layer: {data.get('layer')}")
