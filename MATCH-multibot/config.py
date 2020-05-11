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
NO_DUPLICATES = 0

# Timer notification intervals in ~seconds. First index is the timer start point, rest are intervals for notifications.
# Insert as many as you like, but remember there is few second delay before these are updated to all outputs
# (Message sending delays, HTML update intervals and so forth)...and also that you can spam users to death with these.
TIMER_INTERVALS = [150,90,60,30,15]

# Time to hold the results screens visible
RESULT_HOLDTIME = 30
RESULT_HOLDTIME_SHORT = 15

# M.A.T.C.H. Status codes, leave these be
IDLE = 0
REGISTRATION = 1
RUNNING = 2
ERROR = -1
