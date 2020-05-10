from twitchio.ext import commands
import threading
import asyncio, time
from config import *

DELAY = 30


class MiyakoBotTwitch(commands.Bot):

    def __init__(self, matchsys):
        super().__init__(irc_token=TWITCH_IRC_TOKEN, client_id=TWITCH_CLIENT_ID, nick=TWITCH_NICK, prefix=TWITCH_PREFIX,
                         initial_channels=[TWITCH_CHANNEL])
        self.matchsys = matchsys
        self.message_queue = []
        
    def queue_message(self, message):
        self.message_queue.append(str(message))

    # Events don't need decorators when subclassed
    async def event_ready(self):
        threading.current_thread()
        print(f'Ready | {self.nick}')
        delay = 0
        while(True):
            # Sleep for 10 seconds
            await asyncio.sleep(1)
            if delay == DELAY:
                delay = 0
                print("Miyako-Twitch: Status: " + str(self.matchsys.get_status()))
            while self.message_queue:
                print("Miyako-Discord: Sending message.")
                await self.get_channel(TWITCH_CHANNEL).send(self.message_queue.pop(0))
            delay += 1

    async def event_message(self, message):
        if message.author.name == self.nick:
            print("Fukked")
            return
        response = ""
        data = message.content.split(":")
        if data[0].lower() == "!new tournament":
            try:
                value = int(data[1])
                print(str(value))
                if value > 0:
                    if self.matchsys.get_status() == IDLE:
                        offset_change = self.matchsys.new_tournament(value)
                        
            except ValueError:
                response = "Correct syntax is 'new tournament: <divisions>', dummy"
            except AssertionError:
                # User gave a negative value for divisions...
                response = "Ha ha, negative amount of divisions...boy, you're just as keen as I am about this paperwork."
            await message.channel.send(response)
        elif data[0].lower() == "!register":
            if self.matchsys.get_status() == RUNNING:
                response = "Tournament has already started."
            elif self.matchsys.get_status() != REGISTRATION:
                response = "No tournament registration ongoing."
            else:
                try:
                    # Parse
                    chars = []
                    realchars = []
                    badchars = []
                    
                    # Check what registration contained
                    for i in data[1].split(",")[0:]:
                        value = self.matchsys.offset_char(int(i), True)
                        if int(i) < 0:
                            chars = []
                            response = "There ain't no contestants with negative numbers, sheesh..."
                            break
                        if int(i) > int(self.matchsys.get_max_ID()):
                            chars = []
                            await message.channel.send("Highest selectable id is " + self.matchsys.get_max_ID())
                            break
                        realchars.append(int(i))
                        chars.append(value)
                    if not self.matchsys.check_player(message.author.name and NO_DUPLICATES):
                        player = self.matchsys.new_player(message.author.name, chars)
                        # If everything is fine so far, do final checks and then create new player
                        if chars:
                            # Register characters first, if the registration fails. It matters not if these are there or not
                            badchars = self.matchsys.register_chars(realchars)
                            # Check if registration is accepted.
                        
                        # If character registration gave us badchars, tell to user
                        if badchars:
                            response = "Registration failed, following characters already taken: " + ','.join(str(i) for i in badchars)
                        else:
                            # Everything should be fine now, register
                            if self.matchsys.add_player(player):
                                response = message.author.name + " registered with characters: " + ','.join(str(i) for i in realchars)
                            else:
                                # It failed...what gives?
                                # So either data was checked badly or registration closed
                                # Verify the name in registration, in case some trickery was involved, otherwise the registration closed
                                if self.matchsys.check_player(message.author.name) and NO_DUPLICATES:
                                    response = "Registration in your name already exists."
                                else:
                                    response = "Registration time has ended, sorry"
                    else:
                        response = "Registration in your name already exists."
                # Responses for bad values
                
                # Conversion to int failed, syntax error
                except ValueError:
                    response = "Correct syntax is 'register: <character id>, <character 2id>,...', dummy"
                # New player creation failed, incorrect number of divisions
                except IndexError:
                    response = "You need to give me exactly: " + str(self.matchsys.get_divisions()) + " characters. One for each division"
            await message.channel.send(response)
        elif data[0].lower() == "!status":
            status = self.matchsys.get_status()
            if status == IDLE:
                response = "Idle at the moment"
            elif status == REGISTRATION:
                response = "Collecting registrations"
            elif status == RUNNING:
                response = "Running tournament"    
            else:
                response = "Something is wrong"
            await message.channel.send(response)    
        #await self.handle_commands(message)
