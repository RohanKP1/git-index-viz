import sys
import os
import git
import shutil
import hashlib
import time
import customtkinter as ctk
import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import gin
import matplotlib.pyplot as plt
from main import build_tree_from_index, visualize_tree, draw_tree

class GitIndexVisualizer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Git Index Visualizer")
        self.geometry("1000x600")

        # Set up cache directory
        self.cache_dir = os.path.join(os.path.expanduser("~"), ".git_index_viz_cache")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # Cache settings
        self.cache_ttl = 24 * 60 * 60  # 24 hours in seconds
        self.cache_size_limit = 5  # Maximum number of cached repositories

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        sidebar_width = int(self.winfo_screenwidth() * 0.25)
        self.sidebar_frame = ctk.CTkFrame(self, width=sidebar_width)
        self.sidebar_frame.pack(side="left", fill="y")

        self.label = ctk.CTkLabel(self.sidebar_frame, text="Enter Repository URL:")
        self.label.pack(pady=10)

        self.entry = ctk.CTkEntry(self.sidebar_frame, width=sidebar_width - 20)
        self.entry.pack(pady=10)

        # Cache status indicator
        self.cache_status = ctk.CTkLabel(self.sidebar_frame, text="")
        self.cache_status.pack(pady=2)

        button_frame = ctk.CTkFrame(self.sidebar_frame)
        button_frame.pack(pady=10)

        self.button = ctk.CTkButton(button_frame, text="Submit", command=self.visualize_repo)
        self.button.pack(side="left", padx=5)

        self.clear_cache_button = ctk.CTkButton(button_frame, text="Clear Cache", 
                                               command=self.clear_cache)
        self.clear_cache_button.pack(side="left", padx=5)

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

        # Connect the scroll event to the zoom function
        self.canvas.mpl_connect('scroll_event', self.zoom)

        # Manage cache on startup
        self.manage_cache()

    def zoom(self, event):
        """Zoom in or out on the graph."""
        base_scale = 1.1
        cur_xlim = self.ax.get_xlim3d()
        cur_ylim = self.ax.get_ylim3d()
        cur_zlim = self.ax.get_zlim3d()

        xdata = event.xdata
        ydata = event.ydata
        zdata = (cur_zlim[0] + cur_zlim[1]) / 2  # Use the center of the z-axis limits

        if event.button == 'up':
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            scale_factor = base_scale
        else:
            scale_factor = 1

        new_xlim = [xdata + (x - xdata) * scale_factor for x in cur_xlim]
        new_ylim = [ydata + (y - ydata) * scale_factor for y in cur_ylim]
        new_zlim = [zdata + (z - zdata) * scale_factor for z in cur_zlim]

        self.ax.set_xlim3d(new_xlim)
        self.ax.set_ylim3d(new_ylim)
        self.ax.set_zlim3d(new_zlim)

        self.canvas.draw_idle()

    def get_cache_path(self, repo_url):
        """Generate a unique path for a repository in the cache"""
        # Create a hash of the URL to use as the directory name
        url_hash = hashlib.md5(repo_url.encode()).hexdigest()
        return os.path.join(self.cache_dir, url_hash)

    def manage_cache(self):
        """Clean up old cache entries and ensure we're within the cache size limit"""
        cache_entries = []
        for entry in os.listdir(self.cache_dir):
            entry_path = os.path.join(self.cache_dir, entry)
            if os.path.isdir(entry_path):
                # Get the last modified time of the directory
                mod_time = os.path.getmtime(entry_path)
                cache_entries.append((entry_path, mod_time))
        
        # Sort entries by modification time (oldest first)
        cache_entries.sort(key=lambda x: x[1])
        
        # Remove old entries beyond the TTL
        current_time = time.time()
        for entry_path, mod_time in cache_entries:
            if current_time - mod_time > self.cache_ttl:
                shutil.rmtree(entry_path)
                cache_entries.remove((entry_path, mod_time))
        
        # Ensure we're within the cache size limit
        while len(cache_entries) > self.cache_size_limit:
            # Remove the oldest entry
            oldest_entry = cache_entries.pop(0)
            shutil.rmtree(oldest_entry[0])

    def clear_cache(self):
        """Clear all cached repositories"""
        for entry in os.listdir(self.cache_dir):
            entry_path = os.path.join(self.cache_dir, entry)
            if os.path.isdir(entry_path):
                shutil.rmtree(entry_path)
        
        self.cache_status.configure(text="Cache cleared")
        self.textbox.delete("1.0", ctk.END)
        self.textbox.insert(ctk.END, "Cache has been cleared successfully.")

    def visualize_repo(self):
        repo_url = self.entry.get()
        
        # Normalize the URL (remove .git suffix if present)
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]
        
        # Fix GitHub URL format
        if "/tree/master" in repo_url:
            repo_url = repo_url.split("/tree/master")[0]
            
        # Ensure we have .git at the end for proper cloning
        if not repo_url.endswith(".git"):
            repo_url = repo_url + ".git"
            
        self.entry.delete(0, ctk.END)
        self.entry.insert(0, repo_url)
            
        cache_path = self.get_cache_path(repo_url)
        using_cache = False
        
        if os.path.exists(cache_path):
            # Check if the cache is still valid
            mod_time = os.path.getmtime(cache_path)
            if time.time() - mod_time <= self.cache_ttl:
                using_cache = True
                # Update the access time to mark it as recently used
                os.utime(cache_path, None)
                self.cache_status.configure(text="Using cached repository")
            else:
                # Cache is too old, remove it
                shutil.rmtree(cache_path)
                self.cache_status.configure(text="Cache expired, refreshing...")
        else:
            self.cache_status.configure(text="Cloning repository...")
        
        try:
            if using_cache:
                repo_dir = cache_path
                # Check if the local repository is still valid
                try:
                    repo = git.Repo(repo_dir)
                    # Verify this is the right repository
                    if repo_url != repo.remotes.origin.url:
                        using_cache = False
                        shutil.rmtree(cache_path)
                        self.cache_status.configure(text="Cache mismatch, recloning...")
                except git.exc.InvalidGitRepositoryError:
                    using_cache = False
                    shutil.rmtree(cache_path)
                    self.cache_status.configure(text="Invalid cache, recloning...")
            
            if not using_cache:
                # Clone the repository to the cache
                repo = git.Repo.clone_from(repo_url, cache_path)
                self.cache_status.configure(text="Repository cached")
                repo_dir = cache_path
                
                # Update cache management
                self.manage_cache()
            
            # Proceed with visualization using the cached repository
            index_file = os.path.join(repo_dir, ".git", "index")

            if not os.path.isfile(index_file):
                self.textbox.delete("1.0", ctk.END)
                self.textbox.insert(ctk.END, f"Error: Index file not found at {index_file}")
                return

            entries = list(gin.parse(index_file))
            tree = build_tree_from_index(entries)
            tree_str = str(tree)
            # print(tree_str)

            graph = nx.DiGraph()
            visualize_tree(tree, graph)

            self.ax.clear()
            draw_tree(graph, self.ax, is_3d=True)  # Pass a flag to indicate 3D drawing
            self.canvas.draw()

            # Search for files in the repository and display them
            if tree_str:
                self.textbox.delete("1.0", ctk.END)
                self.textbox.insert(ctk.END, tree_str)
            else:
                self.textbox.insert(ctk.END, "No files found.")
                
        except Exception as e:
            self.textbox.delete("1.0", ctk.END)
            self.textbox.insert(ctk.END, f"Error: {str(e)}")
            self.cache_status.configure(text="Error occurred")

    def on_closing(self):
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = GitIndexVisualizer()
    app.mainloop()