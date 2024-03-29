from twitchio.ext import commands
import asyncio
from config import *

DELAY = 30
MSGNAME = "Miyako-Twitch"

class MiyakoBotTwitch(commands.Bot):

    def __init__(self, matchsys):
        super().__init__(token=TWITCH_IRC_TOKEN,
            client_id=TWITCH_CLIENT_ID,
            nick=TWITCH_NICK,
            prefix='#',
            initial_channels=[TWITCH_CHANNEL])   
        self.matchsys = matchsys
        self.message_queue = []
        
    
    def __consoleprint(self, msg):
        self.matchsys.console_print(MSGNAME, msg)
        
        
    def queue_message(self, message):
        self.message_queue.append(str(message))


    # Events don't need decorators when subclassed
    async def event_ready(self):
        self.__consoleprint(f'Ready | {self.nick}')
        delay = 0
        while(True):
            # Sleep for 10 seconds
            await asyncio.sleep(1)
            if delay == DELAY:
                delay = 0
            while self.message_queue:
                self.__consoleprint("Sending message.")
                await self.get_channel(TWITCH_CHANNEL).send(self.message_queue.pop(0))
                await asyncio.sleep(1.5)
            delay += 1


    async def event_message(self, message):
        """Message/Command handling. Most of the magic happens here"""
        
        if not message.author:
            return
        response = ""
        data = message.content.split(":")
        command = data[0].strip().lower()
        if command == "!new tournament" or command == "!nt":
            if len(data) == 2:
                value = int(data[1])
                try:
                    assert value > 0
                except AssertionError:
                    # User gave a silly value for divisions...
                    response = "Number of divisions must be positive number"
                else:
                    if self.matchsys.get_status() == IDLE:
                        self.__consoleprint("Registering new tournament: " + str(value))
                        offset_change = self.matchsys.new_tournament(value)
            await message.channel.send(response)
            
        elif command == "!register" or command == "!r":
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
                            return
                        if int(i) > int(self.matchsys.get_max_ID()):
                            chars = []
                            await message.channel.send("Highest selectable id is " + self.matchsys.get_max_ID())
                            return
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
                                register_message = message.author.name + " registered with characters: " + ','.join(str(i) for i in realchars)
                                self.matchsys.queue_register_message(register_message)
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
            if response:
                await message.channel.send(response)
        elif command == "!status" or command == "!s":
            status = self.matchsys.get_status()
            if status == IDLE:
                response = "Nothing happening, ready to go."
            elif status == REGISTRATION:
                response = "Registration open"
            elif status == RUNNING:
                response = "Running tournament"
            elif status == FINISHING:
                response = "Tournament ended"
            else:
                response = "Something is wrong"
            await message.channel.send(response)    
        #await self.handle_commands(message)
