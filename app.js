// Global variable to hold all graph data once fetched
let allGraphData = null;
let cy = null; // Cytoscape instance

// --- Core Data Loading ---

async function loadAllData() {
    try {
        const response = await fetch('cytoscape_data.json');
        if (!response.ok) {
             throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        allGraphData = data.elements;
        
        // Ensure all edges have IDs (if they don't already)
        allGraphData.edges = allGraphData.edges.map(edge => {
            if (!edge.data.id) {
                edge.data.id = `${edge.data.source}_${edge.data.target}`;
            }
            return edge;
        });
        
        console.log(`Successfully loaded ${allGraphData.nodes.length} nodes and ${allGraphData.edges.length} edges.`);
        
        // Start the visualization
        searchAndLoadVerse('JHN.1.1'); 
    } catch (error) {
        console.error("Error loading graph data:", error);
        alert(`Failed to load 'cytoscape_data.json'. Ensure the Python server is running and the file exists. Details: ${error.message}`);
    }
}

// --- Initialization ---

function initializeCy(initialElements) {
    if (cy) {
        cy.destroy(); 
    }

    cy = cytoscape({
        container: document.getElementById('cy'),
        elements: initialElements,
        
        style: [
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'background-color': '#4287f5',
                    'color': '#fff',
                    'text-valign': 'center',
                    'font-size': '10px',
                    'width': '15px',
                    'height': '15px',
                    'min-zoom': 0.1,
                    'border-color': '#333' 
                }
            },
            {
                selector: 'edge',
                style: {
                    'curve-style': 'bezier',
                    'width': 'mapData(weight, 1, 300, 1, 4)', 
                    'line-color': '#ccc',
                    'opacity': 0.6
                }
            },
            {
                selector: '.highlighted',
                style: {
                    'background-color': '#ff5722',
                    'line-color': '#ff5722',
                    'transition-property': 'background-color, line-color',
                    'transition-duration': '0.5s',
                    'z-index': 999
                }
            }
        ],

        layout: {
            name: 'cose', 
            animate: true,
            animationDuration: 500,
            padding: 50
        }
    });

    // --- Node Click Event to Populate the Reference Panel ---
    cy.on('tap', 'node', function(evt){
        const node = evt.target;
        const data = node.data();
        
        // Log the data to see what fields are available
        console.log('Node data:', data);
        
        // Try to get text from multiple possible field names
        const verseText = data.text_clean || data.text || data.verse_text || data.verse || 'No text available';
        const strongsText = data.text_strongs || data.strongs || data.strong || 'N/A';
        const bookName = data.book_name || data.book || 'Unknown';
        const chapter = data.chapter || '?';
        const verseNum = data.verse_number || data.verse_num || data.verse || '?';
        
        // 1. Update the main verse display
        document.getElementById('panel-header').textContent = `References for ${data.label || data.id}`;
        document.getElementById('current-verse-display').innerHTML = `
            <strong>${bookName} ${chapter}:${verseNum}</strong>
            <p>${verseText}</p>
            <p style="font-size: 0.8em; color: #555;">Strong's: ${strongsText}</p>
            <button onclick="expandNode('${data.id}')" style="padding: 5px 10px; background-color: #38c172; color: white; border: none; border-radius: 4px; cursor: pointer;">
                Expand TSK Connections on Graph
            </button>
        `;

        // 2. Populate the TSK Cross-References list
        const tskList = document.getElementById('tsk-list');
        tskList.innerHTML = ''; // Clear previous list

        // Find all connected edges
        const connectedEdges = allGraphData.edges.filter(e => 
            e.data.source === data.id || e.data.target === data.id
        ).sort((a, b) => b.data.weight - a.data.weight); // Sort by weight (Votes) descending

        if (connectedEdges.length === 0) {
            tskList.innerHTML = '<li>No TSK cross-references found in the data.</li>';
        } else {
            connectedEdges.forEach(edge => {
                const neighborId = edge.data.source === data.id ? edge.data.target : edge.data.source;
                const neighborData = getNodeData(neighborId);
                const listItem = document.createElement('li');
                listItem.style.cursor = 'pointer';
                listItem.style.padding = '5px';
                listItem.style.borderRadius = '3px';
                listItem.innerHTML = `
                    <span style="font-weight: bold;">${neighborId}</span> 
                    (Votes: ${edge.data.weight}) 
                    <span style="color: #888;">[Click to focus on graph]</span>
                `;
                // Add hover effect
                listItem.onmouseover = function() { this.style.backgroundColor = '#f0f0f0'; };
                listItem.onmouseout = function() { this.style.backgroundColor = ''; };
                
                // Add click listener to load and focus on the clicked reference
                listItem.addEventListener('click', () => {
                    loadAndFocusNode(neighborId);
                });
                tskList.appendChild(listItem);
            });
        }
    });
}

// --- Utility Functions ---

function getNodeData(id) {
    return allGraphData.nodes.find(n => n.data.id === id);
}

// Function to smoothly zoom/pan the graph to a specific node
function focusGraphOnNode(nodeId) {
    const node = cy.getElementById(nodeId);
    if (node.length) {
        cy.animate({
            center: { eles: node },
            zoom: 2 
        }, {
            duration: 500
        });

        // Add a temporary highlight class
        cy.elements().removeClass('highlighted');
        node.addClass('highlighted');
        
        // Trigger tap event to update the reference panel
        node.trigger('tap');
        
        setTimeout(() => {
            node.removeClass('highlighted');
        }, 1500);
    }
}

// Function to load a node onto the graph if it's not there, then focus on it
window.loadAndFocusNode = function(nodeId) {
    const existingNode = cy.getElementById(nodeId);
    
    if (existingNode.length) {
        // Node already exists, just focus on it
        focusGraphOnNode(nodeId);
    } else {
        // Node doesn't exist, need to add it
        const nodeData = getNodeData(nodeId);
        if (!nodeData) {
            alert(`Verse ID ${nodeId} not found in the dataset.`);
            return;
        }
        
        // Find all edges connecting to currently visible nodes
        const visibleNodeIds = cy.nodes().map(n => n.id());
        const connectingEdges = allGraphData.edges.filter(e => 
            (e.data.source === nodeId && visibleNodeIds.includes(e.data.target)) ||
            (e.data.target === nodeId && visibleNodeIds.includes(e.data.source))
        );
        
        // Add the new node and its connecting edges
        const elementsToAdd = [nodeData, ...connectingEdges];
        cy.add(elementsToAdd);
        
        // Run layout on all elements to properly position the new node
        cy.layout({
            name: 'cose',
            animate: true,
            animationDuration: 400,
            fit: true,
            padding: 50,
            nodeRepulsion: 8000,
            idealEdgeLength: 50,
            refresh: 20,
            randomize: false
        }).run();
        
        // Focus on the newly added node after layout completes
        setTimeout(() => {
            focusGraphOnNode(nodeId);
        }, 500);
    }
};

// --- Dynamic Node Loading Logic ---

// Function to expand a single node (add its neighbors)
window.expandNode = function(sourceId) {
    if (!allGraphData || !cy) return;

    // Filter to find edges connected to the sourceId
    const connectedEdges = allGraphData.edges.filter(e => 
        e.data.source === sourceId || e.data.target === sourceId
    );

    let newElements = [];
    const existingNodeIds = cy.nodes().map(n => n.id());
    const existingEdgeIds = cy.edges().map(e => e.id());

    // Identify and add connected nodes and edges that are not already visible
    connectedEdges.forEach(edge => {
        const neighborId = edge.data.source === sourceId ? edge.data.target : edge.data.source;
        
        // Add the neighbor node if it's not already in the graph
        if (!existingNodeIds.includes(neighborId)) {
            const neighborNode = getNodeData(neighborId);
            if (neighborNode) {
                newElements.push(neighborNode);
                existingNodeIds.push(neighborId); // Track that we're adding it
            }
        }
        
        // Add the edge if it's not already in the graph
        if (!existingEdgeIds.includes(edge.data.id)) {
            newElements.push(edge);
        }
    });
    
    if (newElements.length === 0) {
        console.log(`Node ${sourceId} fully expanded, no new connections to show.`);
        alert('All connections for this verse are already visible on the graph.');
        return;
    }

    // Add new elements to the graph
    cy.add(newElements);
    console.log(`Expanded ${sourceId}: Added ${newElements.length} new elements.`);
    
    // Run layout on all visible elements to properly integrate new nodes
    cy.layout({
        name: 'cose',
        animate: true,
        animationDuration: 600,
        fit: true,
        padding: 50,
        nodeRepulsion: 8000,
        idealEdgeLength: 50,
        refresh: 20,
        randomize: false
    }).run();
};

// Function called by the search button
window.searchAndLoadVerse = function(initialId = null) {
    const verseId = initialId || document.getElementById('verse-search').value.trim().toUpperCase();
    if (!verseId) return;

    const startNode = getNodeData(verseId);
    if (!startNode) {
        alert(`Verse ID "${verseId}" not found in data. Please use format like GEN.1.1`);
        return;
    }

    // Start with only the initial node
    const initialElements = [startNode];
    
    // Initialize the graph with the starting node
    initializeCy(initialElements);

    // After initialization, select the node to populate the panel and trigger expansion
    setTimeout(() => {
        const startNodeEle = cy.getElementById(verseId);
        if(startNodeEle.length) {
            startNodeEle.trigger('tap'); // Simulate a click to load the panel
        }
    }, 100); 
};

// Start the whole process by loading the data
loadAllData();