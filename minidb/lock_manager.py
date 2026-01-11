"""
Lock Manager for Concurrency Control
Implements file-based locking for multi-user access
"""
import os
import time
from .exceptions import DatabaseBusyError

class LockManager:
    """Manages file-based locks for concurrent access to tables."""
    
    def __init__(self, data_dir="data", timeout=2.0, retry_interval=0.1):
        """
        Initialize the lock manager.
        
        Args:
            data_dir: Directory where lock files are stored
            timeout: Maximum time to wait for a lock (seconds)
            retry_interval: Time between lock acquisition attempts (seconds)
        """
        self.data_dir = data_dir
        self.timeout = timeout
        self.retry_interval = retry_interval
        
        # Ensure data directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _get_lock_path(self, table_name):
        """Get the path to the lock file for a table."""
        return os.path.join(self.data_dir, f"{table_name}.lock")
    
    def acquire_lock(self, table_name):
        """
        Acquire a lock on a table.
        
        Waits up to timeout seconds for the lock to become available.
        Creates a lock file to indicate the table is locked.
        
        Args:
            table_name: Name of the table to lock
            
        Raises:
            DatabaseBusyError: If lock cannot be acquired within timeout
        """
        lock_path = self._get_lock_path(table_name)
        start_time = time.time()
        
        while True:
            try:
                # Try to create lock file exclusively
                # 'x' mode fails if file already exists
                with open(lock_path, 'x') as f:
                    # Write process info for debugging
                    f.write(f"Locked at {time.time()}\n")
                    f.write(f"PID: {os.getpid()}\n")
                # Lock acquired successfully
                return
                
            except FileExistsError:
                # Lock file exists, someone else has the lock
                elapsed = time.time() - start_time
                
                if elapsed >= self.timeout:
                    # Timeout exceeded
                    raise DatabaseBusyError(
                        f"Could not acquire lock on table '{table_name}' "
                        f"after {self.timeout} seconds. Database is busy."
                    )
                
                # Wait and retry
                time.sleep(self.retry_interval)
    
    def release_lock(self, table_name):
        """
        Release a lock on a table.
        
        Removes the lock file to indicate the table is no longer locked.
        Safe to call even if lock doesn't exist.
        
        Args:
            table_name: Name of the table to unlock
        """
        lock_path = self._get_lock_path(table_name)
        
        try:
            if os.path.exists(lock_path):
                os.remove(lock_path)
        except OSError:
            # Lock file might have been removed by another process
            # or might not exist - this is okay
            pass
    
    def is_locked(self, table_name):
        """
        Check if a table is currently locked.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            bool: True if table is locked, False otherwise
        """
        lock_path = self._get_lock_path(table_name)
        return os.path.exists(lock_path)
    
    def cleanup_stale_locks(self, max_age=300):
        """
        Remove lock files older than max_age seconds.
        
        Useful for cleaning up locks from crashed processes.
        
        Args:
            max_age: Maximum age of lock files in seconds (default: 5 minutes)
        """
        if not os.path.exists(self.data_dir):
            return
        
        current_time = time.time()
        cleaned = []
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.lock'):
                lock_path = os.path.join(self.data_dir, filename)
                
                try:
                    # Check file age
                    file_age = current_time - os.path.getmtime(lock_path)
                    
                    if file_age > max_age:
                        os.remove(lock_path)
                        table_name = filename[:-5]  # Remove .lock extension
                        cleaned.append(table_name)
                        
                except OSError:
                    # File might have been removed already
                    pass
        
        return cleaned
