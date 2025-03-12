import customtkinter as ctk
import networkx as nx
import gin
from main import build_tree_from_index, visualize_tree

import sys
import os
import git
import tempfile
import plotly.graph_objects as go

class GitIndexVisualizer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Git Index Visualizer")
        self.geometry("1000x600")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        sidebar_width = int(self.winfo_screenwidth() * 0.25)
        self.sidebar_frame = ctk.CTkFrame(self, width=sidebar_width)
        self.sidebar_frame.pack(side="left", fill="y")

        self.label = ctk.CTkLabel(self.sidebar_frame, text="Enter Repository URL:")
        self.label.pack(pady=10)

        self.entry = ctk.CTkEntry(self.sidebar_frame, width=sidebar_width - 20)
        self.entry.pack(pady=10)

        self.button = ctk.CTkButton(self.sidebar_frame, text="Submit", command=self.visualize_repo)
        self.button.pack(pady=10)

        self.textbox = ctk.CTkTextbox(self.sidebar_frame, width=sidebar_width - 20, height=200)
        self.textbox.pack(pady=10, fill="both", expand=True)

        self.figure_frame = ctk.CTkFrame(self)
        self.figure_frame.pack(side="right", fill="both", expand=True)

    def visualize_repo(self):
        repo_url = self.entry.get()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                git.Repo.clone_from(repo_url, temp_dir)
                index_file = os.path.join(temp_dir, ".git", "index")

                if not os.path.isfile(index_file):
                    self.textbox.delete("1.0", ctk.END)
                    self.textbox.insert(ctk.END, f"Error: Index file not found at {index_file}")
                    return

                entries = list(gin.parse(index_file))
                tree = build_tree_from_index(entries)
                tree_str = str(tree)

                self.textbox.delete("1.0", ctk.END)
                self.textbox.insert(ctk.END, tree_str)

                graph = nx.DiGraph()
                visualize_tree(tree, graph)

                self.plot_3d_graph(graph)
        except Exception as e:
            self.textbox.delete("1.0", ctk.END)
            self.textbox.insert(ctk.END, f"Error: {str(e)}")

    def plot_3d_graph(self, graph):
        pos = nx.spring_layout(graph, dim=3)
        edge_x = []
        edge_y = []
        edge_z = []
        for edge in graph.edges():
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_z.extend([z0, z1, None])

        edge_trace = go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            mode='lines')

        node_x = []
        node_y = []
        node_z = []
        node_text = []
        for node in graph.nodes():
            x, y, z = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)
            node_text.append(graph.nodes[node]['label'])

        node_trace = go.Scatter3d(
            x=node_x, y=node_y, z=node_z,
            mode='markers+text',
            text=node_text,
            textposition='top center',
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                size=10,
                colorbar=dict(
                    thickness=15,
                    title='Node Connections',
                    xanchor='left'
                ),
                line_width=2))

        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
                            title='3D Git Index Visualization',
                            showlegend=False,
                            margin=dict(b=0, l=0, r=0, t=0),
                            scene=dict(
                                xaxis=dict(showbackground=False),
                                yaxis=dict(showbackground=False),
                                zaxis=dict(showbackground=False)),
                            hovermode='closest'))

        fig.show()

    def on_closing(self):
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = GitIndexVisualizer()
    app.mainloop()