
# tronbot.py
import os
import discord
from discord.ext import commands

import asyncio, time
import threading
import tournament as tournament
import random
from config import *

# Load discord configuration
from discord_config import *



class MiyakoBotDiscord(commands.Cog):
    def __init__(self, bot, matchsys):
        self.matchsys = matchsys
        self.bot = bot
        self.division_count = 0
        self.message_queue = []
        self.pic_message_queue = []
        self.waiting_presence = ""
        self.prefix = self.bot.command_prefix
    
    
    def __consoleprint(self, msg):
        self.matchsys.console_print(MSGNAME, msg)
    
    def set_matchsys(self, match):
        self.matchsys = match
    
    def set_presence(self, presence):
        self.waiting_presence = presence
    
    def queue_message(self, message):
        self.message_queue.append(message)

    def queue_pic(self, pic, message):
        self.pic_message_queue.append([pic, message])
    
    def var_insert(self, msg, var):
        return msg.replace("***", str(var))

    # Send generic message
    async def __send_message(self, message):
        await self.get_channel().send(message)

    # Get online presence
    def get_presence(self):
        guild = discord.utils.get(self.bot.guilds, name=DISCORD_GUILD)
        return guild.me.activity.name

    # Get client channel
    def get_channel(self):
        guild = discord.utils.get(self.bot.guilds, name=DISCORD_GUILD)
        return discord.utils.get(guild.text_channels, name=DISCORD_CHANNELNAME)

    # Update the presence to match tournament status
    async def update_presence(self, presence, idle):
        if idle:
            idle = discord.Activity(type=discord.ActivityType.unknown, name="Inactive")
            await self.bot.change_presence(activity=idle)
            return True
        elif presence != self.get_presence():
            game = discord.Game(name=presence)
            await self.bot.change_presence(activity=game)
            return True
    
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        raise error
    
    
    @commands.command(aliases=['s'])
    async def status(self, ctx):
        await ctx.send(self.status_command())
        
    
    @commands.command(aliases=['newtournament:', 'nt'])
    async def newtournament(self, ctx, value: str):
        #payload = self.strip_prefix(ctx.message.content)
        #payload = int(payload.split(" ")[1:][0])
        response = self.tournament_command(value)
        if response:
            await ctx.send(response)
    
        
    @commands.command(aliases=['register:', 'r'])
    async def register(self, ctx, numbers: str):
        response = self.register_user(numbers, ctx.message.author.name)
        if response:
            await ctx.send(response)


    # Client on_ready operates as watchdog for the system and executes tournaments
    # and timers. This runs in independent thread, so what happens here does not block
    # message functions.
    async def __send_pic(self, pic, message): 
        try:
            await self.get_channel().send(file=discord.File(pic), content=message)
        except FileNotFoundError:
            self.__consoleprint(pic + " is missing, not critical but plz fix")

    @commands.Cog.listener()
    async def on_ready(self):
        self.__consoleprint("Connecting...")
    
        guild = discord.utils.get(self.bot.guilds, name=DISCORD_GUILD)

        self.__consoleprint(f'{self.bot.user} connected to Discord')
        self.__consoleprint(f'Guild: {guild.name} (id: {guild.id})')

        idle = discord.Activity(type=discord.ActivityType.unknown, name="Inactive")
        await self.bot.change_presence(activity=idle)

        # Join specified channel and send greeting
        channel = discord.utils.get(guild.text_channels, name=DISCORD_CHANNELNAME)
        if channel:
            await channel.send(DC_GREETING1)
            await asyncio.sleep(2)
            await channel.send(DC_GREETING2)
            
        # Startup complete
        
        delay = 0
        # Main loop
        while(True):
            # Sleep for 10 seconds
            await asyncio.sleep(1)
            if delay == DELAY:
                delay = 0
            while self.pic_message_queue:
                self.__consoleprint("Sending pic message.")
                data = self.pic_message_queue.pop(0)
                await self.__send_pic(data[0], data[1])
            while self.message_queue:
                self.__consoleprint("Sending message.")
                await self.__send_message(self.message_queue.pop(0))
            while self.waiting_presence:
                if self.waiting_presence == "Idle":
                    await self.update_presence(self.waiting_presence, True)
                else:
                    await self.update_presence(self.waiting_presence, False)
                self.waiting_presence = ""
            delay += 1

    
    def status_command(self):
        status = self.matchsys.get_status()
        if status == IDLE:
            response = DC_IDLE_RESP
        elif status == REGISTRATION:
            response = DC_REGISTRATION_RESP
        elif status == RUNNING:
            response = DC_RUNNING_RESP
        else:
            response = DC_ERROR_RESP
        return response
    
    
    def tournament_command(self, divisions):
        response = ""
        try:
            divisions = int(divisions)
        except ValueError:
            return DC_TOUR_ERR_SYNTAX
        
        if self.matchsys.get_status() == RUNNING:
            response = DC_TOUR_ERR_RUNNING
        elif self.matchsys.get_status() == FINISHING:
            response = DC_TOUR_ERR_FINISHING
        elif self.matchsys.get_status() == REGISTRATION:
            response = DC_TOUR_ERR_RUNNING
        else:
            try:
                # Parse
                
                # Request new tournament from match system
                self.matchsys.new_tournament(divisions)
                # Tournament creation done. Now exit and wait for the MATCH to send us the data during it's next status check
                
            except ValueError:
                # Typo in message
                response = DC_TOUR_ERR_SYNTAX
            except AssertionError:
                # User gave a negative value for divisions...
                response = DC_TOUR_ERR_NEG_DIV
        return response


    def register_user(self, data, username):
        response = ""
        if self.matchsys.get_status() == RUNNING:
            response = DC_REG_ERR_TOUR_RUNNING
        elif self.matchsys.get_status() != REGISTRATION:
            response = DC_REG_ERR_NO_TOUR
        else:
            self.division_count = self.matchsys.get_divisions()
            # Parse
            
            chars = []
            realchars = []
            badchars = []
                
                # Check what registration contained
            try:
                print(f"Payload: {data}")
                for i in data.split(","):
                    print(f"Payload part: {i}")
                    value = self.matchsys.offset_char(int(i), True)
                    if int(i) < 0:
                        chars = []
                        response = DC_REG_ERR_NEG_ID
                        break
                    if int(i) > int(self.matchsys.get_max_ID()):
                        chars = []
                        response = self.var_insert(DC_REG_ERR_MAX_ID, self.matchsys.get_max_ID())
                        break
                    realchars.append(int(i))
                    chars.append(value)
            # Conversion to int failed, syntax error
            except ValueError:
                self.__consoleprint("Message did not contain numerical data")
                return DC_REG_ERR_SYNTAX
                
            
            if not self.matchsys.check_player(username):
                # If everything is fine so far, do final checks and then create new player
                if chars:
                    try:
                        player = self.matchsys.new_player(username, chars)
                    except IndexError:
                        return self.var_insert(DC_REG_ERR_ID_COUNT, self.division_count)

                    # Register characters first, if the registration fails. It matters not if these are there or not
                    badchars = self.matchsys.register_chars(realchars)
                    # Check if registration is accepted.
                
                    # If character registration gave us badchars, tell to user
                    if badchars:
                        var = ','.join(str(i) for i in badchars)
                        response = self.var_insert(DC_REG_ERR_ID_TAKEN, var)
                    else:
                        # Everything should be fine now, register
                        if self.matchsys.add_player(player):
                            register_message = username + " registered with characters: " + ', '.join(str(i) for i in realchars)
                            self.matchsys.queue_register_message(register_message)
                        else:
                            # It failed...what gives?
                            # So either data was checked badly or registration closed
                            # Verify the name in registration, in case some trickery was involved, otherwise the registration closed
                            if self.matchsys.check_player(username) and NO_DUPLICATES:
                                response = DC_REG_ERR_DUPLICATE
                            else:
                                response = DC_REG_ERR_CLOSED
                else:
                    response = DC_REG_ERR_DUPLICATE
        return response


    @commands.Cog.listener()
    async def on_message(self, message):
        '''Message parsing for mentions.
        '''
        # Remove own messages
        if message.author == self.bot.user:
            return
        # If mentioned in message, parse
        elif self.bot.user.mentioned_in(message):
            response = ""
            print(f"CONTENT WAS: {message.content}")
            payload = message.content.split(">")[1]
            
            if payload == " status": # status requested
                response = self.status_command()

            elif payload.startswith(" new tournament:"): # New tournament requested
                divisions = payload.split(":")[1:][0]
                response = self.tournament_command(divisions)

            elif payload.startswith(" register:"): # Registration received
                numbers = "".join(payload.split(":")[1:])
                response = self.register_user(numbers, message.author.name)
            else:
                return
            if response:
                await message.channel.send(response)
        #await self.bot.process_commands(message)
        return


