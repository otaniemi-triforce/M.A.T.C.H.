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
    * Modify the character columns and slots before them to match your setup.
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

Character grid
----
The mugenoperator assumes that all your characters are in a rectangular grid with no empty spaces in it. To ensure this, make sure your select.def isn't inserting any empty cells, and set showemptyboxes off in the system.def in the ```[Select Info]``` section.


Tournament logic and scoring
----
Each tournament consists of 1 to N divisions. Each registered player submits one character to each of these divisions.
Divisions are played as single eliminations and players gain points based on how many rounds their chosen character advances in each division. At the end of the tournament, the player scores form each of the divisions is summed up to give final score.

Each character ID is offset by a random number that is in effect for 5 tournaments and then new offset is randomized (this value can be adjusted via config). This offset mechanism is in place as the system was initally designed to be used with several thousand characters with severe balance issues and it makes finding the overpowered characters more challenging. We might add option to disable this at later point, so at this point setting this to very high number will basically disable the system as players will easily learn which values to use to defeat the system(*).

Some examples:

Creating tournament with 1 divisions -> This is what most consider to be a typical single elimination tournament. Each player registers 1 character, each character fights at least once. With eight players, this means 7 matches will be played. 

Creating tournament with 5 divisions -> This will create a tournament with 5 divisions. Each player registers 5 individual characters that will fight in their respective divisions. With eight players, this means 7 * 5 = 35 matches will be played.


From the above examples one can easily see that tournament with several divisions can take considerable time...especially so if you have many players.


(*) With 2500 characters, we could figure out the offset value with reasonable accuracy within 3-4 tournaments if we put our minds to it. 


Using the Discord bot
----
After the system is started, the Discord bot will connect to designated channel and will accept commands from users.

All commands are passed as mentions to the bot.

 ``<@botname> new tournament: <divisions>``
 
  Command generates a new tournament with given number of divisions.
  
 ``<@botname> register: <Character ID div 1, Character ID div 2,...,Character ID div N>``
 
  Command registers user into created tournament with given character ID's. If duplicate registrations are allowed in config, user can submit several registrations (useful in testing). At this point, the system prevents duplicate character ID's to be registered.

When at least two characters are registered via either of the used bots, the tournament start timers are activated. During the startup period, registrations from users are accepted. After the timers reach zero, tournament is automatically launched and registration closes.

Discord status of the bot indicates the state the bot is in:
 * When registering for tournament, status should tell how many divisions are in use
 * When tournament is running, the current match status should be displayed
There is usually some delay in the status updates.

At the end of each division and the tournament, the bot sends standings as a message to the channel.

Using the Twitch bot
----
Very similar to the Discord version.

Accepted commands:

``!new tournament: <divisions>``

 Command generates a new tournament with given number of divisions.
 
``!register: <Char ID div 1, Char ID div 2,...,Char ID div N>``

 Command registers user into created tournament with given character ID's. If duplicate registrations are allowed in config, user can submit several registrations (useful in testing). At this point, the system prevents duplicate character ID's to be registered.

When at least two characters are registered via either of the used bots, the tournament start timers are activated. During the startup period, registrations from users are accepted. After the timers reach zero, tournament is automatically launched and registration closes.

The twitch bot does not report results or status, as it is assumed that this information is conveyed via the stream. To help with this, the system writes the current match and results into a simple dynamic HTML file, that can be included in the stream. This is explained in more detail in the next chapter.

HTML status/score file
----
The M.A.T.C.H. outputs match data and scores to two simple, auto-updating HTML-files: ``results.html`` and ``info.html``. These are intented to be used with OBS to present data about the ongoing match and scores, but can be used for other purposes as well. The style of the HTML-files can be modified via included ``style.css`` file.
Currently, support for easily modifying the creation, content or the location of this file is very limited as this has not been very high priority functionality. We may look into improving this later.


TODO / Caveats
----
In it's current state, the system has many quirks/issues/'features' that could use improvement in the future:
  * Neither of the bots offer assistance in their use. (This is a real headscratcher, what were we thinking 8 or months ago?) 
  * There is no way to reset/undo/cancel any of the functions via bots or any other way (apart from system reset). This includes: 
     * Once registration is started, there is no going back
     * Registration is permanent action, until tournament has finished
     * Once started, the tournament can't be stopped
  * The above limitation is due to the fact that there is no admin system or other user classification. The system was designed to be autonomous and to be as simple as possible. This is not ideal in other use cases and it is not ideal in our use case either, as it takes one clever user to render the system basically inoperable (new tournament: 15 or more should do the trick)
  * Based on our experience, the system is not fully autonomous even when this was the design goal. Mugen has tendency to cause trouble in a way that is hard to detect via automation, which in turn means that someone needs to be watching the system when it is operating anyway.
  * OBS browser has issues with the HTML-file occasionally. This seems to be more of a OBS problem, as the tricks used to make it dynamic are basic HTML.
  * In the future, this system could be turned fully automatic tournament machine without any user input. Probably not very difficult to do, so might as well implement that as well

There are probably N other things that are bit wonky. Just can't remember them at this point.

Some additional notes
----
Given the nature of the Mugen as "stable" platform under certain conditions (hundreds of random characters with varying quality), this system will probably crash on you. The Mugenoperator used in this system will try to get the system up again and will probably succeed (maybe, hopefully). The loading time of Mugen is a problem though and having a SSD is a really good idea to reduce the loading time of the game when it crashes. 
