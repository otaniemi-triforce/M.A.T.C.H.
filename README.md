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
 * Install python3
 * From pip install:
    * twitchio, discord.py - depending on what kind of bots you want
 * Download this system along with Mugenoperator from MUGEN-tournament (https://github.com/otaniemi-triforce/MUGEN-tournament)
 * Choose whether you wish to have the plain Discord version or the more advanced Discord/Twitch Multibot-version.
 * Create accounts for Discord/Twitch bots. Instructions to these are available from those services.
 * Copy the contents of the selected version to the Mugen root and setup the account info to config.py (directly to the MATCH in Discord option)
 * Run MATCH.py and hope for the best
 
 * If everything worked, the system should launch Mugen and connect the bots to defined channels.
 * Test the system locally and then put up a stream and let people in.
 
 Notice: Given the nature of the Mugen as "stable" platform under certain conditions (hundreds of random characters with varying quality), this system will probably crash on you. The Mugenoperator used in this system will try to get the system up again and will probably succeed. The loading time of Mugen is a problem though and having a SSD is a really good idea to reduce the loading time of the game when it crashes. 
