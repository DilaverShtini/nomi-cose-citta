# Default Network Configuration
DEFAULT_SERVER_HOST = '127.0.0.1'
DEFAULT_SERVER_PORT = 5000
BUFFER_SIZE = 1024
ENCODING = 'utf-8'

# File Paths
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHARED_DATA_PATH = os.path.join(BASE_DIR, "shared_data")

# Replication Configuration
HEARTBEAT_FILE = os.path.join(SHARED_DATA_PATH, "heartbeat.json")
HEARTBEAT_INTERVAL = 2 #write heartbeat every 2 seconds
HEARTBEAT_TIMEOUT = 6 

# Game Configuration
DEFAULT_CATEGORIES = ["Name", "Things", "City"]

# Extra categories list available for selection
AVAILABLE_EXTRA_CATEGORIES = [
    "Animals",
    "Flowers",
    "Fruits",
    "Colors",
    "Professions",
    "Countries",
    "Sports",
    "Movies",
    "Singers",
    "Foods",
    "Brands",
    "Famous People",
    "Books",
    "TV Series",
    "Cartoon Characters",
    "Historical Figures",
    "Music Albums",
    "Video Games",
    "Monuments",
    "Board Games",
    "Musical Instruments",
    "Languages",
    "Plants",
    "Means of Transport",
    "Desserts",
    "Drinks",
    "Traditional Italian Dishes",
    "Mythological Characters",
    "Superheroes",
    "Fairy Tale Characters",
    "Comic Book Characters",
    "Applications",
    "Social Networks",
    "TV Shows",
    "Hobbies"
]

# Game modes
GAME_MODE_CLASSIC = "classic"           # Nomi + Cose + Città
GAME_MODE_CLASSIC_PLUS = "classic_plus" # Nomi + Cose + Città + N extra categories
GAME_MODE_FREE = "free"                 # Any N categories

# Game limits
MIN_EXTRA_CATEGORIES = 1
MAX_EXTRA_CATEGORIES = 10
MIN_ROUND_TIME = 30    # seconds
MAX_ROUND_TIME = 180   # seconds
DEFAULT_ROUND_TIME = 60

# Scoring rules
POINTS_UNIQUE_CATEGORY = 15
POINTS_UNIQUE_WORD = 10
POINTS_SHARED_WORD = 5
POINTS_INVALID = 0 

# Win condition
TARGET_SCORE = 100

#Voting phase duration (seconds) - server waits this long before forcing finalization
VOTING_SMALL_DURATION = 120
VOTING_MEDIUM_DURATION = 180
VOTING_LONG_DURATION = 240
VOTING_LONG_LONG_DURATION = 300

# Seconds to show score screen before starting the next round automatically
SCORE_DISPLAY_DELAY = 4
