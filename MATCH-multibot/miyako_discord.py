
# tronbot.py
import os
import discord
import asyncio, time
import threading
import tournament as tournament
import random
from config import *


DELAY = 30


#game = discord.Game(name="Running tournament. Current division: " + str() + " divisions -- Registered: " + str(len(players)))
#await client.change_presence(activity=game)


class MiyakoBotDiscord(discord.Client):
    def __init__(self, matchsys, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matchsys = matchsys
        self.message_queue = []
        self.pic_message_queue = []
        self.waiting_presence = ""
    
    def set_matchsys(self, match):
        self.matchsys = match
    
    def set_presence(self, presence):
        self.waiting_presence = presence
    
    def queue_message(self, message):
        self.message_queue.append(message)

    def queue_pic(self, pic, message):
        self.pic_message_queue.append([pic, message])
        

    # Send generic message
    async def __send_message(self, message):
        await self.get_channel().send(message)

    # Get online presence
    def get_presence(self):
        guild = discord.utils.get(self.guilds, name=DISCORD_GUILD)
        return guild.me.activity.name

    # Get client channel
    def get_channel(self):
        guild = discord.utils.get(self.guilds, name=DISCORD_GUILD)
        return discord.utils.get(guild.text_channels, name='mugen-mayhem')

    # Update the presence to match tournament status

    async def update_presence(self, presence, idle):
        if idle:
            idle = discord.Activity(type=discord.ActivityType.unknown, name="Inactive")
            await self.change_presence(activity=idle)
            return True
        elif presence != self.get_presence():
            game = discord.Game(name=presence)
            await self.change_presence(activity=game)
            return True
        
            

    # Client on_ready operates as watchdog for the system and executes tournaments
    # and timers. This runs in independent thread, so what happens here does not block
    # message functions.
    async def __send_pic(self, pic, message): 
        try:
            await self.get_channel().send(file=discord.File(pic), content=message)
        except FileNotFoundError:
            print(pic + " is missing, not critical but plz fix")

    async def on_ready(self):
        guild = discord.utils.get(self.guilds, name=DISCORD_GUILD)

        print(f'{self.user} connected to Discord')
        print(f'Guild: {guild.name} (id: {guild.id})')

        idle = discord.Activity(type=discord.ActivityType.unknown, name="Inactive")
        await self.change_presence(activity=idle)

        # Join specified channel and send greeting
        channel = discord.utils.get(guild.text_channels, name='mugen-mayhem')
        if channel:
            message = "Miyako here-... "
            await channel.send(message)
            message = "Dan-kun wanted me to run some matches, so..."
            time.sleep(2)
            await channel.send(message)
            
        # Startup complete
        
        delay = 0
        # Main loop
        while(True):
            # Sleep for 10 seconds
            await asyncio.sleep(1)
            if delay == DELAY:
                delay = 0
                print("Miyako-Discord: Status: " + str(self.matchsys.get_status()))
            while self.pic_message_queue:
                print("Miyako-Discord: Sending pic message.")
                data = self.pic_message_queue.pop(0)
                await self.__send_pic(data[0], data[1])
            while self.message_queue:
                print("Miyako-Discord: Sending message.")
                await self.__send_message(self.message_queue.pop(0))
            while self.waiting_presence:
                if self.waiting_presence == "Idle":
                    await self.update_presence(self.waiting_presence, True)
                else:
                    await self.update_presence(self.waiting_presence, False)
                self.waiting_presence = ""
            delay += 1
            

    # Message handling
    async def on_message(self, message):
        # Remove own messages
        if message.author == self.user:
            return
        # If mentioned in message, parse
        elif self.user.mentioned_in(message):
            response = ""
            payload = message.content.split(">")[1]
            
            if payload == " status": # status requested
                status = self.matchsys.get_status()
                if status == IDLE:
                    response = "Idle at the moment"
                elif status == REGISTRATION:
                    response = "Collecting registrations"
                elif status == RUNNING:
                    response = "Running tournament"    
                else:
                    response = "Something is wrong"

            elif payload.startswith(" new tournament:"): # New tournament requested
                if self.matchsys.get_status() == RUNNING:
                    response = "Previous tournament still running"
                elif self.matchsys.get_status() == FINISHING:
                    response = "Previous tournament still finishing. Wait for a moment."
                else:
                    try:
                        # Parse
                        divisions = int(payload.split(":")[1:][0])
                        # Request new tournament from match system
                        self.matchsys.new_tournament(divisions)
                        # Tournament creation done. Now exit and wait for the MATCH to send us the data during it's next status check
                        
                    except ValueError:
                        # Typo in message
                        response = "Correct syntax is 'new tournament: <divisions>', dummy"
                    except AssertionError:
                        # User gave a negative value for divisions...
                        response = "Ha ha, negative amount of divisions...boy, you're just as keen as I am about this paperwork."

            elif payload.startswith(" register:"): # Registration received
                if self.matchsys.get_status() == RUNNING:
                    response = "Tournament has already started."
                elif self.matchsys.get_status() != REGISTRATION:
                    response = "No tournament registration ongoing."
                else:
                    try:
                        # Parse
                        data = payload.split(":")[1:]
                        chars = []
                        realchars = []
                        badchars = []
                        
                        # Check what registration contained
                        for i in data[0].split(",")[0:]:
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
            else:
                return
            if response:
                await message.channel.send(response)
        return
