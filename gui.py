import customtkinter as ctk
import networkx as nx
import mplcursors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import gin
from main import build_tree_from_index, visualize_tree, draw_tree

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # Import for 3D plotting
import sys
import os
import git
import tempfile
import shutil

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

        self.figure = plt.figure(figsize=(7, 5))
        self.ax = self.figure.add_subplot(111, projection='3d')  # Create a 3D subplot
        self.ax.set_axis_off()
        self.ax.grid(False)
        self.ax.set_facecolor('white')
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.figure_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def visualize_repo(self):
        repo_url = self.entry.get()
        temp_dir = tempfile.mkdtemp()
        try:
            repo = git.Repo.clone_from(repo_url, temp_dir)
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

            self.ax.clear()
            draw_tree(graph, self.ax, is_3d=True)  # Pass a flag to indicate 3D drawing
            self.canvas.draw()

            # Search for files in the repository and display them
            results = []
            for item in repo.tree().traverse():
                results.append(item.path)
            self.textbox.delete("1.0", ctk.END)
            if results:
                self.textbox.insert(ctk.END, "\n".join(results))
            else:
                self.textbox.insert(ctk.END, "No files found.")
        except Exception as e:
            self.textbox.delete("1.0", ctk.END)
            self.textbox.insert(ctk.END, f"Error: {str(e)}")
        finally:
            shutil.rmtree(temp_dir)

    def on_closing(self):
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = GitIndexVisualizer()
    app.mainloop()