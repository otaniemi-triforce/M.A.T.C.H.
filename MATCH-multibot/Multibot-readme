M.A.T.C.H. multibot: The state of the art of...M.A.T.C.H. I suppose.

This version is more sensible than the initial Discord only version and need for it arose from requests to have Twitch chatbot as well.
Sure, so I rewrote the thing to make the MATCH more centralized controller of message flow. The new MATCH allows multiple bots to send requests to the system and in turn passes messages regarding system changes to all tied bots.

Not only does this allow the system to interact with Discord and Twitch at the same time, but with any chatbot that runs on python and can be modified to do the following:
 * Send messages from some kind of non-blocking queue (collect messages and send them as soon as other tasks permit)
 * Do the initial sanity checks on the user commands. This might be improved in the future to be part of the main MATCH functionalities.
Adding bots to the system is not really dynamic at the moment and will require you to get your hands slightly dirty in process (something that I may improve in the future as well).
At the same time it is not overly complicated either so you'll probably manage by looking how stupidly it's done at the moment.

And...well that's about it. This is pretty simple system at the moment.

- Yarbarb
