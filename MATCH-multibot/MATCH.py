import threading
import time
import miyako_discord
import miyako_twitch
import tournament as tournament
import random
import mugenoperator as mo
import asyncio


from config import *

# Status codes
IDLE = 0
REGISTRATION = 1
RUNNING = 2
ERROR = -1

# Important pics...because important
pics = ["Miya-results1.png", "Miya-results2.png", "Miya-results3.png"]

# Time to hold the results screens visible
RESULT_HOLDTIME = 20

# Watchdog heartbeat delay rounds
DELAY = 20


class match_system():
    def __init__(self):
        self.state = IDLE
        self.timers = False
        
        self.mugen = mo.MugenOperator()
        self.max_char_ID = self.mugen.get_max_ID()
        
        self.reserved_characters = []
        self.players = []
        self.div = 0
        self.ongoing_div = 1
        self.offset = 0
        self.offset_counter = OFFSET_COUNT
        self.lock = threading.Lock()
        
        self.toursys = ""
        
        
    def check_mugen(self):
        if(self.mugen.are_you_still_there()):
            print("MUGEN is active: " + str(mugen.get_state()))
        else:
            print("MUGEN is dead, abandon all hope.")
            self.mugen.reset()

    def get_new_presence(self):
            if self.toursys.is_running() and self.get_status() == RUNNING:
                state_round = self.toursys.get_state("Round")
                state_div = self.toursys.get_state("Div")
                print("Division: " + str(state_div) + " (" + str(self.ongoing_div) + ") : " + " round: " + str(state_round))
                if state_div == self.ongoing_div:
                    print("Division complete!")
                    self.ongoing_div = state_div + 1
                    
                fight = self.toursys.get_state("Fight")
                if fight:
                    state_fight =  fight[0][0] + " (" + str(self.offset_char(fight[0][1], False)) + ") VS " 
                    state_fight += fight[1][0] + " (" + str(self.offset_char(fight[1][1], False)) + ")"
                    self.update_file_text("Current match: " + state_fight, "info.html")
                else:
                    state_fight = "-"
                new_presence = "Running tournament. Match: " + state_fight + " -- Division: " + str(state_div + 1) + " Round : " + str(state_round)
            else:
                if self.get_status() == IDLE:
                    new_presence = "Idle"
                elif self.get_status() == REGISTRATION:
                    new_presence = "Registration open for " + str(self.div) + " division tournament. Current entries: " + str(len(self.players))
            return new_presence

    def __start_timers(self):
        self.timers = True
        
    def __reset_timers(self):
        self.timers = False
        
    def __timers_active(self):
        return self.timers

    def update_file_text(self, text, file):
        html = ""
        for char in text:
            if char == '\n':
                html += "<br>"
            elif char == " ":
                html +="&nbsp;"
            else:
                html += char
        f = open(file, "wt")
        f.write('<head><meta http-equiv="refresh" content="5">' + html + '</head>')
        f.close()

    # Find current online presence set to discord
    # Use this as client state
    def get_status(self):
        return self.state
        
    def get_divisions(self):
        return self.div
    
    # Create new tournament, store values of previous tournament (for no reason at this point)
    def new_tournament(self, divisions):
        # Lock tournament data
        self.lock.acquire()
        # Check that the situation has not been changed by other threads
        if self.get_status() != IDLE:
            self.lock.release()
            return False
        
        # No tournament is running
        
        # This should be checked before entering new tournament.
        # This function will simply return false.
        if divisions < 1:
            self.lock.release()
            return False
        
        # Reset old tournament, start new
        self.ongoing_div = 1
        self.players = []
        self.div = divisions
        self.reserved_characters = []
        self.state = REGISTRATION
        # Check if offset needs renewing
        if self.offset_counter >= OFFSET_COUNT:
            self.offset = random.randint(0, self.max_char_ID)
            self.offset_counter = 0
        else:
            self.offset_counter += 1
        self.lock.release()
        return True
            
    def offset_changed(self):
        return self.offset_counter == 0

    def get_offset_duration(self):
        return str(OFFSET_COUNT - self.offset_counter)

    # Apply current offset
    def offset_char(self, value, add):
        if add:
            tmp = value + self.offset
        else:
            tmp = value - self.offset
        return tmp % (self.max_char_ID + 1)

    def get_max_ID(self):
        return str(self.max_char_ID)

    def check_player(self, name):
        for player in self.players:
            if player["Name"] == name:
                return True
        return False
                
    # Register characters, return list of characters that failed
    # Return empty list if success
    def register_chars(self, chars):
        badchars = []
        self.lock.acquire()
        if self.state != REGISTRATION:
            self.lock.release()
            return badchars
        for char in chars:
            if char in self.reserved_characters:
                badchars.append(char)
        if not badchars:
            self.reserved_characters += chars
        self.lock.release()
        return badchars

    def unregister_chars(self, chars):
        self.lock.acquire()
        for char in chars:
            if char in self.reserved_characters:
                reserved_characters.remove(char)
        self.lock.release()

    # Add new player, check for duplicate 
    def add_player(self, player):
        self.lock.acquire()
        # Ensure that state has not been changed by other threads
        if self.get_status() != REGISTRATION:
            self.lock.release()
            return False
        
        # Are duplicate entries unacceptable?
        if (NO_DUPLICATES):
            if self.check_player(player["Name"]):
                self.lock.release()
                return False    
        self.players.append(player)
        if len(self.players) > 1:
            self.__start_timers()
        self.lock.release()
        print("Added : " + str(player))
        return True

    # Create new player with characters chars, raise IndexError if any character is reserved 

    # PLAYER data
    # Contains: User name, Achieved rank in each division, Character id's for Each division
    # player == {"Name" : "Example", "Rank" : [0,0,0], "Characters" : [1,2,3]}

    def new_player(self, name, chars):
        if not len(chars) == self.div:
            raise IndexError('Character mismatch')
            return {}
        return {"Name":name, "Rank": [0 for i in range(self.div)], "Characters": chars}

    
    # Return time alert
    def time_warning(self, i):
        return "Tournament starts in: " + str(i) + " seconds."
    
    def main(self):
        ds_client = miyako_discord.MiyakoBotDiscord(self)
        twch_client = miyako_twitch.MiyakoBotTwitch(self)
        
        main_thread = threading.Thread(target=self.main_loop, args=(ds_client, twch_client))
        main_thread.start()
        
        loop = asyncio.get_event_loop()
        loop.create_task(ds_client.start(DISCORD_TOKEN))
        loop.create_task(twch_client.start())
        loop.run_forever()
    
    def main_loop(self, ds_client, twch_client):
        self.toursys = tournament.Tournament()
        delay = 1
        
        self.update_file_text("", "info.html")
        previous_state = self.get_status()
        
        
        while(1):
            if previous_state != self.get_status():
                previous_state = self.get_status()
                if self.get_status() == REGISTRATION:
                    self.update_file_text("Registration in progress", "info.html")
                
                    message = "Registration is now open for tournament with " + str(self.div) + " divisions.\n"
                    ds_client.queue_message(message)
                    twch_client.queue_message(message)
                    message = ""
                    if self.offset_counter == 0:
                        message += "New character offset was created.\n"
                    message += "Current character offset will be used for " + self.get_offset_duration() + " matches.\n"
                    ds_client.queue_message(message)
                    twch_client.queue_message(message)
                    message = "\nCharacter ID's 0-" + self.get_max_ID() + " are accepted."
                    ds_client.queue_message(message)
                    twch_client.queue_message(message)
                    
            if delay > DELAY:
                print("M.A.T.C.H.: waiting something to happen")
                delay = 0
            delay += 1
            time.sleep(5)
            ds_client.set_presence(self.get_new_presence())
            # Print status then check if timers & tournaments need running
            if not self.toursys.is_running() and self.__timers_active():
                print("M.A.T.C.H.: Timers started")
                # Run timers in order
                ds_client.queue_message(self.time_warning(START)) # 60
                twch_client.queue_message(self.time_warning(START))
                time.sleep(START - (WARN1 + WARN2)) #30
                ds_client.set_presence(self.get_new_presence())
                ds_client.queue_message(self.time_warning(WARN1 + WARN2)) #30
                twch_client.queue_message(self.time_warning(WARN1 + WARN2))
                self.update_file_text("Registration in progress. Tournament starting soon.", "info.html")
                time.sleep(WARN1) 
                ds_client.set_presence(self.get_new_presence())
                ds_client.queue_message(self.time_warning(WARN2))
                twch_client.queue_message(self.time_warning(WARN2))
                time.sleep(WARN2)
                # Countdown complete, reset
                self.lock.acquire()
                self.state = RUNNING
                self.lock.release()
                self.__reset_timers()
                
                # Kickoff tournament
                ds_client.queue_pic("miya-happy-sm.png", "Tournament started, finally we get the good bit")
                twch_client.queue_message("Tournament started, finally some action.")
                # Create new tournament thread
                tour_t = threading.Thread(target=self.toursys.run_tournament , args=(self.players, self.div, self.mugen))
                
                print ("M.A.T.C.H.: TOURNAMENT THREAD STARTED")
                tour_t.start()
                
            # While in tournament, suspend other activity
            if self.toursys.is_running():
                while self.toursys.is_running():
                    # Check status
                    # Send new presence data to Discord bot and update info texts
                    ds_client.set_presence(self.get_new_presence())
                    time.sleep(5)
                # Tournament ended
                self.lock.acquire()
                self.state = IDLE
                self.lock.release()
                self.update_file_text("", "info.html")
                print("M.A.T.C.H.: Tournament ended")
                twch_client.queue_message("Tournament finished.")
                ds_client.queue_pic(pics[random.randint(0,len(pics) - 1)], "Ah that was nice.")
                results = self.toursys.final_rankings(self.players, self.div)
                ds_client.queue_message(results)
                
                # Update the results.html. Hold data for RESULT_HOLDTIME and then clear
                results_html = "<div>Tournament ended\n" + results + " </div>"
                update_file_text(results_html, "results.html")
                time.sleep(RESULT_HOLDTIME)
                update_file_text("", "results.html")
                


def main():   
    jee = match_system()
    jee.main() 
    
if __name__ == "__main__":
    main()
