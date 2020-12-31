import threading
import time
import miyako_discord
import miyako_twitch
import tournament as tournament
import random
import mugenoperator as mo
import asyncio


from config import *

# Watchdog heartbeat delay rounds
DELAY = 60


class match_system():
    def __init__(self):
        self.state = IDLE
        self.timers = False
        self.__timer_count = TIMER_INTERVALS[0]
        
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
        self.register_messages = []
        self.division_complete = False
        
        
        self.scoreboard = self.__read_scorefile(SCOREFILE)
        if (USE_DISCORD):
            self.ds_client = miyako_discord.MiyakoBotDiscord(self)
        if (USE_TWITCH):
            self.twch_client = miyako_twitch.MiyakoBotTwitch(self)
        
        
        
    def check_mugen(self):
        if(self.mugen.are_you_still_there()):
            print("MUGEN is active: " + str(mugen.get_state()))
        else:
            print("MUGEN is dead, abandon all hope.")
            self.mugen.reset()

    # Update/create HTML file.
    # Text is the content, time is the automatic refresh time for the page
    # Idea here is that the page can be empty with minimal refresh time making it responsive to updates
    # When needed, the content can be updated and shown for refresh time.
    def update_file_text(self, text, file, time):
        html = ""
        endline = True
        for char in text:
            if char == '\n':
                html += "<br>"
                endline = True
            elif char == " " and endline:
                html +="&nbsp;"
            else:
                endline = False
                html += char
        f = open(file, "wt")
        # Write headers and then content
        f.write('<head><meta http-equiv="refresh" content=' + str(time) +'>')
        f.write('<link rel="stylesheet" type="text/css" href="style.css">')
        f.write('</head><body>')
        f.write(html)
        f.write('</body>')
        
        f.close()
        
        
    ########################
    # SCOREBOARD FUNCTIONS #
    ########################

    # Write scoreboard to file
    def __write_scorefile(self, data, file):
        f = open(file, "wt")
        for key in iter(data):
            f.write(key + "," + str(data[key]) + ",\n")
        f.close()

    # Read scoreboard from file
    def __read_scorefile(self, file):
        try:
            f = open(file, "r")
            data = {}
            for line in f:
                tmp = line.split(",")[:2]
                data[tmp[0]] = int(tmp[1])
            f.close() 
        except FileNotFoundError:
            # The scorefile has been cleared
            return {}
        return data

    # Add current scores to the scoreboard
    def __update_scoreboard(self, players):
        for player in players:
            score = 0
            for p in player["Rank"]:
               score += p
            if player["Name"] in self.scoreboard:
                self.scoreboard[player["Name"]] += score 
            else:
                self.scoreboard[player["Name"]] = score
        
    # Generates HTML table with scores from dictionary {"Name": score}
    def __scoretable(self, dict):
        table = "<table>"
        count = 1
        # Limit the table size to RANKING_LIST_MAX
        for player in [k for k in sorted(dict.items(), key=lambda item: item[1], reverse=True)]:
            if count > RANKING_LIST_MAX:
                break
            table += "<tr><td>" + str(count) + ".</td><td>" + player[0] + "</td><td>" + str(player[1]) + "</td></tr>"
            count += 1
        table += "</table>"
        return table

    # Create results HTML for the finished division. Display the page for HOLDTIME_SHORT.
    
    def show_division_results(self, results_dict, division):
        # Right, time to create and show the results with some HTML trickery
        # First create the page structure. Put the content in div to enable different style
        
        results_html = "<div> Division " + str(division) + " results."
        results_html += "\n--------------\n"
        results_html += self.__scoretable(results_dict) + "</div>"
        
        # Update page with results and automatic refresh of short holdtime
        self.update_file_text(results_html, "results.html", RESULT_HOLDTIME_SHORT)
        # Wait few seconds for the page to update
        time.sleep(3)
        # Write empty page with auto refresh of 1 second. This will be shown after the auto-refresh of the first update is reached
        self.update_file_text("", "results.html", 1)
        # Wait for the rest of the results holdtime.
        time.sleep(RESULT_HOLDTIME_SHORT - 2)

    ##################
    #     TIMERS     #
    ##################


    def __start_timers(self):
        self.timers = True
        
    def __reset_timers(self):
        self.__timer_count = TIMER_INTERVALS[0]
        self.timers = False
        
    def __timers_active(self):
        return self.timers

    # Return time alert
    def time_warning(self, i):
        return "Tournament starts in: " + str(i) + " seconds."



    #############################
    #     TOURNAMENT LOGIC      #
    #############################


    # Queue registration messages to be sent
    def queue_register_message(self, message):
        if message:
            self.register_messages.append(str(message))


    # Return current status of the system
    def get_status(self):
        return self.state

    # Return current tournament division count
    def get_divisions(self):
        return self.div
    
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

    # Get the current tournament status from the tournament subsystem
    # Updates the info text and lets the system know that division has finished
    # Returns a presence that can be forwarded to discord
    
    def tournament_status(self):
            if self.toursys.is_running() and self.get_status() == RUNNING:
                state_round = self.toursys.get_state("Round")
                state_div = self.toursys.get_state("Div")
                if state_div == self.ongoing_div:
                    self.ongoing_div = state_div + 1
                    self.division_complete = True
                fight = self.toursys.get_state("Fight")
                if fight:
                    state_fight =  fight[0][0] + " (" + str(self.offset_char(fight[0][1], False)) + ") VS " 
                    state_fight += fight[1][0] + " (" + str(self.offset_char(fight[1][1], False)) + ")"
                    self.update_file_text("Current match: " + state_fight, "info.html", 5)
                else:
                    state_fight = "-"
                new_presence = "Running tournament. Match: " + state_fight + " -- Division: " + str(state_div + 1) + " Round : " + str(state_round)
            else:
                if self.get_status() == IDLE:
                    new_presence = "Idle"
                elif self.get_status() == REGISTRATION:
                    new_presence = "Registration open for " + str(self.div) + " division tournament. Current entries: " + str(len(self.players))
                else:
                    new_presence = "Tournament ended"
            return new_presence


    ############################
    #      OFFSET SYSTEM       #
    ############################
    
    
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


    ######################################################
    #         MAIN LOGIC, THREADS & ASYNCIO LOOP         #
    ######################################################
    
    def main(self):
        
        main_thread = threading.Thread(target=self.main_loop, args=())
        main_thread.start()
        
        loop = asyncio.get_event_loop()
        if (USE_DISCORD):
            loop.create_task(self.ds_client.start(DISCORD_TOKEN))
        if (USE_TWITCH):
            loop.create_task(self.twch_client.start())
        if (USE_TWITCH or USE_DISCORD):
            loop.run_forever()
    
    
    
    
    # Main program logic
    #
    # 1. Idle state/Registration/Timers
    # 2. Tournament start
    # 3. Tournament loop
    # 4. Results
    #
    #
    
    def main_loop(self):
    
        # INIT
        
        self.toursys = tournament.Tournament()
        delay = 1
        
        # Reset the HTML outputs to empty content and 1 second refresh
        
        self.update_file_text("", "results.html", 1)
        self.update_file_text("", "info.html", 1)
        previous_state = self.get_status()
        
        
        # LOOP
        while(1):
            # IDLE/REGISTRATION START
             
            # Check for status change
            if previous_state != self.get_status():
                previous_state = self.get_status()
                
                # Registration started, update files & clients
                if self.get_status() == REGISTRATION:
                    self.update_file_text("Registration in progress", "info.html", 8)                    
                    # Send message to clients. Twitch is needs the message in two parts
                    message = "Registration is now open for tournament with " + str(self.div) + " divisions.\nCharacter ID's 0-" + self.get_max_ID() + " are accepted.\n"
                    ds_message = "" + message
                    if (USE_TWITCH):
                        # Send part 1 to Twitch
                        self.twch_client.queue_message(message)
                    
                    # Prepare the second part
                    message = ""
                    if self.offset_counter == 0:
                        message += "New character offset was created.\n"
                    message += "Current character offset will be used for " + self.get_offset_duration() + " matches.\n"
                    if (USE_TWITCH):
                        # Send part 2 to Twitch
                        self.twch_client.queue_message(message)

                    if (USE_DISCORD):
                        # Send both parts to Discord in one message
                        self.ds_client.queue_message(ds_message + message)
         
         
            if (USE_DISCORD):
                # Update the discord presence every 5 seconds
                if delay % 5 == 0:
                    self.ds_client.set_presence(self.tournament_status())
                
            # If any queued registrations exists, send them to all clients
            while self.register_messages:
                msg = self.register_messages.pop(0)
                if (USE_DISCORD):
                    self.ds_client.queue_message(msg)
                if (USE_TWITCH):
                    self.twch_client.queue_message(msg)

            # Timer system
            if self.__timers_active():
                for interval in TIMER_INTERVALS:
                    if self.__timer_count == interval:
                        if (USE_DISCORD):
                            self.ds_client.queue_message(self.time_warning(interval)) # 60
                        if (USE_TWITCH):
                            self.twch_client.queue_message(self.time_warning(interval))
                        self.update_file_text("Registration in progress. Tournament starting in " + str(interval), "info.html", 8)
                self.__timer_count -= 1

            # Print system status every DELAY seconds
            if delay > DELAY:
                print("M.A.T.C.H. status: " + str(self.get_status()))
                delay = 0
            delay += 1

            # Wait for one second
            time.sleep(1)


            # IDLE/REGISTRATION END

            # TOURNAMENT START AND RUNNING
            
            # Print status then check if timers & tournaments need running
            if not self.toursys.is_running() and self.__timers_active() and self.__timer_count <= 0:
                # Countdown complete, reset
                self.lock.acquire()
                self.state = RUNNING
                self.lock.release()
                self.__reset_timers()
                
                # Kickoff tournament
                if (USE_DISCORD):
                    self.ds_client.queue_pic(TOURNAMENT_START_PIC, "Tournament started, finally we get the good bit")
                if (USE_TWITCH):
                    self.twch_client.queue_message("Tournament started, finally some action.")
                # Create new tournament thread
                tour_t = threading.Thread(target=self.toursys.run_tournament , args=(self.players, self.div, self.mugen))
                
                print ("M.A.T.C.H.: TOURNAMENT THREAD STARTED")
                tour_t.start()
                
            # While in tournament, suspend other activity
            if self.toursys.is_running():
                delay = 0
                while self.toursys.is_running():
                    # Check status
                    # Send new presence data to Discord bot and update info texts
                    if (USE_DISCORD):
                        if delay == 5:
                            self.ds_client.set_presence(self.tournament_status())
                            delay = 0
                        
                    
                    # Check if we need to deliver division results
                    if self.division_complete:
                        self.division_complete = False
                        
                        # Sanity check, at least one division needs to be completed
                        if self.div > 0:
                            results, results_dict = self.toursys.rankings(self.players, self.ongoing_div - 2)
                            
                            # Send update to Discord
                            self.ds_client.queue_message("Division: " + str(self.ongoing_div - 1) + " finished." )
                            # Show results HTML
                            self.show_division_results(results_dict, self.ongoing_div - 1)                        
                            
                    time.sleep(1)
                    delay += 1
                
                # TOURNAMENT END
                
                # RESULTS
                
                # Clear the info text
                self.update_file_text("", "info.html", 1)
                
                if (USE_DISCORD):
                    # Update Discord presence and show division results:
                    self.ds_client.set_presence(self.tournament_status())
                results, results_dict = self.toursys.rankings(self.players, self.ongoing_div - 2)
                
                # Send update to Discord
                if (USE_DISCORD):
                    self.ds_client.queue_message("Division: " + str(self.ongoing_div) + " finished." )
                
                # Show results HTML
                self.show_division_results(results_dict, self.ongoing_div)
                
                
                print("M.A.T.C.H.: Tournament ended")
                
                # Send tournament end messages
                if (USE_TWITCH):
                    self.twch_client.queue_message("Tournament finished.")
                if (USE_DISCORD):
                    self.ds_client.queue_pic(PICS[random.randint(0,len(PICS) - 1)], "Ah that was nice.")
                # Create results
                results, results_dict = self.toursys.final_rankings(self.players, self.div)
                
                if (USE_DISCORD):
                    self.ds_client.queue_message(results)
                
                # Add scores to highscores and write new scorefile
                self.__update_scoreboard(self.players)
                self.__write_scorefile(self.scoreboard, SCOREFILE)
                
                
                
                # Update the results.html with results then highscores. 
                # Hold data for RESULT_HOLDTIME for both, then clear
                
                results_html = "<div>Final tournament scores:\n--------------\n" + self.__scoretable(results_dict) + " </div>"
                self.update_file_text(results_html, "results.html", RESULT_HOLDTIME)
                # Meanwhile, create HTML table for highscores
                scores = "<div>All time scores:\n--------------\n"
                scores += self.__scoretable(self.scoreboard)
                scores += "</div>"
                # Wait for the browser to update the page
                time.sleep(2)
                # Change content
                self.update_file_text(scores, "results.html", RESULT_HOLDTIME)
                # Wait for the results to change to highscores
                time.sleep(RESULT_HOLDTIME + 1)
                # Clear the page and set refresh to 1 second
                self.update_file_text("", "results.html", 1)

                # While the all-time scores are shown, reset the system state
                
                # Reset the previous state, in case someone tries to register before idle loop executes 
                previous_state = ""
                
                # Change state
                self.lock.acquire()
                self.state = IDLE
                self.lock.release()
                
                # Wait for the all-time highscores (Kinda pointless, might as well move ahead)
                # time.sleep(RESULT_HOLDTIME - 4)
                
                # And back to idle/registration part of the loop...
                


def main():   
    matchsys = match_system()
    matchsys.main() 
    
if __name__ == "__main__":
    main()
