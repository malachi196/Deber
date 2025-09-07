# deber's api: a tutorial
This is a guide to ALL of the commands in DEBER! \
(note: the command prefix is "$")
### commands
+ `strike <user>`: give a user 1 strike (3 strikes = timout)
+ `strike_count <user>`: obtain the number of strikes a user has
+ `builduserfile`: scrape all of the users from discord
+ `rebuildmeta`: parses the scraped users and registers any unknown users
+ `realname <user>`: fetch a user's irl name (if registered)
+ `debermessage <channel>`: used for official messages and stuff(though you may have to edit deber source code for your usage)
+ `watch_reactions <channel> <msgid>`: infinitely check for either adding or removing reactions|n the specified message!
+ `stop_rwatch`: stops checking for reactions on the set message (if any)
+ `deber <args>`: deber system console
### slash commands
+ `/online`: lists the users who are online in masworld (used for nonadmin)