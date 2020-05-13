# Discord token and guild(Channel) name

DISCORD_TOKEN=""
DISCORD_GUILD=""

TWITCH_CHANNEL = ''
TWITCH_IRC_TOKEN = ''
TWITCH_CLIENT_ID = ''
TWITCH_NICK = ''
TWITCH_PREFIX = '#'

# Number of time the same offset will be used
OFFSET_COUNT = 5

# Set this to prevent multiple registrations with same name
# Note that this will make the scores rather interesting
NO_DUPLICATES = 1

# Initial time and warning intervals
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
