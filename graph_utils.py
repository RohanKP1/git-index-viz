import networkx as nx
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import mplcursors

def build_graph_from_tree(node, graph=None, parent=None, max_depth=2, current_depth=0):
    """
    Build a NetworkX graph from a tree structure with optional depth limiting.
    Returns the graph and a dictionary mapping node IDs to TreeNode objects.
    """
    if graph is None:
        graph = nx.DiGraph()
    
    # Create a unique ID for this node
    node_id = f"{parent}_{node.name}" if parent else node.name
    
    # Add node to graph
    label = f"{node.name}\n({node.size} bytes)" if node.size > 0 else node.name
    color = '#FF9999' if node.is_file() else '#99CCFF'  # Red for files, blue for directories
    shape = 'o' if node.is_file() else 's'  # Circle for files, square for directories
    
    graph.add_node(node_id, 
                  label=label, 
                  size=node.size, 
                  color=color, 
                  shape=shape, 
                  expanded=False,
                  name=node.name,
                  type=node.node_type,
                  original_node=node)
    
    # Add edge if this isn't the root
    if parent:
        graph.add_edge(parent, node_id, color='#666666', style='solid')
    
    # Only process children if we're within depth limit
    if current_depth < max_depth:
        for child in node.children.values():
            build_graph_from_tree(child, graph, node_id, max_depth, current_depth + 1)
    
    return graph

def expand_node(graph, node_id, node_map):
    """Expand a collapsed node to show its children."""
    if node_id not in graph.nodes:
        return graph
    
    # Mark node as expanded
    graph.nodes[node_id]['expanded'] = True
    node = graph.nodes[node_id]['original_node']
    
    # Add all children
    for child in node.children.values():
        child_id = f"{node_id}_{child.name}"
        if child_id not in graph.nodes:
            label = f"{child.name}\n({child.size} bytes)" if child.size > 0 else child.name
            color = '#FF9999' if child.is_file() else '#99CCFF'
            shape = 'o' if child.is_file() else 's'
            
            graph.add_node(child_id, 
                          label=label, 
                          size=child.size, 
                          color=color, 
                          shape=shape, 
                          expanded=False,
                          name=child.name,
                          type=child.node_type,
                          original_node=child)
            
            graph.add_edge(node_id, child_id, color='#666666', style='solid')
    
    return graph

def collapse_node(graph, node_id):
    """Collapse an expanded node, removing its children from the graph."""
    if node_id not in graph.nodes:
        return graph
    
    # Mark node as not expanded
    graph.nodes[node_id]['expanded'] = False
    
    # Get all children recursively
    to_remove = []
    for child_id in list(graph.successors(node_id)):
        to_remove.append(child_id)
        # Get all descendants too
        descendants = list(nx.descendants(graph, child_id))
        to_remove.extend(descendants)
    
    # Remove all children
    for node in to_remove:
        if node in graph:
            graph.remove_node(node)
    
    return graph

def draw_interactive_graph(graph, ax, is_3d=False, selected_node=None):
    """Draw the graph with interactive capabilities."""
    # Using a spring layout for node positioning
    pos = nx.spring_layout(graph, dim=3) if is_3d else nx.spring_layout(graph, seed=42)
    
    # Clear previous plot
    ax.clear()
    
    # Different styling for selected nodes
    node_colors = []
    node_sizes = []
    
    for node in graph.nodes():
        if node == selected_node:
            node_colors.append('#FFFF00')  # Yellow for selected node
            node_sizes.append(700)         # Bigger for selected node
        else:
            node_colors.append(graph.nodes[node]['color'])
            node_sizes.append(500 if graph.nodes[node]['type'] == 'directory' else 300)
    
    if is_3d:
        # 3D plotting
        for i, (node, (x, y, z)) in enumerate(pos.items()):
            ax.scatter(x, y, z, s=node_sizes[i], c=node_colors[i], edgecolors='black')
            
            # Adjust label position
            label_text = graph.nodes[node]['name']
            if graph.nodes[node]['size'] > 0:
                label_text += f"\n({graph.nodes[node]['size']} bytes)"
            
            ax.text(x + 0.05, y + 0.05, z + 0.05, label_text, size=8, zorder=1, color='black')
        
        # Draw edges
        for u, v in graph.edges():
            x = [pos[u][0], pos[v][0]]
            y = [pos[u][1], pos[v][1]]
            z = [pos[u][2], pos[v][2]]
            ax.plot(x, y, z, color='#666666', alpha=0.6)
    else:
        # 2D plotting
        nx.draw(graph, pos, 
                ax=ax, 
                node_color=node_colors,
                node_size=node_sizes, 
                edgecolors='black',
                font_size=8,
                font_weight='bold',
                with_labels=False,
                edge_color='#666666',
                alpha=0.9)
        
        # Add labels with position adjustments
        for node, (x, y) in pos.items():
            label_text = graph.nodes[node]['name']
            if graph.nodes[node]['size'] > 0:
                label_text += f"\n({graph.nodes[node]['size']} bytes)"
            
            ax.text(x + 0.03, y + 0.03, label_text, size=8, color='black')
    
    # Turn off axis and grid
    ax.grid(False)
    ax.set_axis_off()
    ax.set_facecolor('white')
    
    return pos

    