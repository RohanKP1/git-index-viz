import gin
import matplotlib.pyplot as plt
import networkx as nx
from treelib import Tree

class TreeNode:
    def __init__(self, name, size=0):
        self.name = name
        self.size = size
        self.children = {}

    def add_child(self, child):
        self.children[child.name] = child

    def __str__(self):
        tree = Tree()
        self._build_tree(tree, self)
        return tree.show(stdout=False)

    def _build_tree(self, tree, node, parent=None):
        node_id = node.name
        node_tag = f"{node.name} ({node.size} bytes)" if node.size > 0 else node.name
        tree.create_node(node_tag, node_id, parent=parent)
        for child in node.children.values():
            self._build_tree(tree, child, node_id)

def build_tree_from_index(entries):
    root = TreeNode("root")
    for entry in entries:
        if "name" in entry:
            parts = entry["name"].split('/')
            current_node = root
            for part in parts:
                if part not in current_node.children:
                    size = entry.get("size", 0) if part == parts[-1] else 0
                    new_node = TreeNode(part, size)
                    current_node.add_child(new_node)
                current_node = current_node.children[part]
    return root

def visualize_tree(node, graph, parent=None):
    label = f"{node.name}\n({node.size} bytes)" if node.size > 0 else node.name
    color = 'red' if node.size > 0 else 'green'  # Example color logic
    graph.add_node(node.name, label=label, size=node.size, color=color, shape='o')
    if parent:
        graph.add_edge(parent, node.name, color='blue', style='solid')
    for child in node.children.values():
        visualize_tree(child, graph, node.name)

def draw_tree(graph, ax, is_3d=False):
    pos = nx.spring_layout(graph, dim=3) if is_3d else nx.spring_layout(graph)
    
    if is_3d:
        for node, (x, y, z) in pos.items():
            ax.scatter(x, y, z, s=100)
            ax.text(x + 0.1, y + 0.1, z + 0.1, f"{node}\n({graph.nodes[node]['size']} bytes)", size=10, zorder=1, color='k')
        
        for edge in graph.edges():
            x = [pos[edge[0]][0], pos[edge[1]][0]]
            y = [pos[edge[0]][1], pos[edge[1]][1]]
            z = [pos[edge[0]][2], pos[edge[1]][2]]
            ax.plot(x, y, z, color='b')
    else:
        nx.draw(graph, pos, ax=ax, with_labels=False, node_size=500, node_color='skyblue', font_size=10, font_weight='bold')
        for node, (x, y) in pos.items():
            ax.text(x + 0.02, y + 0.02, f"{node}\n({graph.nodes[node]['size']} bytes)", size=10, color='k')
    
    ax.grid(False)  # Disable the grid
    ax.set_axis_off()  # Disable the axis
    ax.set_facecolor('white')  # Set the background color to white

def main():
    index_file = '.git/index'
    entries = list(gin.parse(index_file))
    tree = build_tree_from_index(entries)
    tree_str = str(tree)

    graph = nx.DiGraph()
    visualize_tree(tree, graph)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8), gridspec_kw={'width_ratios': [3, 7]})
    ax1.axis('off')
    ax1.text(0, 1, tree_str, fontsize=12, va='top', ha='left', family='monospace')
    draw_tree(graph, ax2)
    plt.show()

if __name__ == "__main__":
    main()