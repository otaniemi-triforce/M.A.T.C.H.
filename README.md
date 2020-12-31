# M.A.T.C.H.
Mugen Automated Tournament Creator and Handler
----

Mugen Automated Tournament Creator and Handler (M.A.T.C.H.) is a system that, like the name suggests, allows automated creation and control of AI vs AI Mugen tournaments. The system has integration to several chat-platforms (Discord and Twitch at the moment) allowing users to give commands to the system remotely. The control of the system includes initializing the tournament structure and registering characters (AI Prizefighters) to the tournaments. To keep the selection from being too easy, the system generates and maintains a random offset that is applied to all choices for five tournaments (otherwise people would just automatically go for Mint or some other overpowered characters).

Why would you want to do this?
----
Well, the idea here is to give users bit more control over the streamed AI fights in Mugen and also provde them with a new challenge: Can you find and pick the best fighters of the offset roster against the other players?
Also given the division nature of the tournaments, this kind of like Mugen lottery.
If nothing else, it provides a different kind of interaction from betting on the character.

Okay how does this thing work?
----
Well, for starters you need a machine that can run Mugen, this relatively lightweight system and OBS or some other streaming system to show the fights to the user.

If you have this, then minimal installation is to:
 * Install the Mugen with some set of characters
 * Install Python 3.8.6 (at the time of the writing, discord.py has issues with Python 3.9)
 * From pip install:
    * ```ReadWriteMemory, pywin32```
    * Addionally: ```twitchio``` and/or ```discord.py```  
 *  ~~Choose whether you wish to have the plain Discord version or the more advanced Discord/Twitch Multibot-version.~~
    * The plain discord version of the system is basically deprecated at this point. 
 * Create accounts for Discord and/or Twitch bots. Instructions to these are available from those services.
 * Copy the contents of the selected version to the Mugen root
 * Modify the included config.py file. 
    * Setup the relevant account info for the bots and enable them.
    * Modify the location of the select.def to match your setup.
    * It is recommended to briefly look through the different settings in the config file and adjust either the config or MUGEN accordingly.
 * Do the adjustments to system.def described in the following section
 * After all this, you should be able to run MATCH.py and hope for the best.
 
If everything worked, the system should launch Mugen and connect the bots to defined channels. Test the system locally and then put up a stream and let people in.



system.def modifications to match mugenoperator needs
----
I order for the mugenoperator to properly work with you MUGEN installation, the system.def needs to be modified to suit its needs. Given that these modifications will break fancy designs, we suggest that you use as simple a theme as possible.

Basically the operator expects that the MUGEN menu should contain watch mode as first option. To do this, (backup and) modify the used system.def in the following manner:
 In section: ```[Title Info]``` modify the menu lines to following:
```
menu.itemname.watch = "WATCH"
menu.itemname.arcade = ""
menu.itemname.versus = ""
menu.itemname.teamarcade = ""
menu.itemname.teamversus = ""
menu.itemname.teamcoop = ""
menu.itemname.survival = ""
menu.itemname.survivalcoop = ""
menu.itemname.training = ""
menu.itemname.options = "OPTION"
menu.itemname.exit = ""
```
Second required modification in the system.def is to the ```[Select Info]``` section. This is bit more tricky as in this will probably break the visuals of the MUGEN selection screen, so some manual adjustments are probably required.

Begin by modifying the matching lines in the beginning of the section to following:
```
rows = 39   ; 37
columns = 66  ; 67
wrapping = 1              ; 1 to let cursor wrap around
pos = 1,90                ; Position to draw to
showemptyboxes = 0        ; 1 to show empty boxes
moveoveremptyboxes = 0    ; 1 to allow cursor to move over empty boxes
cell.size = 28,28         ; x,y size of each cell (in pixels)
cell.spacing = 1          ; Space between each cell
```
This will set the following required features:
   * Number of rows and columns, that the operator uses to select the character. Having any other number in these, especially in columns will cause the system to select incorrect characters
   * Allows wrapping, more predictable behavior
   * Prevents the cursor from entering empty boxes, which in turn prevents the system from getting stuck

The rest of the values basically try to fit all the 2574 boxes into 1980x1080 resolution screen and this is where you probably need to do some adjustments.
Adjusting the cell.size and cell.spacing will allow to fit more or less character boxes to the screen and pos defines the position of the first square.

The downside of all this is the system will probably look horrible without extensive editing. We are looking into releasing our modified themes to go with this or adding features to modify the selection system otherwise.


 
Some additional notes
----
Given the nature of the Mugen as "stable" platform under certain conditions (hundreds of random characters with varying quality), this system will probably crash on you. The Mugenoperator used in this system will try to get the system up again and will probably succeed. The loading time of Mugen is a problem though and having a SSD is a really good idea to reduce the loading time of the game when it crashes. 
