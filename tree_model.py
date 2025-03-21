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

    def __str__(self, level=0, prefix=""):
        size_str = f" ({self.size} bytes)" if self.size > 0 else ""
        type_icon = "📄 " if self.is_file() else "📁 "
        ret = prefix + ("└── " if level > 0 else "") + type_icon + self.name + size_str + "\n"
        children = list(self.children.values())
        for i, child in enumerate(children):
            if i == len(children) - 1:
                ret += child.__str__(level + 1, prefix + "    ")
            else:
                ret += child.__str__(level + 1, prefix + "│   ")
        return ret

def build_tree_from_index(entries):
    """Builds a tree structure from Git index entries."""
    root = TreeNode("root")
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