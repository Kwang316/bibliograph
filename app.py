import streamlit as st
import json
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="KJV Interactive Cross-Reference Builder",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Dark theme styles */
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }
    
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'graph_data' not in st.session_state:
    st.session_state.graph_data = None
if 'selected_verse' not in st.session_state:
    st.session_state.selected_verse = None
if 'graph_elements' not in st.session_state:
    st.session_state.graph_elements = []

# Load graph data
@st.cache_data
def load_graph_data():
    """Load the cytoscape_data.json file"""
    try:
        # Try multiple possible paths
        possible_paths = [
            Path('cytoscape_data.json'),  # Current directory
            Path('../Christology/cytoscape_data.json'),  # Relative to current
            Path('C:/Users/hongt/Projects/Christology/cytoscape_data.json'),  # Absolute path
            Path.home() / 'Projects' / 'Christology' / 'cytoscape_data.json',  # User home relative
        ]
        
        json_path = None
        for path in possible_paths:
            if path.exists():
                json_path = path
                break
        
        if json_path is None:
            st.error("⚠️ cytoscape_data.json not found. Please ensure the file exists in one of these locations:")
            for path in possible_paths:
                st.text(f"  - {path}")
            return None
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        st.success(f"✅ Loaded data from: {json_path}")
        return data
    except Exception as e:
        st.error(f"Error loading graph data: {str(e)}")
        return None

# Load data
if st.session_state.graph_data is None:
    st.session_state.graph_data = load_graph_data()

if st.session_state.graph_data is None:
    st.stop()

# Process data for easier access
elements = st.session_state.graph_data.get('elements', {})
nodes = elements.get('nodes', [])
edges = elements.get('edges', [])

# Organize verses by book and chapter
verses_by_book_chapter = {}
for node in nodes:
    book = node['data'].get('book', '')
    chapter = node['data'].get('chapter', '')
    if book and chapter:
        if book not in verses_by_book_chapter:
            verses_by_book_chapter[book] = {}
        if chapter not in verses_by_book_chapter[book]:
            verses_by_book_chapter[book][chapter] = []
        verses_by_book_chapter[book][chapter].append(node['data'])

# Helper function to safely convert chapter to int for sorting
def chapter_sort_key(x):
    """Convert chapter to int for sorting, handling both int and string types"""
    if isinstance(x, int):
        return x
    if isinstance(x, str) and x.isdigit():
        return int(x)
    return 999

# Sort books and chapters
sorted_books = sorted(verses_by_book_chapter.keys())
if sorted_books:
    # Default to first book
    default_book = sorted_books[0]
    sorted_chapters = sorted(verses_by_book_chapter[default_book].keys(), key=chapter_sort_key)
else:
    default_book = None
    sorted_chapters = []

# Main layout
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📖 Bible Text")
    
    # Book and chapter selection
    col_book, col_chapter, col_go = st.columns([2, 1, 1])
    with col_book:
        selected_book = st.selectbox("Book", sorted_books, key="book_select", label_visibility="collapsed")
    
    if selected_book:
        chapters = sorted(verses_by_book_chapter[selected_book].keys(), key=chapter_sort_key)
        with col_chapter:
            selected_chapter = st.selectbox("Chapter", chapters, key="chapter_select", label_visibility="collapsed")
        with col_go:
            if st.button("Go", use_container_width=True):
                st.session_state.selected_verse = None
                st.session_state.graph_elements = []
                st.rerun()
    
    # Display verses
    if selected_book and selected_chapter:
        # Helper function to safely get verse number for sorting
        def verse_sort_key(x):
            verse_val = x.get('verse', 0)
            if isinstance(verse_val, int):
                return verse_val
            try:
                return int(verse_val)
            except (ValueError, TypeError):
                return 0
        
        verses = sorted(verses_by_book_chapter[selected_book][selected_chapter], key=verse_sort_key)
        
        st.markdown(f"### {selected_book} Chapter {selected_chapter}")
        
        # Display verses with clickable functionality
        for verse_data in verses:
            verse_id = verse_data.get('id', '')
            verse_num = verse_data.get('verse', '')
            verse_text = verse_data.get('text', '')
            
            # Check if this verse is currently selected
            is_selected = st.session_state.selected_verse == verse_id
            
            # Create a container for each verse with custom styling
            verse_style = """
            <style>
            .verse-container {
                padding: 8px;
                margin: 5px 0;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            .verse-container:hover {
                background-color: #333333;
            }
            .verse-container.selected {
                background-color: #FF0000;
                color: #FFFFFF;
                font-weight: 500;
            }
            </style>
            """
            
            # Use columns to create clickable verse display
            col_vnum, col_vtext = st.columns([0.1, 0.9])
            
            with col_vnum:
                st.markdown(f"**{verse_num}**")
            
            with col_vtext:
                if st.button(
                    verse_text,
                    key=f"verse_{verse_id}",
                    use_container_width=True,
                    help=f"Click to add {verse_id} to graph"
                ):
                    st.session_state.selected_verse = verse_id
                    # Add verse to graph if not already there
                    if verse_id not in [e.get('data', {}).get('id', '') for e in st.session_state.graph_elements if 'data' in e]:
                        # Find node data
                        node_data = next((n for n in nodes if n['data'].get('id') == verse_id), None)
                        if node_data:
                            st.session_state.graph_elements.append(node_data)
                    st.rerun()

with col2:
    st.markdown("### 🔗 TSK Cross-References")
    
    if st.button("Clear Graph", use_container_width=True):
        st.session_state.graph_elements = []
        st.session_state.selected_verse = None
        st.rerun()
    
    # Get current verse data
    current_verse_id = st.session_state.selected_verse
    if current_verse_id:
        current_node = next((n for n in nodes if n['data'].get('id') == current_verse_id), None)
        if current_node:
            node_data = current_node['data']
            
            # Display current verse info
            st.markdown(f"""
            **{node_data.get('book', '')} {node_data.get('chapter', '')}:{node_data.get('verse', '')}**
            
            {node_data.get('text', '')}
            """)
            
            # Find connected edges
            connected_edges = [
                e for e in edges 
                if e['data'].get('source') == current_verse_id or e['data'].get('target') == current_verse_id
            ]
            connected_edges.sort(key=lambda x: x['data'].get('weight', 0), reverse=True)
            
            st.markdown(f"**Cross-References ({len(connected_edges)})**")
            
            # Display references
            for idx, edge in enumerate(connected_edges):
                neighbor_id = edge['data']['target'] if edge['data'].get('source') == current_verse_id else edge['data']['source']
                neighbor_node = next((n for n in nodes if n['data'].get('id') == neighbor_id), None)
                
                if neighbor_node:
                    neighbor_data = neighbor_node['data']
                    weight = edge['data'].get('weight', 0)
                    edge_id = edge['data'].get('id', f"edge_{idx}")
                    
                    with st.expander(f"{neighbor_id} (Votes: {weight})"):
                        st.markdown(f"**{neighbor_data.get('book', '')} {neighbor_data.get('chapter', '')}:{neighbor_data.get('verse', '')}**")
                        st.markdown(neighbor_data.get('text', ''))
                        
                        # Button to add to graph - use edge_id to ensure uniqueness
                        if st.button(f"Add {neighbor_id} to Graph", key=f"add_{neighbor_id}_{edge_id}_{idx}"):
                            if neighbor_node not in st.session_state.graph_elements:
                                st.session_state.graph_elements.append(neighbor_node)
                            st.session_state.selected_verse = neighbor_id
                            st.rerun()
    else:
        st.info("Click a verse in the Bible text to see cross-references.")

# Cytoscape visualization
st.markdown("---")
st.markdown("### 📊 Graph Visualization")

# Prepare elements for Cytoscape
cy_elements = st.session_state.graph_elements.copy()

# Add edges for visible nodes
visible_node_ids = [e['data'].get('id') for e in cy_elements if 'data' in e]
for edge in edges:
    source = edge['data'].get('source')
    target = edge['data'].get('target')
    if source in visible_node_ids and target in visible_node_ids:
        # Check if edge already exists
        edge_id = edge['data'].get('id', f"{source}_{target}")
        if not any(e.get('data', {}).get('id') == edge_id for e in cy_elements):
            cy_elements.append(edge)

# Create HTML with embedded Cytoscape
cytoscape_html = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #121212;
        }}
        #cy {{
            width: 100%;
            height: 600px;
            border: 1px solid #333;
            border-radius: 8px;
            background-color: #121212;
        }}
    </style>
</head>
<body>
    <div id="cy"></div>
    <script>
        const elements = {json.dumps(cy_elements)};
        
        const cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: elements,
            style: [
                {{
                    selector: 'node',
                    style: {{
                        'label': 'data(id)',
                        'background-color': '#FF0000',
                        'color': '#FFFFFF',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'font-size': '10px',
                        'text-transform': 'uppercase',
                        'padding': '8px',
                        'shape': 'round-rectangle',
                        'width': 'label',
                        'height': 'label',
                        'text-max-width': '100px',
                        'border-color': '#FF4500',
                        'border-width': 3,
                        'box-shadow': '0 0 12px #FF4500, inset 0 0 6px #FFFFFF',
                        'cursor': 'pointer'
                    }}
                }},
                {{
                    selector: 'edge',
                    style: {{
                        'curve-style': 'bezier',
                        'width': 'mapData(weight, 1, 300, 2, 6)',
                        'line-color': '#AAAAAA',
                        'opacity': 0.8,
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': '#AAAAAA'
                    }}
                }},
                {{
                    selector: '.highlighted',
                    style: {{
                        'background-color': '#FFA500',
                        'border-color': '#FFD700',
                        'line-color': '#00FFFF',
                        'opacity': 1,
                        'z-index': 999,
                        'box-shadow': '0 0 15px #FFFF00, inset 0 0 8px #FFFFFF'
                    }}
                }}
            ],
            layout: {{
                name: 'cose',
                animate: true,
                animationDuration: 600,
                fit: true,
                padding: 50,
                nodeRepulsion: 8000,
                idealEdgeLength: 100
            }}
        }});
        
        // Highlight selected verse if any
        const selectedId = '{current_verse_id if current_verse_id else ""}';
        if (selectedId) {{
            const selectedNode = cy.getElementById(selectedId);
            if (selectedNode.length) {{
                cy.elements().removeClass('highlighted');
                selectedNode.addClass('highlighted');
                selectedNode.connectedEdges().addClass('highlighted');
                cy.animate({{
                    center: {{ eles: selectedNode }},
                    zoom: 2.5
                }}, {{
                    duration: 500
                }});
            }}
        }}
        
        // Node click handler
        cy.on('tap', 'node', function(evt) {{
            const node = evt.target;
            cy.elements().removeClass('highlighted');
            node.addClass('highlighted');
            node.connectedEdges().addClass('highlighted');
            cy.animate({{
                center: {{ eles: node }},
                zoom: 2.5
            }}, {{
                duration: 500
            }});
        }});
    </script>
</body>
</html>
"""

# Display the Cytoscape graph
st.components.v1.html(cytoscape_html, height=600)

