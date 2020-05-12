
# tronbot.py
import os
import discord
import asyncio, time
import threading
import tournament as tournament
import mugenoperator as mo
import random

# Discord token and guild(Channel) name
TOKEN=""
GUILD="Triforce"


# Set this to prevent multiple registrations with same name
NO_DUPLICATES = 1

# Mugenoperator for running the matches
mugen = mo.MugenOperator()

# Greatest selectable chara id.
MAX_CHAR_ID = mugen.get_max_ID()

# Status codes
DISABLED = 0
REGISTRATION = 1
RUNNING = 2
ERROR = -1


# Number of time the same offset will be used
OFFSET_COUNT = 5
offset_counter = OFFSET_COUNT
offset = 0

# Tournament state
reserved_characters = []
players = []
old_players = []
div = 0
current_div = 1

# Important pics...because important
pics = ["Miya-results1.png", "Miya-results2.png", "Miya-results3.png"]

#Timers for the match start
timers = False
# Initial time and warning intervals
START = 90
WARN1 = 45
WARN2 = 15

def start_timers():
    global timers
    timers = True
    
def reset_timers():
    global timers
    timers = False
    
def timers_active():
    return timers
    
async def minute_warning(i, channel):
    await channel.send("Tournament starts in: " + str(i) + " seconds.")






# Create new tournament, store values of previous tournament (for no reason at this point)
def new_tournament(divisions):
    global players
    global div
    global reserved_characters
    global offset
    global offset_counter 
    global current_div
    
    assert(divisions > 0)
    current_div = 1
    players = []
    div = divisions
    reserved_characters = []
    if offset_counter >= OFFSET_COUNT:
        offset = random.randint(0, MAX_CHAR_ID)
        offset_counter = 0
        return True
    else:
        offset_counter += 1
        return False

# Register characters
def register_chars(chars):
    global reserved_characters
    reserved_characters += chars

# Add new player, check for duplicate 
def add_player(player):
    global players
    print("Added : " + str(player))
    if (NO_DUPLICATES):
        for i in players:
            assert(i["Name"] != player["Name"])
    players.append(player)
    return True

# Create new player with characters chars, raise IndexError if any character is reserved 

# PLAYER data
# Contains: User name, Achieved rank in each division, Character id's for Each division
# player == {"Name" : "Example", "Rank" : [0,0,0], "Characters" : [1,2,3]}

def new_player(name, chars):
    if not len(chars) == div:
        raise IndexError('Character mismatch')
        return {}
    return {"Name":name, "Rank": [0 for i in range(div)], "Characters": chars}

# Apply current offset
def offset_char(value, add):
    if add:
        tmp = value + offset
    else:
        tmp = value - offset
    return tmp % (MAX_CHAR_ID + 1)


###############################
# DISCORD STUFF FROM HERE ON ##
###############################

# Initialize the client
client = discord.Client()

# Find current online presence set to discord
# Use this as client state
def get_status():
    presence = get_presence()
    if presence.startswith('Inactive'):
        return DISABLED
    elif presence.startswith("Registration"):
        return REGISTRATION
    elif presence.startswith("Running"):
        return RUNNING
    else:
        return ERROR

# Get online presence
def get_presence():
    guild = discord.utils.get(client.guilds, name=GUILD)
    return guild.me.activity.name

# Get client channel
def get_channel():
    guild = discord.utils.get(client.guilds, name=GUILD)
    return discord.utils.get(guild.text_channels, name='mugen-mayhem')

# Update the presence to match tournament status

#statement = "Current battle: " + player1["Name"] + "("+ str(player1["Characters"][division]) + ")" 
#        statement += " VS. " + player2["Name"] + "("+ str(player2["Characters"][division]) + ")"



async def update_presence(tour):
    if tour.is_running():
        global current_div
        state_round = tour.get_state("Round")
        state_div = tour.get_state("Div")
        print("Division: " + str(state_div) + " (" + str(current_div) + ") : " + " round: " + str(state_round))
        if state_div == current_div:
            print("Division complete!")
            await get_channel().send(tour.rankings(players, current_div - 1))
            current_div = state_div + 1
        fight = tour.get_state("Fight")
        if fight:
            state_fight =  fight[0][0] + " (" + str(offset_char(fight[0][1], False)) + ") VS " 
            state_fight += fight[1][0] + " (" + str(offset_char(fight[1][1], False)) + ")"
            update_info_text("Current match: " + state_fight)
        else:
            state_fight = "-"
        new_presence = "Running tournament. Match: " + state_fight + " -- Division: " + str(state_div + 1) + " Round : " + str(state_round)
        if new_presence != get_presence():
            game = discord.Game(name=new_presence)
            await client.change_presence(activity=game)
        

# Client on_ready operates as watchdog for the system and executes tournaments
# and timers. This runs in independent thread, so what happens here does not block
# message functions.
async def send_pic(pic, message): 
    try:
        await get_channel().send(file=discord.File(pic), content=message)
    except FileNotFoundError:
        print(pic + " is missing, not critical but plz fix")

def update_info_text(text):
    f = open("info.html", "wt")
    f.write('<head><meta http-equiv="refresh" content="5">' + text + '</head>')
    f.close()


@client.event
async def on_ready():
    guild = discord.utils.get(client.guilds, name=GUILD)

    
    if(mugen.are_you_still_there()):
        print("MUGEN is active: " + str(mugen.get_state()))
    else:
        print("MUGEN is dead, abandon all hope.")
        mugen.reset()
    
    print(f'{client.user} connected to Discord')
    print(f'Guild: {guild.name} (id: {guild.id})')

    idle = discord.Activity(type=discord.ActivityType.unknown, name="Inactive")
    await client.change_presence(activity=idle)

    # Join specified channel and send greeting
    channel = discord.utils.get(guild.text_channels, name='mugen-mayhem')
    if channel:
        message = "Miyako here-... "
        await channel.send(message)
        message = "Dan-kun wanted me to run some matches, so..."
        time.sleep(2)
        await channel.send(message)
        
    tour = tournament.Tournament()
    update_info_text("")
    # Startup complete
    DELAY = 5
    delay = 0
    # Main loop
    while(True):
        # Sleep for 10 seconds
        await asyncio.sleep(10)
        if delay == DELAY:
            delay = 0
            print("Watchdog. Status: " + str(get_status()))
                
        delay += 1
        # Print status then check if timers & tournaments need running
        if not tour.is_running() and timers_active():
            # Run timers in order
            await minute_warning(START, channel,) # 60
            await asyncio.sleep(START - (WARN1 + WARN2)) #30
            await minute_warning(WARN1 + WARN2, channel,) #30
            await asyncio.sleep(WARN1) 
            await minute_warning(WARN2, channel,)
            await asyncio.sleep(WARN2)
            # Countdoen complete, reset
            reset_timers()
            
            # Kickoff tournament
            await send_pic("miya-happy-sm.png", "Tournament started, finally we get the good bit")
            
            # Create new tournament thread
            tour_t = threading.Thread(target=tour.run_tournament , args=(players, div, mugen))
            game = discord.Game(name="Running tournament. Current division: " + str() + " divisions -- Registered: " + str(len(players)))
            await client.change_presence(activity=game)
            
            print ("TOURNAMENT THREAD STARTED")
            tour_t.start()
            
        # While in tournament, suspend other activity
        if tour.is_running():
            while tour.is_running():
                # Check status
                await update_presence(tour)
                await asyncio.sleep(5)
            
            update_info_text("")
            await send_pic(pics[random.randint(0,len(pics) - 1)], "Ah that was nice.")
            await channel.send(tour.final_rankings(players, div))
            idle = discord.Activity(type=discord.ActivityType.unknown, name="Inactive")
            await client.change_presence(activity=idle)

# Message handling
@client.event
async def on_message(message):
    # Remove own messages
    if message.author == client.user:
        return
    # If mentioned in message, parse
    elif client.user.mentioned_in(message):
        payload = message.content.split(">")[1]
        
        if payload == " status": # status requested
            status = get_status()
            if status == DISABLED:
                response = "Idle at the moment"
            elif status == REGISTRATION:
                response = "Collecting registrations"
            elif status == RUNNING:
                response = "Running tournament"    
            else:
                response = "Something is wrong"

        elif payload.startswith(" new tournament:"): # New tournament requested
            if get_status() == RUNNING:
                response = "Previous tournament still running"
            else:
                try:
                    # Parse
                    divisions = int(payload.split(":")[1:][0])
                    offset_change = new_tournament(divisions)
                    # Update presence
                    game = discord.Game(name="Registration, " + str(divisions) + " divisions -- Registered: " + str(len(players)))
                    await client.change_presence(activity=game)
                    # Write response
                    response = "Registration is now open for tournament with " + str(divisions) + " divisions.\n"
                    if offset_change:
                        response += "New character offset was created.\n"
                    response += "Current character offset will be used for " + str(OFFSET_COUNT - offset_counter) + " matches.\n"        
                    response += "\nCharacter ID's 0-" + str(MAX_CHAR_ID) + " are accepted."
                    
                except ValueError:
                    # Typo in message
                    response = "Correct syntax is 'new tournament: <divisions>', dummy"
                except AssertionError:
                    # User gave a negative value for divisions...
                    response = "Ha ha, negative amount of divisions...boy, you're just as keen as I am about this paperwork."

        elif payload.startswith(" register:"): # Registration received
            if get_status() == RUNNING:
                response = "Tournament has already started."
            elif get_status() != REGISTRATION:
                response = "No tournament registration ongoing."
            else:
                try:
                    # Parse
                    data = payload.split(":")[1:]
                    chars = []
                    badchars = []
                    realchars = []
                    
                    # Check what registration contained
                    for i in data[0].split(",")[0:]:
                        value = offset_char(int(i), True)
                        if int(i) < 0:
                            chars = []
                            response = "There ain't no contestants with negative numbers, sheesh..."
                            break
                        if int(i) > MAX_CHAR_ID:
                            chars = []
                            await message.channel.send("Highest selectable id is " + str(MAX_CHAR_ID))
                            break
                        if reserved_characters.count(value):
                            chars= []
                            badchars.append(int(i)) 
                        elif not badchars:
                            chars.append(value)
                            realchars.append(int(i))
                    # If everything is fine so far, do final checks and then create new player
                    if chars and add_player(new_player(message.author.name, chars)):
                        register_chars(chars)
                        game = discord.Game(name="Registration, " + str(div) + " divisions -- Registered: " + str(len(players)))
                        await client.change_presence(activity=game)
                        
                        # Enough players for tournament, start counters
                        if len(players) > 1:
                            start_timers()
                        response = message.author.name + " registered with characters: " + ','.join(str(i) for i in realchars)
                    elif badchars:
                        # Output the badchars so the user can learn from this.
                        response = "Registration failed, following characters already taken: " + ','.join(str(i) for i in badchars)
                # Responses for bad values        
                except ValueError:
                    response = "Correct syntax is 'register: <character id>, <character 2id>,...', dummy"
                except IndexError:
                    response = "You need to give me exactly: " + str(div) + " characters"
                except AssertionError:
                    response = "Registration with your name already exists"
        else:
            return

        await message.channel.send(response)
    return

client.run(TOKEN)

