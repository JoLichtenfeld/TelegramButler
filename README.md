# TelegramButler
Invite this butler to your flat share's / family's telegram group and it will assist you with your daily tasks!

#### Trash reminder
Every day at a specified time, it will check the ics calendar file provided by the public services.
If a trash can is due the next morning, it will send a notification in the group. After taking out the trash, just text ```\done```.
Otherwise, the bot will remind you later.

#### Birthday reminder
Never forget another group member's birthday again! A cheers will be posted at the very day.
```\all_birthdays``` lists all stored birthdays.

#### Movie watchlist
Saturday night and you don't know which film to watch? Just tell the Butler all your ideas and then pick one later.
```\add_film```
```\remove_film```
```\random_film```
```\list_films```

#### Talk anonymously
Don't want to blame your roomies in person for not cleaning the bath? Let the Butler do the job anonymously! Just tell it in a private chat and it will be reposted in the group chat.
```\talk bla bla bla```

#### Cake
Let the bot decide who has to bake a cake! ```\cake```

## How to
This script needs to run 24/7. A raspberry pi is a energy-saving solution for this purpose.

Follow [this](https://core.telegram.org/bots/tutorial) tutorial on how to create a new bot.

Copy the ```example_config.yaml``` and rename it to ```config.yaml```. Adapt it to your needs: Fill in the bot token, names and birthdates in the given format, also adjust the notification times etc.

Add an iCalendar file and call it ```waste_calendar.ics```.

Finally, run ```bot.py```.

For auto-completion of the telegram commands do the following:
- Text ```/setcommands``` to the *BotFather* bot
- Select this bot
- Send the following text:
```hello - Say hello
birthdays - List all registered birthdays
cake - Whose turn is it to bake the next cake?
done - Disable the current reminder
next_birthday - Whose birthday is next?
next_trash - When is the next trash can due?
talk - Tell me something in a private chat, and I'll forward it anonymously to everyone!
add_film - Add a film to our watchlist
random_film - It does what you think it does...
list_films - Lists the entire watchlist
remove_film - Removes the respective film from the watchlist```

