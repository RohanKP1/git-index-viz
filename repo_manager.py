import os
import git
import gin
import hashlib
import shutil
import time
from tree_model import build_tree_from_index

class RepositoryManager:
    """Manages Git repository operations including cloning, caching, and parsing."""
    
    def __init__(self, cache_dir=None, cache_ttl=24*60*60, cache_size_limit=5):
        """
        Initialize the repository manager.
        
        Args:
            cache_dir: Directory to store cached repositories
            cache_ttl: Time-to-live for cached repositories in seconds (default: 24 hours)
            cache_size_limit: Maximum number of repositories to cache
        """
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser("~"), ".git_index_viz_cache")
        self.cache_ttl = cache_ttl
        self.cache_size_limit = cache_size_limit
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_cache_path(self, repo_url):
        """Generate a unique path for a repository in the cache."""
        url_hash = hashlib.md5(repo_url.encode()).hexdigest()
        return os.path.join(self.cache_dir, url_hash)
    
    def manage_cache(self):
        """Clean up old cache entries and ensure we're within the cache size limit."""
        cache_entries = []
        for entry in os.listdir(self.cache_dir):
            entry_path = os.path.join(self.cache_dir, entry)
            if os.path.isdir(entry_path):
                try:
                    mod_time = os.path.getmtime(entry_path)
                    cache_entries.append((entry_path, mod_time))
                except PermissionError:
                    print(f"Permission denied for {entry_path}. Skipping.")
                    continue
        
        # Sort entries by modification time (oldest first)
        cache_entries.sort(key=lambda x: x[1])
        
        # Remove old entries beyond the TTL
        current_time = time.time()
        for entry_path, mod_time in cache_entries[:]:
            if current_time - mod_time > self.cache_ttl:
                try:
                    shutil.rmtree(entry_path)
                    cache_entries.remove((entry_path, mod_time))
                except PermissionError:
                    print(f"Permission denied for {entry_path}. Skipping.")
                    continue
        
        # Ensure we're within the cache size limit
        while len(cache_entries) > self.cache_size_limit:
            # Remove the oldest entry
            oldest_entry = cache_entries.pop(0)
            try:
                shutil.rmtree(oldest_entry[0])
            except PermissionError:
                print(f"Permission denied for {oldest_entry[0]}. Skipping.")
                continue
    
    def clear_cache(self):
        """Clear all cached repositories."""
        for entry in os.listdir(self.cache_dir):
            entry_path = os.path.join(self.cache_dir, entry)
            if os.path.isdir(entry_path):
                shutil.rmtree(entry_path)
        return True
    
    def normalize_url(self, repo_url):
        """Normalize the repository URL for consistent caching."""
        # Remove .git suffix if present
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]
        
        # Fix GitHub URL format
        if "/tree/master" in repo_url:
            repo_url = repo_url.split("/tree/master")[0]
        
        # Ensure we have .git at the end for proper cloning
        if not repo_url.endswith(".git"):
            repo_url = repo_url + ".git"
        
        return repo_url
    
    def get_repository(self, repo_url):
        """
        Get a repository, either from cache or by cloning.
        
        Args:
            repo_url: URL of the repository to get
            
        Returns:
            tuple: (repo_dir, using_cache, error_message)
        """
        repo_url = self.normalize_url(repo_url)
        cache_path = self.get_cache_path(repo_url)
        using_cache = False
        error_message = None
        
        try:
            if os.path.exists(cache_path):
                # Check if the cache is still valid
                mod_time = os.path.getmtime(cache_path)
                if time.time() - mod_time <= self.cache_ttl:
                    using_cache = True
                    # Update the access time to mark it as recently used
                    os.utime(cache_path, None)
                    
                    # Verify this is the right repository
                    try:
                        repo = git.Repo(cache_path)
                        if repo_url != repo.remotes.origin.url:
                            using_cache = False
                            shutil.rmtree(cache_path)
                    except git.exc.InvalidGitRepositoryError:
                        using_cache = False
                        shutil.rmtree(cache_path)
                else:
                    # Cache is too old
                    shutil.rmtree(cache_path)
            
            if not using_cache:
                # Clone the repository to the cache
                git.Repo.clone_from(repo_url, cache_path)
                # Update cache management
                self.manage_cache()
            
            return cache_path, using_cache, None
            
        except Exception as e:
            return None, False, str(e)
    
    def get_tree_from_repo(self, repo_dir):
        """
        Parse the Git index file and build a tree representation.
        
        Args:
            repo_dir: Path to the repository
            
        Returns:
            tuple: (tree, error_message)
        """
        try:
            index_file = os.path.join(repo_dir, ".git", "index")
            
            if not os.path.isfile(index_file):
                return None, f"Index file not found at {index_file}"
            
            entries = list(gin.parse(index_file))
            tree = build_tree_from_index(entries)
            return tree, None
            
        except Exception as e:
            return None, str(e)
    
    def get_file_list(self, repo_dir):
        """
        Get a list of all files in the repository.
        
        Args:
            repo_dir: Path to the repository
            
        Returns:
            tuple: (file_list, error_message)
        """
        try:
            repo = git.Repo(repo_dir)
            results = []
            for item in repo.tree().traverse():
                results.append(item.path)
            return results, None
            
        except Exception as e:
            return None, str(e)