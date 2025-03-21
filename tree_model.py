from treelib import Tree

class TreeNode:
    """Node for representing files and directories in the Git repository."""
    def __init__(self, name, size=0, node_type="directory"):
        self.name = name
        self.size = size
        self.children = {}
        self.node_type = node_type  # "file" or "directory"

    def add_child(self, child):
        self.children[child.name] = child

    def get_child(self, name):
        return self.children.get(name)

    def get_children(self):
        return list(self.children.values())
    
    def is_file(self):
        return self.node_type == "file"
    
    def is_directory(self):
        return self.node_type == "directory"

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

def build_tree_from_index(entries, repo_url=None):
    """Builds a tree structure from Git index entries."""
    if repo_url is None:
        repo_name = "root"  
    else:      
        repo_name = repo_url.split('.git')[0].split('/')[-1] 
    root = TreeNode(repo_name)
    for entry in entries:
        if "name" in entry:
            parts = entry["name"].split('/')
            current_node = root
            # Process all parts except the last one as directories
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # Last part is a file
                    if part not in current_node.children:
                        new_node = TreeNode(part, entry.get("size", 0), "file")
                        current_node.add_child(new_node)
                else:
                    # This is a directory
                    if part not in current_node.children:
                        new_node = TreeNode(part, 0, "directory")
                        current_node.add_child(new_node)
                    current_node = current_node.children[part]
    return root