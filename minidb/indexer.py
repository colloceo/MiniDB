import os
import struct
from typing import Optional

class Indexer:
    """Manages a disk-based binary index for primary key lookups.
    
    Format: Pairs of (Primary_Key, File_Offset) stored as 8-byte binary integers.
    PK: 4-byte unsigned integer.
    Offset: 4-byte unsigned integer.
    """
    
    ENTRY_SIZE = 8  # 4 bytes for PK, 4 bytes for Offset
    
    def __init__(self, index_path: str) -> None:
        """Initializes the indexer with the path to the .idx file.
        
        Args:
            index_path: Path to the .idx file.
        """
        self.index_path = index_path

    def append(self, pk_val: int, offset: int) -> None:
        """Inserts a (PK, Offset) pair into the index file while maintaining sort order.
        
        Args:
            pk_val: The primary key value.
            offset: The byte offset in the main data file.
        """
        if not os.path.exists(self.index_path) or os.path.getsize(self.index_path) == 0:
            with open(self.index_path, "wb") as f:
                f.write(struct.pack('>II', pk_val, offset))
            return

        # Perform binary search to find the insertion point
        file_size = os.path.getsize(self.index_path)
        num_entries = file_size // self.ENTRY_SIZE
        
        insert_pos = num_entries # Default to end
        
        with open(self.index_path, "r+b") as f:
            left = 0
            right = num_entries - 1
            while left <= right:
                mid = (left + right) // 2
                f.seek(mid * self.ENTRY_SIZE)
                mid_pk, _ = struct.unpack('>II', f.read(self.ENTRY_SIZE))
                
                if mid_pk == pk_val:
                    # Duplicate PK? Should have been caught by Table validation
                    insert_pos = mid
                    break
                elif mid_pk < pk_val:
                    left = mid + 1
                    insert_pos = left
                else:
                    right = mid - 1
                    insert_pos = mid

            # Now shift entries from insert_pos onwards
            # This is O(N) but keeps the index sorted for O(log N) lookups
            for i in range(num_entries - 1, insert_pos - 1, -1):
                f.seek(i * self.ENTRY_SIZE)
                entry = f.read(self.ENTRY_SIZE)
                f.seek((i + 1) * self.ENTRY_SIZE)
                f.write(entry)
            
            # Write new entry
            f.seek(insert_pos * self.ENTRY_SIZE)
            f.write(struct.pack('>II', pk_val, offset))

    def find(self, target_pk: int) -> Optional[int]:
        """Performs a binary search on the index file to find the offset for a PK.
        
        Args:
            target_pk: The primary key value to search for.
            
        Returns:
            Optional[int]: The file offset if found, else None.
        """
        if not os.path.exists(self.index_path):
            return None
            
        file_size = os.path.getsize(self.index_path)
        num_entries = file_size // self.ENTRY_SIZE
        
        if num_entries == 0:
            return None
            
        left = 0
        right = num_entries - 1
        
        with open(self.index_path, "rb") as f:
            while left <= right:
                mid = (left + right) // 2
                f.seek(mid * self.ENTRY_SIZE)
                data = f.read(self.ENTRY_SIZE)
                
                if len(data) < self.ENTRY_SIZE:
                    break
                    
                pk_val, offset = struct.unpack('>II', data)
                
                if pk_val == target_pk:
                    return offset
                elif pk_val < target_pk:
                    left = mid + 1
                else:
                    right = mid - 1
                    
        return None

    def clear(self) -> None:
        """Deletes the index file."""
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
            
    def rebuild(self, pk_offset_pairs: list) -> None:
        """Rebuilds the index file from a list of (PK, Offset) pairs.
        
        Args:
            pk_offset_pairs: List of tuples (PK, Offset). Sorted by PK for binary search.
        """
        self.clear()
        # Sort by PK to ensure binary search works
        sorted_pairs = sorted(pk_offset_pairs, key=lambda x: x[0])
        with open(self.index_path, "wb") as f:
            for pk, offset in sorted_pairs:
                f.write(struct.pack('>II', pk, offset))
