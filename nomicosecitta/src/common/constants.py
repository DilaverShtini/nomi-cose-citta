# Default Network Configuration
DEFAULT_SERVER_HOST = '127.0.0.1'
DEFAULT_SERVER_PORT = 5000
BUFFER_SIZE = 1024
ENCODING = 'utf-8'

# File Paths
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHARED_DATA_PATH = os.path.join(BASE_DIR, "shared_data")