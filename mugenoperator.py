# This file should be in the same folder as mugen.exe to work properly

#from pynput.keyboard import Controller
#from pynput.keyboard import Key
from time import sleep
from ReadWriteMemory import ReadWriteMemory
import os
import signal
import math
import subprocess
import win32gui,win32api,win32con
from config import *


# Memory reader info
PROCESS_NAME = 'mugen.exe'
BASE_ADDRESS = 0x00400000
WIN_ADDRESS  = BASE_ADDRESS + 0x001040E8
THREADSTACK0 = 0x0019FF7C - 0x418

PLAYER1 = 1
PLAYER2 = 2

LOADING_STATE = 0
MENU_STATE = 1
SELECT_STATE = 2
VS_STATE = 3
FIGHT_STATE = 4
DEAD_STATE = 5



class MugenOperator():

    def __init__(self):
        self.player1_chars = []
        self.player2_chars = []
        self.rwm = ReadWriteMemory()
        self.char1 = -1
        self.char2 = -1
        self.winner = -1
        self.index = 0
        self.p = None
        self.window = 0
        self.max_id = self.check_characterlist()  # index of last char
        print("MUGEN OPERATOR STARTED. Number of characters detected: "+str(self.max_id + 1))
        self.lastrow = self.calculate_wanted_point(self.max_id)[1]
        self.reset()
    
    # Resets variables. Set kill = True to also kill MUGEN.
    def reset(self, kill = False):
        if(kill and self.p != None):
            try:
                os.kill(self.p.pid, signal.SIGTERM)
                self.debug("MUGEN killed.")
            except PermissionError:
                self.debug("Tried to kill MUGEN, but it seems to be already dead.")
                pass
        # If mugen is not already running (in most cases it shouldn't be), start it
        if (not self.are_you_still_there()):
            logpurged = False
            while not logpurged:
                try:
                    os.remove(LOGFILE)
                    open(LOGFILE, 'w').close()
                    logpurged = True
                except PermissionError: # Someone is still holding the file, give it a sec
                    sleep(1)
                    pass
            self.index = 0
            os.startfile(PROCESS_NAME)  # Start MUGEN
        else:   # MUGEN is running, set current index to end of current logfile
            f = open(LOGFILE)
            self.index = len(f.readlines())-1
            f.close()
        processloaded = False
        while not processloaded or self.p == None or self.window == 0:
            try:
                self.p = self.rwm.get_process_by_name(PROCESS_NAME)
                self.window = win32gui.FindWindow(None,"M.U.G.E.N")
                self.p.open()
                processloaded = True
            except:
                print("Process not found! Is MUGEN running? Trying again...")
                sleep(2)
        self.win1_ptr = self.p.get_pointer(WIN_ADDRESS, [0x0000871C])
        self.win2_ptr = self.p.get_pointer(WIN_ADDRESS, [0x00008728])

        self.loadingchar = 2
        self.player1_cursor = [0,0]
        self.player2_cursor = [1,0]
        self.state = LOADING_STATE
    
    # Check if MUGEN is still alive
    def are_you_still_there(self):
        processes = subprocess.Popen('tasklist', stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0]
        return (PROCESS_NAME.encode("utf8") in processes)
    
    def get_max_ID(self):
        return self.max_id
    
    # Return state of MUGEN
    def get_state(self):
        if(self.are_you_still_there()):
            return self.state
        return DEAD_STATE
    
    # Add a character to a list, returns True if success
    def add_character(self, charnum, pl):
        if(charnum < 0):
            return False
        if(pl == PLAYER1):
            self.player1_chars.append(charnum)
            return True
        elif(pl == PLAYER2):
            self.player2_chars.append(charnum)
            return True
        return False
    
    # returns the character queue for player pl
    def get_queue(self, pl):
        if(pl == PLAYER1):
            return self.player1_chars
        elif(pl == PLAYER2):
            return self.player2_chars
            
    # returns the character queue size for player pl
    def get_queue_size(self, pl):
        if(pl == PLAYER1):
            return len(self.player1_chars)
        elif(pl == PLAYER2):
            return len(self.player2_chars)

    # Read current match status from MUGEN's memory
    def readmem(self):
        self.p.read(WIN_ADDRESS)
        p1wins = int(self.p.read(self.p.get_pointer(WIN_ADDRESS, [0x0000871C])))
        p2wins = int(self.p.read(self.p.get_pointer(WIN_ADDRESS, [0x00008728])))
        self.debug("Match status: "+str(p1wins)+" - "+str(p2wins))
        if(p1wins == ROUNDS and p2wins == ROUNDS):  # Draw, not sure if this actually can happen in mugen
            self.winner = 0
        elif(p1wins == ROUNDS):                     # Player 1 wins
            self.winner = PLAYER1
        elif(p2wins == ROUNDS):                     # Player 2 wins
            self.winner = PLAYER2
    
    # Set cursor to where it needs to be
    def set_cursor_position(self,position):
        self.p.write(self.p.get_pointer(THREADSTACK0, [0x916]),position[0])
        self.p.write(self.p.get_pointer(THREADSTACK0, [0x917]),position[1])

    # Scan the log file and do operations based on lines there
    def scanlines(self):        
        f = open(LOGFILE,'r', encoding="utf8", errors="replace")   # Open logfile for reading
        lines = f.readlines()           # Read all lines to memory
        f.close()                       # Close the file for now   

        while(self.index < len(lines)):
            line = lines[self.index]
            self.index += 1
            
            # DETECT STATE CHANGES
            
            # Main menu loaded
            if(line.startswith("Mode select init")):
                self.state = MENU_STATE
                self.player1_cursor = [0,0]
                self.player2_cursor = [1,0]
                continue

            # Character select loaded
            elif(line.startswith("Charsel init")):
                self.state = SELECT_STATE
                continue
                
            # Fight
            elif(line.startswith("Game loop init")):
                self.state = FIGHT_STATE
                continue
            
            
            # OTHER PROCESSING
            
            # Round / match ended, check scoreboard
            if(line.startswith("Finishing match") or line.startswith("Resetting round")):
                self.readmem()
                continue

            # Char selected, check that it was same as it should be
            if(line.startswith("Selected char")):
                num = int(line.split()[2])
                player = line.split()[5]
                if(player == "0.0"):
                    if(num != self.char1):
                        self.debug("ERROR: Character mismatch. P"+str(player)+" char should be "+str(self.char1)+", but "+str(num)+" was loaded!")
                        self.player1_cursor = self.calculate_wanted_point(num)  # Fix cursor position
                else:
                    if(num != self.char2):
                        self.debug("ERROR: Character mismatch. P"+str(player)+" char should be "+str(self.char2)+", but "+str(num)+" was loaded!")
                        self.player2_cursor = self.calculate_wanted_point(num)  # Fix cursor position
            
            # Loading character
            if(line.startswith("Loading character")):
                self.loadingchar = int(self.loadingchar == 1) + 1 # Used for figuring out what failed, if any
                continue
                
            # Failed to load something
            if(line.endswith("failed to load\n") or line.endswith("failed to load")):
                # Character
                if(len(line.split("Character")) == 2):
                    self.winner = int(self.loadingchar==1)+1  # Mark the other player as winner
                    self.debug("ERROR: failed to load character for P"+str(self.loadingchar))
                    bchar = open(BADCHARFILE,'a')
                    bchar.write(line)
                    bchar.close()
                # Something else
                else:
                    self.debug("UNHANDLED FAILURE TO LOAD")
                    self.debug(line)
                    self.winner = 0
                
                # Mugen is dead, set state as such
                self.state = DEAD_STATE
                return

    def debug(self, msg):
        if(DEBUG):
            print(msg)

    # Memory based character load, memory addresses are machine specific! Not used in this version.
    '''
    def select_char(self,charnum, player):
    # Player 1
        if(player == PLAYER1):
            char1_ptr = self.p.get_pointer(THREADSTACK0, [0x354 + 0x10]) # Get pointer to the char variable in memory
            self.press(OK,1) # Accept anything
            self.char1 = charnum
            if(not self.p.write(char1_ptr,charnum)): # Overwrite whatever was just accepted
                debug("Failed to write P1 character!")
    # Player 2
        elif(player == PLAYER2):
            char2_ptr = self.p.get_pointer(THREADSTACK0, [0x1E30 + 0x10]) # Get pointer to the char variable in memory
            self.press(OK,1) # Accept anything
            self.char2 = charnum
            if(not self.p.write(char2_ptr,charnum)): # Overwrite whatever was just accepted
                debug("Failed to write P2 character!")
    '''

    def select_char(self, charnum, player):
        pos = self.calculate_wanted_point(charnum)
    # Player 1
        if(player == PLAYER1):
            if(self.player1_cursor[1] == self.lastrow):  # Move up to a full row
                self.press(UP,1)
                self.player1_cursor[1] -= 1
            while(self.player1_cursor != pos):
                if(pos[0] < self.player1_cursor[0]):
                    self.press(PREV,1)
                    self.player1_cursor[0] -= 1
                    continue
                elif(pos[0] > self.player1_cursor[0]):
                    self.press(NEXT,1)
                    self.player1_cursor[0] += 1
                    continue

                if(pos[1] < self.player1_cursor[1]):
                    self.press(UP,1)
                    self.player1_cursor[1] -= 1
                    continue
                elif(pos[1] > self.player1_cursor[1]):
                    self.press(DOWN,1)
                    self.player1_cursor[1] += 1
                    continue
            self.char1 = charnum
    # Player 2
        elif(player == PLAYER2):
            if(self.player2_cursor[1] == self.lastrow):  # Move up to a full row
                self.press(UP,1)
                self.player2_cursor[1] -= 1
            while(self.player2_cursor != pos):
                if(pos[0] < self.player2_cursor[0]):
                    self.press(PREV,1)
                    self.player2_cursor[0] -= 1
                    continue
                elif(pos[0] > self.player2_cursor[0]):
                    self.press(NEXT,1)
                    self.player2_cursor[0] += 1
                    continue

                if(pos[1] < self.player2_cursor[1]):
                    self.press(UP,1)
                    self.player2_cursor[1] -= 1
                    continue
                elif(pos[1] > self.player2_cursor[1]):
                    self.press(DOWN,1)
                    self.player2_cursor[1] += 1
                    continue
            self.char2 = charnum
        else:
            debug("Can only select character for player 1 or 2. Check your inputs for typos!")
        self.press(OK,1)    # Select the character

    # Calculate the wanted position for the cursor
    def calculate_wanted_point(self, charnum):
        col = (charnum+CHARBEFORE) % CHARCOLS
        row = math.floor((charnum+CHARBEFORE)/CHARCOLS)
        return [col,row] 

    # Presses a button n times
    def press(self, button, times=1):
        win32api.SendMessage(self.window, win32con.WM_KEYDOWN, ord(button.upper()), 1)
        sleep(HOLDTIME)
        win32api.SendMessage(self.window, win32con.WM_KEYUP, ord(button.upper()), 1)

    # Checks the select file, returns ID of last character, and writes list of chars to file if params true
    def check_characterlist(self, write_to_file = True, includepath = True):
        f = open(SELECTFILE,'r')
        lines = f.readlines()
        f.close()
        if(write_to_file):
            l = open(CHARFILE,'w', encoding="utf8", errors="ignore")
        index = 0   # Index of next character found
        for line in lines:
            if(line.strip().startswith(";")): # Commented line
                continue
            if(line.strip().startswith("[ExtraStages]")): # End of character list
                break
            if(len(line.strip()) == 0): # Empty line, no neet to process further
                continue

            # Make sure every line has the same directory syntax (Mugen accepts both \ AND /)
            line = line.replace('/', '\\')
            
            # Split the line. First part should be the directory so split that 
            parts = line.split(",")[0].strip().split("\\")
            
            charpath = CHARFOLDER
            for part in parts:
                charpath = os.path.join(charpath,part)
            
            if not charpath.endswith(".def"):
                if os.path.exists(charpath + ".def"):
                    charpath = charpath + ".def"
                else:
                    if os.path.exists(charpath + "\\" + parts[-1] + ".def"):
                        charpath = charpath + "\\" + parts[-1] + ".def"
                    else:
                        continue # Not found, proceed to next line
            elif not os.path.exists(charpath):
                continue # No such file

            print(charpath)  
            # Try opening the character file, if error, skip it and hope it doesn't break anything
            try:
                cf = open(charpath,'r', encoding="utf8", errors="replace")
                clines = cf.readlines()
                cf.close()
                charname = ""
                for cline in clines:
                    if(cline.lower().strip().startswith("displayname") or (cline.lower().strip().startswith("name") and charname == "")):
                        cparts = cline.split("=")
                        charname = cparts[1].split('"')[1].strip()
                if(includepath):
                    msg = str(index) + "," + str(charname)+","+str(charpath)+"\n"
                else:
                    msg = str(index) + "," + str(charname)+"\n"
                if(write_to_file):
                    l.write(msg)
                
                # Character successfully loaded, increment index
                index += 1
            except:
                pass
        if(write_to_file):
            l.close()
        return index - 1

    # Returns the number of winning player (1 or 2), -1 if no match has ended since last scan, 0 if draw (not sure when that would happen) 
    def scan(self):
        self.scanlines()
        if(self.state == MENU_STATE):
            self.press(OK,1)
            sleep(1)    # Ensures that mugen has time to move to a new state before next scan
        elif(self.state == SELECT_STATE):
            if(len(self.player1_chars) > 0 and len(self.player2_chars) > 0):
                self.press(OK,1) # TEAM MODE for P1 (single)
                self.select_char(self.player1_chars.pop(0),PLAYER1)
                self.press(OK,1) # TEAM MODE for P2 (single)
                self.select_char(self.player2_chars.pop(0),PLAYER2)
                self.press(OK,1) # STAGE SELECT (random)
                self.state = VS_STATE
                
        elif(self.state == FIGHT_STATE):
            pass    # Let 'em fight
        ret = self.winner
        self.winner = -1
        return ret
