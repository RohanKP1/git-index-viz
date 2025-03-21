import customtkinter as ctk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
import mplcursors
import sys
import os
import threading

from repo_manager import RepositoryManager
from graph_utils import build_graph_from_tree, draw_interactive_graph, expand_node, collapse_node

class GitIndexVisualizer(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize repository manager
        self.repo_manager = RepositoryManager()

        # Initialize UI state variables
        self.current_repo_url = None
        self.current_repo_dir = None
        self.current_tree = None
        self.current_graph = None
        self.selected_node = None
        self.node_positions = None
        self.view_mode = "2D"  # or "3D"
        
        self.setup_ui()
    
    def setup_ui(self):
        self.title("Git Index Visualizer")
        self.geometry("1200x700")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configure the app grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)
        
        # === Left panel (controls and file tree) ===
        self.left_panel = ctk.CTkFrame(self)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.left_panel.grid_rowconfigure(3, weight=1)  # Make the treeview expandable
        self.left_panel.grid_columnconfigure(0, weight=1)
        
        # Repository URL input
        self.url_frame = ctk.CTkFrame(self.left_panel)
        self.url_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.url_frame.grid_columnconfigure(0, weight=1)
        
        self.url_label = ctk.CTkLabel(self.url_frame, text="Repository URL:")
        self.url_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.url_entry = ctk.CTkEntry(self.url_frame)
        self.url_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Cache status indicator
        self.cache_status = ctk.CTkLabel(self.left_panel, text="")
        self.cache_status.grid(row=1, column=0, sticky="ew", padx=10, pady=0)
        
        # Control buttons
        self.button_frame = ctk.CTkFrame(self.left_panel)
        self.button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.submit_button = ctk.CTkButton(
            self.button_frame, text="Load Repository", command=self.visualize_repo)
        self.submit_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.clear_cache_button = ctk.CTkButton(
            self.button_frame, text="Clear Cache", command=self.clear_cache)
        self.clear_cache_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.toggle_view_button = ctk.CTkButton(
            self.button_frame, text="Toggle 2D/3D", command=self.toggle_view_mode)
        self.toggle_view_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # File tree view (using a text widget for simplicity)
        self.file_tree_label = ctk.CTkLabel(self.left_panel, text="Repository Files:")
        self.file_tree_label.grid(row=3, column=0, sticky="nw", padx=10, pady=(10, 0))
        
        self.file_tree = ctk.CTkTextbox(self.left_panel, width=300, height=400)
        self.file_tree.grid(row=4, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        # === Right panel (graph visualization) ===
        self.right_panel = ctk.CTkFrame(self)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        
        # Graph title and info
        self.graph_info_frame = ctk.CTkFrame(self.right_panel)
        self.graph_info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.graph_info_frame.grid_columnconfigure(0, weight=1)
        
        self.graph_title = ctk.CTkLabel(
            self.graph_info_frame, 
            text="Git Repository Structure", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.graph_title.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.graph_instructions = ctk.CTkLabel(
            self.graph_info_frame, 
            text="Click on a directory node to expand/collapse it", 
            font=ctk.CTkFont(size=12)
        )
        self.graph_instructions.grid(row=1, column=0, sticky="w", padx=10, pady=0)
        
        self.node_info = ctk.CTkLabel(
            self.graph_info_frame, 
            text="No node selected", 
            font=ctk.CTkFont(size=12)
        )
        self.node_info.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        
        # Matplotlib figure for graph visualization
        self.figure_frame = ctk.CTkFrame(self.right_panel)
        self.figure_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.figure = plt.figure(figsize=(8, 6))
        self.ax = self.figure.add_subplot(111, projection='3d' if self.view_mode == "3D" else None)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.figure_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Set up canvas click event
        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)
        
        # Final setup
        self.update_status("Ready")
    
    def update_status(self, message):
        """Update the cache status label."""
        self.cache_status.configure(text=message)
        self.update_idletasks()
    
    def clear_cache(self):
        """Clear the repository cache."""
        threading.Thread(target=self._clear_cache).start()
    
    def _clear_cache(self):
        """Background thread for cache clearing."""
        self.update_status("Clearing cache...")
        success = self.repo_manager.clear_cache()
        if success:
            self.update_status("Cache cleared successfully")
            self.file_tree.delete("1.0", ctk.END)
            self.file_tree.insert(ctk.END, "Cache has been cleared successfully.")
        else:
            self.update_status("Failed to clear cache")
    
    def visualize_repo(self):
        """Load and visualize a repository."""
        repo_url = self.url_entry.get().strip()
        if not repo_url:
            self.update_status("Please enter a repository URL")
            return
        
        # Start the visualization in a background thread
        threading.Thread(target=self._visualize_repo, args=(repo_url,)).start()
    
    def _visualize_repo(self, repo_url):
        """Background thread for repository loading and visualization."""
        self.update_status("Processing repository...")
        
        # Normalize URL for display
        normalized_url = self.repo_manager.normalize_url(repo_url)
        self.url_entry.delete(0, ctk.END)
        self.url_entry.insert(0, normalized_url)
        
        # Get repository
        repo_dir, using_cache, error = self.repo_manager.get_repository(normalized_url)
        
        if error:
            self.update_status(f"Error: {error}")
            self.file_tree.delete("1.0", ctk.END)
            self.file_tree.insert(ctk.END, f"Error: {error}")
            return
        
        self.update_status("Using cached repository" if using_cache else "Repository loaded")
        
        # Get tree from repository
        tree, error = self.repo_manager.get_tree_from_repo(repo_dir)
        
        if error:
            self.update_status(f"Error: {error}")
            self.file_tree.delete("1.0", ctk.END)
            self.file_tree.insert(ctk.END, f"Error: {error}")
            return
        
        # Get file list
        files, error = self.repo_manager.get_file_list(repo_dir)
        
        if error:
            self.update_status(f"Warning: {error}")
        else:
            self.file_tree.delete("1.0", ctk.END)
            if files:
                self.file_tree.insert(ctk.END, "\n".join(files))
            else:
                self.file_tree.insert(ctk.END, "No files found.")
        
        # Build graph and visualize
        self.current_repo_url = normalized_url
        self.current_repo_dir = repo_dir
        self.current_tree = tree
        
        # Build initial graph (showing only first 2 levels)
        self.current_graph = build_graph_from_tree(tree, max_depth=2)
        
        # Draw graph
        self.redraw_graph()
        
        self.update_status("Repository visualization complete")
    
    def redraw_graph(self):
        """Redraw the graph with current settings."""
        if self.current_graph is None:
            return
        
        # Update axis projection if needed
        if self.view_mode == "3D" and not isinstance(self.ax, Axes3D):
            self.figure.clear()
            self.ax = self.figure.add_subplot(111, projection='3d')
        elif self.view_mode == "2D" and isinstance(self.ax, Axes3D):
            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
        
        # Draw the graph
        self.node_positions = draw_interactive_graph(
            self.current_graph, 
            self.ax, 
            is_3d=(self.view_mode == "3D"),
            selected_node=self.selected_node
        )
        
        # Update the canvas
        self.canvas.draw()
    
    def toggle_view_mode(self):
        """Toggle between 2D and 3D view modes."""
        self.view_mode = "2D" if self.view_mode == "3D" else "3D"
        self.update_status(f"Switched to {self.view_mode} view")
        self.redraw_graph()
    
    def on_canvas_click(self, event):
        """Handle click events on the graph canvas."""
        if self.current_graph is None or not event.inaxes:
            return
        
        # Get the closest node to the click position
        closest_node = None
        closest_dist = float('inf')
        
        for node, pos in self.node_positions.items():
            if self.view_mode == "3D":
                # For 3D, we need to project 3D coordinates to 2D screen coordinates
                x2d, y2d = self.ax.transData.transform((pos[0], pos[1]))
                dist = ((x2d - event.x) ** 2 + (y2d - event.y) ** 2) ** 0.5
            else:
                # For 2D, we can compute distance directly
                dist = ((pos[0] - event.xdata) ** 2 + (pos[1] - event.ydata) ** 2) ** 0.5
            
            if dist < closest_dist and dist < 0.1:  # Adjust threshold as needed
                closest_dist = dist
                closest_node = node
        
        if closest_node:
            # Update selected node
            self.selected_node = closest_node
            
            # Get node data
            node_data = self.current_graph.nodes[closest_node]
            
            # Update node info display
            if node_data['type'] == 'directory':
                if node_data['expanded']:
                    # Collapse the node
                    self.current_graph = collapse_node(self.current_graph, closest_node)
                    self.update_status(f"Collapsed directory: {node_data['name']}")
                else:
                    # Expand the node
                    self.current_graph = expand_node(self.current_graph, closest_node, None)
                    self.update_status(f"Expanded directory: {node_data['name']}")
            else:
                self.update_status(f"Selected file: {node_data['name']} ({node_data['size']} bytes)")
            
            # Update node info label
            node_type = "Directory" if node_data['type'] == 'directory' else "File"
            size_info = f" - {node_data['size']} bytes" if node_data['size'] > 0 else ""
            self.node_info.configure(text=f"Selected: {node_data['name']} ({node_type}{size_info})")
            
            # Redraw the graph
            self.redraw_graph()
    
    def on_closing(self):
        """Handle application closing."""
        self.destroy()
        sys.exit()