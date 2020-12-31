# Discord token and guild(Channel) name

DISCORD_TOKEN=""
DISCORD_GUILD=""

TWITCH_CHANNEL = ''
TWITCH_IRC_TOKEN = ''
TWITCH_CLIENT_ID = ''
TWITCH_NICK = ''
TWITCH_PREFIX = '#'

# Mugenoperator configuration. Use these to adjust the file locations, behaviour and buttons the operator uses.

# Select.def location. If you use themes, this needs to be modified to point to select.def within theme folder (data/<THEME_NAME>/select.def)
SELECTFILE = "data/select.def"

LOGFILE = "mugen.log"               # Path to log file to monitor
CHARFOLDER = "chars"                # Chars folder
CHARFILE = "charlist.txt"           # File to write list of characters to
BADCHARFILE = "badchar.txt"         # Path to a file containing list of bad characters

OK = "r"            # Button to press for selecting
NEXT = 'd'          # Button to press to move right
PREV = 'a'          # Button to press to move left
UP = 'w'            # Button to press to move up
DOWN = 's'          # Button to press to move down

ROUNDS = 2          # Rounds won required to win the match
HOLDTIME = 0.1      # Button down AND release time in seconds. Button press will always be HOLDTIME * 2. Low values can cause presses to be missed.  
DEBUG = True        # Enable debug prints for mugenoperator


# Number of time the same offset will be used
OFFSET_COUNT = 5

# Set this to prevent multiple registrations with same name
# Note that this will make the scores rather interesting
NO_DUPLICATES = 0

# Initial time and warning intervals in seconds. For testing purposes set these to smaller values. 
TIMER_INTERVALS = [180,120,60,30,15]

# Time to hold the results screens visible
RESULT_HOLDTIME = 15
RESULT_HOLDTIME_SHORT = 15

# File for scores
SCOREFILE = "match.score"

# Last position in the ranking list. Change this (or the .css) to fit the scores to the generated HTML-page
RANKING_LIST_MAX = 24

# Important pics...because important. One of these is sent to Discord when tournament ends.
PICS = ["match-common/Miya-results1.png", "match-common/Miya-results2.png", "match-common/Miya-results3.png"]
TOURNAMENT_START_PIC = "match-common/miya-happy-sm.png"

# M.A.T.C.H. Status codes, no need to ever touch these
IDLE = 0
REGISTRATION = 1
RUNNING = 2
ERROR = -1

