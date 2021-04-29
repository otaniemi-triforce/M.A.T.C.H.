import threading
import time
import tournament as tournament
import random
import mugenoperator as mo
import asyncio

from config import *

if (USE_DISCORD):
    import miyako_discord
if (USE_TWITCH):
    import miyako_twitch

MSGNAME = "M.A.T.C.H."

# Console structure:

CONSOLE_STRUCTURE  = "\n\n\n"
CONSOLE_STRUCTURE += "Operator console\n"
CONSOLE_STRUCTURE += "----------------\n"
CONSOLE_STRUCTURE += "Command options:\n"
CONSOLE_STRUCTURE += "  1. Force tournament start\n"
CONSOLE_STRUCTURE += "  2. Reset registration\n"
CONSOLE_STRUCTURE += "  3. Halt tournament\n"
CONSOLE_STRUCTURE += "  4. Halt tournament and restart Mugen\n"
CONSOLE_STRUCTURE += "  5. Restart mugen\n"
CONSOLE_STRUCTURE += "Type option number and press enter to execute.\n"
CONSOLE_STRUCTURE += "Empty or invalid option closes console.\n"



class match_system():
    def __init__(self):
        self.state = IDLE
        self.timers = False
        self.status = ""
        self.__timer_count = TIMER_INTERVALS[0]
        self.console_locked = 0
        
        self.mugen = ""
        self.max_char_ID = 0
        
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
        self.ds_client = ""
        self.twch_client = ""
        
        
        
    def __init_mugen(self):
        self.mugen = mo.MugenOperator(self)
        self.max_char_ID = self.mugen.get_max_ID()


        
    # Function to check if mugen is still running

    def check_mugen(self):
        if self.mugen.are_you_still_there():
            if self.state == ERROR:
                self.lock.acquire()
                self.state = IDLE
                self.lock.release()
                # Some kind of message needs to be sent.
        else:
            self.lock.acquire()
            self.state = ERROR
            self.lock.release()
            
            self.mugen.reset(True)


    def check_mugen_loaded(self):
        state = self.mugen.get_state()
        return not (state == mo.LOADING_STATE or state == mo.DEAD_STATE)



    # Function to control console printouts.
    
    def console_print(self, sender, message):
        if not self.console_locked:
            print(str(sender) + ": " + str(message))


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
        try:
            f = open(file, "wt", encoding="utf-8")
            # Write headers and then content
            f.write('<head><meta http-equiv="refresh" content=' + str(time) +'>')
            f.write('<link rel="stylesheet" type="text/css" href="style.css">')
            f.write('</head><body>')
            f.write(html)
            f.write('</body>')
            
            f.close()
        except UnicodeEncodeError:
            self.console_print(MSGNAME, "Character encoding error while updating file: " + file)
            
            
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
    
    def show_html_results(self, results_dict, title, display_time):
        # Right, time to create and show the results with some HTML trickery
        # First create the page structure. Put the content in div to enable different style
        
        results_html = "<div> " + str(title) 
        results_html += "\n--------------\n"
        results_html += self.__scoretable(results_dict) + "</div>"
        
        # Update page with results and automatic refresh of short holdtime
        self.update_file_text(results_html, "results.html", display_time)
        # Wait few seconds for the page to update
        time.sleep(3)
        # Write empty page with auto refresh of 1 second. This will be shown after the auto-refresh of the first update is reached
        self.update_file_text("", "results.html", 1)

        # Wait for the rest of the results holdtime.
        if display_time > 2:
            time.sleep(display_time - 2)

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
        return str(i) + " seconds to tournament start."



    #################################
    #     TOURNAMENT FUNCTIONS      #
    #################################


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


    # Check if player is already registered
    
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



    # Remove given characters that have been previously selected
    
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
        self.console_print(MSGNAME,"Added : " + str(player))
        return True



    # Create new player with characters chars, raise IndexError if any character is reserved 
    # PLAYER data contains: 
    # User name, Achieved rank in each division, Character id's for Each division
    # player == {"Name" : "Example", "Rank" : [0,0,0], "Characters" : [1,2,3]}

    def new_player(self, name, chars):
        if not len(chars) == self.div:
            raise IndexError('Character mismatch')
            return {}
        return {"Name":name, "Rank": [0 for i in range(self.div)], "Characters": chars}
        


    ##################################
    #        TOURNAMENT LOGIC        #
    ##################################
        
    # Create new tournament, this will clear any previous tournament data
    
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
                elif self.get_status == RESET:
                    new_presence = "Match reset...stand by"
                else:
                    new_presence = "Tournament ended"
            return new_presence


    # Start and run tournament

    def run_tournament(self):
        # Create new tournament thread
        tour_t = threading.Thread(target=self.toursys.run_tournament , args=(self.players, self.div, self.mugen))
        
        self.console_print(MSGNAME,"Tournament controller started")
        tour_t.start()
    
        # Kickoff tournament
        if (USE_DISCORD):
            self.ds_client.queue_pic(TOURNAMENT_START_PIC, "Tournament started, finally we get the good bit")
        if (USE_TWITCH):
            self.twch_client.queue_message("Tournament started, finally some action.")
    
        # While in tournament, suspend other activity
        if self.toursys.is_running():
            timer = 0
            while self.toursys.is_running():
                # Check status
                status = self.tournament_status()
                # Send new presence data to Discord bot and update info texts
                if (USE_DISCORD):
                    if timer % 5 == 0:
                        self.ds_client.set_presence(status)
                        
                
                # Check if we need to deliver division results
                if self.division_complete:
                    self.division_complete = False
                    
                    # Sanity check, at least one division needs to be completed
                    if self.div > 0:
                        results, results_dict = self.toursys.rankings(self.players, self.ongoing_div - 2)
                        
                        text = "Division " + str(self.ongoing_div - 1)
                        if (USE_DISCORD):
                            # Send update to Discord
                            self.ds_client.queue_message(text + " finished." )
                        
                        # Show division results HTML
                        self.show_html_results(results_dict, text + " results.", RESULT_TIME_DIVISION)
                
                # Timer reset
                if status != self.status:
                    self.status = status
                    timer = 0
                
                # Recovery timer check
                if timer > RECOVERY_TIME:
                    # Mugen is probably stuck.
                    self.lock.acquire()
                    self.state = RESET
                    self.lock.release()
                    
                    self.mugen.reset(True)
                    timer = 0
                
                
                time.sleep(1)
                if self.check_mugen_loaded():
                    if self.state == RESET:
                        self.lock.acquire()
                        self.state = RUNNING
                        self.lock.release()
                    timer += 1



    def stop_tournament_registration(self):    
        # Stop only if in registration or timers are running
        if not (self.state == REGISTRATION or self.__timers_active()):
            return "No tournament registration ongoing"
        else:
            self.lock.acquire()
            self.state = IDLE
            self.__reset_timers()
            self.lock.release()
            self.console_print(MSGNAME, "Registration cancelled.")
            
            
            if (USE_DISCORD):
                self.ds_client.queue_message("Tournament registration aborted by operator")
            if (USE_TWITCH):
                self.twch_client.queue_message("Tournament registration aborted by operator")
            return ""
            

    def stop_tournament(self, kill):
        if self.state == IDLE or self.state == REGISTRATION:
            return "No tournament is running at the moment"
        else:
            self.lock.acquire()
            self.toursys.stop_tournament()
            self.state = IDLE
            self.lock.release()
            self.console_print(MSGNAME, "Tournament stopped.")
            if (USE_DISCORD):
                self.ds_client.queue_message("Ongoing tournament stopped by operator")
            if (USE_TWITCH):
                self.twch_client.queue_message("Ongoing tournament stopped by operator")

            # Kill mugen process as well, if requested.
            self.mugen.reset(kill)            
            return ""

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
        
        print(MSGNAME + " starting up...\n")
        print("Operator console can be accessed by pressing enter.")
        print("--------------------------------------------------------------\n\n")
        
        time.sleep(3)
        # Start mugen and init mugenoperator
        self.__init_mugen()
         
        # Init bots
        if (USE_DISCORD):
            self.ds_client = miyako_discord.MiyakoBotDiscord(self)
        if (USE_TWITCH):
            self.twch_client = miyako_twitch.MiyakoBotTwitch(self)

        # Start main loop
        main_thread = threading.Thread(target=self.main_loop, args=())
        main_thread.start()
        
        interaction_thread = threading.Thread(target=self.operator_loop, args=())
        interaction_thread.start()
        
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
    #    - Results
    # 4. Watchdog
    #
    
    def main_loop(self):
    
        # INIT
        self.toursys = tournament.Tournament(self)
        system_timer = 1
        
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
                if system_timer % 5 == 0:
                    self.ds_client.set_presence(self.tournament_status())
                
            # If any queued registrations exists, send them to all clients
            while self.register_messages:
                msg = self.register_messages.pop(0)
                if (USE_DISCORD):
                    self.ds_client.queue_message(msg)
                if (USE_TWITCH):
                    self.twch_client.queue_message(msg)

            # Timed message system
            if self.__timers_active():
                for interval in TIMER_INTERVALS:
                    if self.__timer_count == interval:
                        if (USE_DISCORD):
                            self.ds_client.queue_message(self.time_warning(interval))
                        if (USE_TWITCH):
                            self.twch_client.queue_message(self.time_warning(interval))
                        self.update_file_text("Registration in progress. Tournament starting in " + str(interval), "info.html", 8)
                self.__timer_count -= 1

            
            # IDLE/REGISTRATION END

            # TOURNAMENT START AND RUNNING
            
            # Print status then check if timers & tournaments need running
            if not self.toursys.is_running() and self.__timers_active() and self.__timer_count <= 0:
                # Countdown complete, reset
                self.lock.acquire()
                self.state = RUNNING
                self.lock.release()
                self.__reset_timers()
                
                self.run_tournament()
                
                # Check if the toursys was killed by operator.
                if self.state == RUNNING:
                
                    # TOURNAMENT END
                    
                    # Change state to finishing up
                    self.lock.acquire()
                    self.state = FINISHING
                    self.lock.release()
                    
                    
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
                    
                    # Show division results HTML
                    title = "Division " + str(self.ongoing_div) + " results."
                    self.show_html_results(results_dict, title, RESULT_TIME_DIVISION)
                    
                    
                    self.console_print(MSGNAME,"Showing results")
                    
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
                    
                    # Change state to idle before all time scores.
                    self.lock.acquire()
                    self.state = IDLE
                    self.lock.release()
                    
                    # Update the results.html with results then highscores. 
                    # Hold data for RESULT_TIME_FINAL for both, then clear
                    
                    title = "Final tournament scores:"
                    self.show_html_results(results_dict, title, RESULT_TIME_FINAL)
                    
                    # Meanwhile, create HTML table for highscores
                    title = "All time scores:"
                    self.show_html_results(self.scoreboard, title, RESULT_TIME_FINAL)
                    
                    # Reset the previous state, in case someone tries to register before idle loop executes 
                    previous_state = ""
                

            # Watchdog system                    
            # Print system status every DELAY seconds
            
            if system_timer > WATCHDOG_DELAY:
                self.check_mugen()
                if self.get_status() == IDLE:
                    status = "Ready - Waiting commands"
                elif self.get_status() == REGISTRATION:
                    status = "Registration ongoing"
                elif self.get_status() == RUNNING:
                    status = "Tournament running"
                elif self.get_status() == FINISHING:
                    status = "Tournament ended, displaying results"
                else:
                    status = "Mugen failure, trying to recover"
                self.console_print(MSGNAME,status)
                system_timer = 0
            system_timer += 1                
            
            # Wait for one second on each cycle of main loop
            time.sleep(1)    
            
            # End of the main loop. 


    ################################
    #  Operator console system     #
    ################################



    # Main operator console loop
        
    def operator_loop(self):
        while(True):
            input()
            
            # Suppress other console messages
            self.console_locked = 1
            
            print(CONSOLE_STRUCTURE)
            selection = input(">>")
            
            if selection == "1":
                self.force_tournament_start()
            elif selection == "2":
                self.op_registration_reset()
            elif selection == "3":
                self.op_tournament_reset()
            elif selection == "4":
                self.op_tournament_hard_reset()
            elif selection == "5":
                self.op_mugen_reset()
            else: 
                print("\n\n")
                # Completed, free console
                self.console_locked = 0
    
    def op_registration_reset(self):
        if self.op_confirm("This will stop the current registration and system returns to ready state"):
            print("Clearing registration...\n")
            
            self.console_locked = 0
            print(self.stop_tournament_registration())
    

    def force_tournament_start(self):
        if self.get_status() != REGISTRATION:
            print("Registration not running.\n\n")
            return False
        if len(self.players) < 2 :
            print("Too few registrations. Unable to force start.\n\n")
            return False
        if self.op_confirm(f"This will start the tournament with {len(self.players)} players."):
            print("Force starting tournament\n")
            
            self.console_locked = 0
            self.__timer_count = 1
            return True
    
        
    def op_tournament_reset(self):
        if self.op_confirm("Current running tournament will be stopped.\nResults data will be lost and system returns to ready state"):
            print("Tournament reset in progress...\n")
            self.console_locked = 0
            print(self.stop_tournament(False))
    
    def op_tournament_hard_reset(self):
        if self.op_confirm("Current running tournament and Mugen will be stopped.\nResults data will be lost and system returns to ready state"):
            print("Tournament and Mugen reset in progress...\n")
            self.console_locked = 0
            print(self.stop_tournament(True))
    
        
    def op_mugen_reset(self):
        if self.op_confirm("Current Mugen process will be killed and restarted."):
            print("Executing mugen restart...\n")
            self.console_locked = 0
            self.mugen.reset(True)

    def op_confirm(self, msg):
        print(msg)
        confirm = input("Are you sure? (Y/N)\n>>")
        if confirm == "y" or confirm == "Y":
            return True
        else:
            print("Action cancelled")
            return False

def main():   
    matchsys = match_system()
    matchsys.main() 
    
if __name__ == "__main__":
    main()
