#### Bot settings ####

USE_DISCORD = 0 # Enable Discord bot
DISCORD_TOKEN=""
DISCORD_GUILD=""
DISCORD_CHANNELNAME = ''

## Important pics...because important. ## 
# One of these is sent to Discord when tournament ends. Feel free to add more/modify these.
PICS = ["match-common/Miya-results1.png", "match-common/Miya-results2.png", "match-common/Miya-results3.png"]
# Picture sent at the start of the tournament
TOURNAMENT_START_PIC = "match-common/miya-happy-sm.png"


#### Twitch bot settings ####

USE_TWITCH = 0 # Enable Twitch bot
TWITCH_CHANNEL = '------------------------'
TWITCH_IRC_TOKEN = ''
TWITCH_CLIENT_ID = ''
TWITCH_NICK = ''
TWITCH_PREFIX = '#'

# Mugenoperator configuration. Use these to adjust the file locations, behaviour and buttons the operator uses.

# Select.def location. If you use themes, this needs to be modified to point to select.def within theme folder (data/<THEME_NAME>/select.def)
SELECTFILE = "data/select.def"
CHARBEFORE = 0          # The number of objects, ie randomselects, before the beginning of characters the choose from


# These numbers should match to what is defined in your system.def for MUGEN
CHARCOLS = 13           # Columns in the character grid. Should match to "columns" under [Select Info] in your System.def
# ALSO: set the row number to high enough in the system.def [Select Info] so that columns * rows is equal or higher than the number of characters you have.
# Cursor starting positions, [row, column]
P1_CURSOR_START = [0,0] # Should match to "p1.cursor.startcell" in system.def [Select Info]
P2_CURSOR_START = [0,1] # Should match to "p2.cursor.startcell" in system.def [Select Info]


LOGFILE = "mugen.log"               # Path to log file to monitor
CHARFOLDER = "chars"                # Chars folder
CHARFILE = "charlist.txt"           # File to write list of characters to
BADCHARFILE = "badchar.txt"         # Path to a file containing list of bad characters

# Make sure these match to what you have configured for player 1
OK = "r"            # Button to press for selecting
NEXT = 'd'          # Button to press to move right
PREV = 'a'          # Button to press to move left
UP = 'w'            # Button to press to move up
DOWN = 's'          # Button to press to move down

ROUNDS = 2          # Rounds won required to win the match
HOLDTIME = 0.1      # Button down AND release time in seconds. Button press will always be HOLDTIME * 2. Low values can cause presses to be missed.  
DEBUG = True        # Enable debug prints for mugenoperator


#### HTML related parameters ####

# Duration the different scores are shown

# Used for final/all time scores
RESULT_TIME_FINAL = 15
# Used for division results
RESULT_TIME_DIVISION = 15

####   Highscores   ####

# File for scores
SCOREFILE = "match.score"

# Last position in the ranking list. Change this (or the .css) to fit the scores to the generated HTML-page
RANKING_LIST_MAX = 24


#### MATCH settings ####

# Number of time the same offset will be used
OFFSET_COUNT = 5

# Set this to prevent multiple registrations with same name
# Note that this can make the scores rather interesting
NO_DUPLICATES = 0

# Initial time and countdown intervals in seconds. For testing purposes set these to smaller values.
# First value defines starting point, rest are intervals.
# Intervals will be used in order from highest to lowest, values higher than the initial time will be ignored.
# A message is sent on every interval, any number of intervals can be used.

TIMER_INTERVALS = [6,2]


###

# Mugen self-recovery timer limit. The system will automatically reset mugen if single match takes this long
RECOVERY_TIME = 500

# Watchdog delay. This determines the M.A.T.C.H. status interval in seconds.
WATCHDOG_DELAY = 60

# Filenames used for writing results etc
RESULTS_HTML = "results.html"
RESULTS_TXT = "results.txt"
INFO_TXT = "info.txt"

# Results TXT structure (in lines or spaces)
LEFT_PADDING = 6
TOP_PADDING = 3
BOTTOM_PADDING = 3
TITLE_LEFT_PADDING = 18
WIDTH = 60
RANK_SPACES = 3
NAME_SPACES = 30
POINTS_SPACES = 7

# Results in HTML or txt
USE_HTML = False

# M.A.T.C.H. Status codes, no need to ever touch these
IDLE = 0
REGISTRATION = 1
RUNNING = 2
FINISHING = 3
ERROR = -1
RESET = -2

