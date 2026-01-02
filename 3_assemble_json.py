import pandas as pd
import json
import ast

# --- Configuration ---
NODES_FILE = "graph_nodes_final.csv"
EDGES_FILE = "graph_edges_normalized.csv"
OUTPUT_FILE = "cytoscape_data.json"

# --- Main Script ---
print(f"Starting JSON Assembly from {NODES_FILE} and {EDGES_FILE}...")

try:
    # 1. Load Data
    df_nodes = pd.read_csv(NODES_FILE)
    df_edges = pd.read_csv(EDGES_FILE)
    
    # Convert 'processed_tokens' back to a display string for the JSON
    df_nodes['processed_tokens'] = df_nodes['processed_tokens'].apply(ast.literal_eval).apply(lambda x: ', '.join(x) if isinstance(x, list) else '')

    # 2. Prepare Nodes
    nodes = []
    for _, row in df_nodes.iterrows():
        # Create a simple label for graph view (e.g., GEN 1:1)
        label = f"{row['book_name'][:3]}.{row['chapter']}.{row['verse_number']}"
        
        nodes.append({
            'data': {
                'id': row['id'],
                'label': label,
                'book': row['book_name'],
                'chapter': row['chapter'],
                'verse': row['verse_number'],
                'text_clean': row['text_clean'],
                'text_strongs': row['text_strongs'],
                'processed_tokens': row['processed_tokens'] # List of keywords for search
            },
            'group': 'nodes'
        })

    # 3. Prepare Edges
    edges = []
    for _, row in df_edges.iterrows():
        edges.append({
            'data': {
                'id': f"{row['source']}_{row['target']}", # Unique ID for the edge
                'source': row['source'],
                'target': row['target'],
                'weight': row['weight'],
                'type': row['type']
            },
            'group': 'edges'
        })

    # 4. Combine and Save
    cytoscape_data = {
        'elements': {
            'nodes': nodes,
            'edges': edges
        }
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(cytoscape_data, f, indent=2) 
    
    print(f"Successfully created the Cytoscape JSON file: {OUTPUT_FILE}")
    print(f"JSON contains {len(nodes)} nodes and {len(edges)} edges.")

except Exception as e:
    print(f"Error in JSON assembly: {e}")