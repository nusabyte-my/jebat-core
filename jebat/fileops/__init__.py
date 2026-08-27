"""File operations — read, write, patch, search with safety."""

from .safety import BackupManager
from .read import read_file
from .write import write_file, undo_write
from .patch import patch_file
from .search import search_files