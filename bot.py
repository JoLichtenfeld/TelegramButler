"""Main module of the bot."""

from datetime import date, timedelta, time, datetime
from functools import wraps
from telegram import *
from telegram.ext import *
import pytz
import random
from utils import *
from camera import capture_and_transfer_image

CALENDAR_PATH = 'waste_calendar.ics'
CONFIG_PATH = 'config.yaml'
WATCHLIST_PATH = 'watchlist.yaml'


class ButlerBot:
    def __init__(self) -> None:              
        self.application = None        

        self.config = loadYAML(CONFIG_PATH)        
        self.waste_events = loadWasteEvents(CALENDAR_PATH, self.config['selected_trash_cans'])        
        self.watchlist = loadYAML(WATCHLIST_PATH)

        self.application = ApplicationBuilder().token(self.config["token"]).build()

        self.application.add_handler(CommandHandler('birthdays', self.birthdaysCommand))
        self.application.add_handler(CommandHandler('cake', self.cakeCommand))
        self.application.add_handler(CommandHandler('done', self.doneCommand))
        self.application.add_handler(CommandHandler('id', self.idCommand))
        self.application.add_handler(CommandHandler('next_birthday', self.nextBirthdayCommand))
        self.application.add_handler(CommandHandler('next_trash', self.nextTrashCommand))
        self.application.add_handler(CommandHandler('hello', self.helloCommand))
        self.application.add_handler(CommandHandler('talk', self.talkCommand))
        self.application.add_handler(CommandHandler('add_film', self.addFilmCommand))
        self.application.add_handler(CommandHandler('random_film', self.randomFilmCommand))
        self.application.add_handler(CommandHandler('list_films', self.listFilmsCommand))
        self.application.add_handler(CommandHandler('remove_film', self.removeFilmCommand))
        self.application.add_handler(CommandHandler('picture', self.pictureCommand))
        
        # send start message to maintainer
        self.application.job_queue.run_once(self.sendStartMsg, when=5, chat_id=self.config["maintainer_chat_id"])

        # daily check for trash cans
        trash_check_time = toTime(self.config["trash_msg_time"]).replace(tzinfo=pytz.timezone('Europe/Amsterdam')) # place your local timezone here
        snooze_time = toTimeDelta(self.config["snooze_time"])
        trash_reminder1_time = datetime.combine(date.today(), trash_check_time) + snooze_time
        trash_reminder2_time = datetime.combine(date.today(), trash_check_time) + snooze_time * 2
        
        self.application.job_queue.run_daily(self.dailyTrashCheck, time=trash_check_time, chat_id=self.config["group_chat_id"], name="dailyTrashCheck") 
        self.application.job_queue.run_daily(self.reminder, time=trash_reminder1_time, chat_id=self.config["group_chat_id"], name="reminder1")
        self.application.job_queue.run_daily(self.reminder, time=trash_reminder2_time, chat_id=self.config["group_chat_id"], name="reminder2")                

        # reset flag in case nobody handled the notification
        self.application.job_queue.run_daily(self.disable, time=toTime("10:00:00").replace(tzinfo=pytz.timezone('Europe/Amsterdam')))

        # daily birthday check: runs every day at the specified time and checks if today is the birthday of anyone
        bday_check_time = toTime(self.config["birthday_msg_time"]).replace(tzinfo=pytz.timezone('Europe/Amsterdam'))
        self.application.job_queue.run_daily(self.dailyBirthdayCheck, time=bday_check_time, chat_id=self.config["group_chat_id"])
    

    async def dailyBirthdayCheck(self, context: CallbackContext) -> None:
        """Checks if today is the birthday of anyone"""
        for name, date_str in self.config["birthdays"].items():
            print("Checking birthday of " + name)
            date = toDate(date_str)
            today = datetime.now().date()
            if date.day == today.day and date.month == today.month:
                print("Happy Birthday, " + name + "!")
                notification = "Happy Birthday, " + name + "! " + getRandomAnimalEmoji()
                await context.bot.send_message(chat_id=context._chat_id, text=notification)


    async def sendStartMsg(self, context: CallbackContext) -> None:
        """Inform the maintainer at startup"""
        notification = "bot started"
        await context.bot.send_message(chat_id=context._chat_id, text=notification)


    # TODO!
    async def send_typing_action(func):
        """Send typing action while processing func command."""
        # Taken from https://stackoverflow.com/questions/61520440/pretending-that-telegram-bot-is-typing

        @wraps(func)
        async def command_func(self, update, context, *args, **kwargs):
            await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=constants.ChatAction.TYPING)            
            return func(self, update, context, *args, **kwargs)
        
        return command_func


    async def verifyMessage(self, update: Update, context: ContextTypes.DEFAULT_TYPE, maintainer_only = False, group_only = True, members_only = True, private_chat_only = False, empty_msg_allowed = True) -> bool:
        """Verifiy that the message is sent by a valid user in the specified chat."""                 

        if group_only and private_chat_only:
            raise ValueError("Both group_only and private_chat_only flags cannot be set to True at the same time.")

        # Skip updates that were issued when bot was down
        # Otherwise, after a restart, the bot would handle all messages that were sent in the meantime
        then = update.message.date
        now = datetime.now(pytz.timezone('Europe/Berlin'))        
        if now - then > timedelta(seconds=5):
            return False      
        
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        if maintainer_only and chat_id != self.config['maintainer_chat_id']:
            return False

        if group_only and chat_id != self.config['group_chat_id']:
            return False
        
        if members_only and user_id not in self.config['member_ids']:
            return False
        
        # Only group chats have negative chat ids
        if private_chat_only and chat_id < 0:
            return False
        
        if not empty_msg_allowed and not context.args:
            return False
        
        return True


    def startBot(self) -> None:
        """Start polling."""
        self.application.run_polling()


    def checkTrash(self) -> str:
        """Return the trash can due next day, if any, else None."""  
        # Notify maintainer if the calendar has reached its end
        if list(self.waste_events)[-1] == date.today():            
            self.notifyMaintainer("End of calendar reached!")

        tomorrow = date.today() + timedelta(days=1)
        if not tomorrow in self.waste_events.keys():
            return None
        
        return self.waste_events[tomorrow]


    async def notifyMaintainer(self, msg: str) -> None:
        """Send a private message to the maintainer."""
        await self.application.bot.send_message(chat_id=self.config["maintainer_chat_id"], text=msg)


    async def birthdaysCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """List all stored birthdays with name and date."""
        if not await self.verifyMessage(update, context, group_only=False):
            return
        
        text = ""
        for name, bday in self.config["birthdays"].items():
            text += '\n' + name + "  " + bday
        if text:
            text = "All birthdays:" + text
        else:
            text = "No entries found."
        await context.bot.send_message(chat_id=context._chat_id, text=text, parse_mode=constants.ParseMode.HTML)


    async def cakeCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Pick a random group memmber that has to bake the next cake."""
        if not await self.verifyMessage(update, context, group_only=False):
            return
        
        candidates = list(self.config['birthdays'].keys())
        text = "🍰 The next cake will be baked by " + random.choice(candidates) + "!"
        await context.bot.send_message(chat_id=context._chat_id, text=text)


    async def doneCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Disable the trash reminders."""
        if not await self.verifyMessage(update, context, group_only=True):
            return        
        
        if not self.config["waiting_for_disable"]:
            return
                
        msg = "Thanks, " + update.effective_user.first_name + "!"
        await context.bot.send_message(chat_id=context._chat_id, text=msg)

        self.config["waiting_for_disable"] = False
        saveYAML(CONFIG_PATH, self.config)


    async def idCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message containing the chat id."""
        if not await self.verifyMessage(update, context, group_only=False, members_only=False):
            return
        
        msg = "This chat's ID is: " + str(update.effective_chat.id) + " " + getRandomAnimalEmoji() + '\n'
        msg += "Your ID is: " + str(update.effective_user.id) + " " + getRandomAnimalEmoji() + '\n'
        msg += "Your name is: " + update.effective_user.first_name + " " + getRandomAnimalEmoji()
        await update.message.reply_text(msg)


    async def nextBirthdayCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Tell the name and date of the next birthday event."""
        if not await self.verifyMessage(update, context, group_only=False):
            return

        bdays = self.config["birthdays"]

        # find next birthday
        next_name = None
        next_bday = None
        min_days_remaining = 444
        today = datetime.now()
        for name, birthday in bdays.items():
            birthday = toDate(birthday)
            delta1 = datetime(today.year, birthday.month, birthday.day)
            delta2 = datetime(today.year+1, birthday.month, birthday.day)
            days_til_this_bday = ((delta1 if delta1 > today else delta2) - today).days
            if days_til_this_bday < min_days_remaining:
                next_bday = birthday
                next_name = name
                min_days_remaining = days_til_this_bday

        text = "Next birthday: <b>" + next_name + "</b> at <b> " + next_bday.strftime("%d.%m.") + " </b>" + getRandomAnimalEmoji()
        await context.bot.send_message(chat_id=context._chat_id, text=text, parse_mode=constants.ParseMode.HTML)


    async def nextTrashCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send the name and date of the next due trash can as a message."""
        if not await self.verifyMessage(update, context, group_only=False):
            return

        next_dates = [event for event in list(self.waste_events) if event > date.today()]

        if not next_dates:
            text = "No more trash events found! Is the calendar up to date?"
            await context.bot.send_message(chat_id=context._chat_id, text=text)
            return       
         
        next_date = next_dates[0]        
        can = self.config["ics_trash_cans"][self.waste_events[next_date]]
        when = next_date

        text = "Nächste Mülltonne: <b>" + can + " </b>am <b>" + toGermanWeekday(when) + "</b> Morgen, " + when.strftime("%d.%m.")
        await context.bot.send_message(chat_id=context._chat_id, text=text, parse_mode=constants.ParseMode.HTML)


    async def helloCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a hello message."""
        if not await self.verifyMessage(update, context, group_only=False):
            return
        msg = "Hello there! " + getRandomAnimalEmoji()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


    async def talkCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Talk to the group anonymously."""
        if not await self.verifyMessage(update, context, group_only=False, private_chat_only=True, empty_msg_allowed=False):
            return        
        
        text = " ".join(context.args)
        await context.bot.send_message(chat_id=self.config["group_chat_id"], text=text)

    
    async def addFilmCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Add a film to the watchlist."""
        if not await self.verifyMessage(update, context, group_only=False):
            return
        
        if not context.args:
            text = "Usage: /add_film [film title]"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            return        
        
        film = " ".join(context.args)
        if film in self.watchlist["films"]:
            text = "Film \"" + film + "\" already in watchlist!"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            return
        
        self.watchlist["films"].append(film)
        saveYAML(WATCHLIST_PATH, self.watchlist)

        text = "Added film \"" + film + "\" to the watchlist"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


    async def randomFilmCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Pick a random film."""
        if not await self.verifyMessage(update, context, group_only=False):
            return

        if not self.watchlist["films"]:
            text = "No films on watchlist :("
        else:
            text = random.choice(self.watchlist["films"])
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


    async def listFilmsCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """List all films in watchlist."""
        if not await self.verifyMessage(update, context, group_only=False):
            return

        if not self.watchlist["films"]:
            text = "---Empty---"
        else:
            text = "\n".join(self.watchlist["films"])
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


    async def removeFilmCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Remove a film from the watchlist."""
        if not await self.verifyMessage(update, context, group_only=False):
            return

        if not context.args:
            text = "Usage: /remove_film [film title]"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            return
        
        film = " ".join(context.args)
        if not film in self.watchlist["films"]:
            text = "Film \"" + film + "\" not in watchlist! Spelling correct?"
        else:
            self.watchlist["films"].remove(film)
            saveYAML(WATCHLIST_PATH, self.watchlist)
            text = "Removed \"" + film + "\" from watchlist"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    async def pictureCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a picture from the camera."""
        if not await self.verifyMessage(update, context, group_only=False, members_only=True):
            return
        
        self.last_picture_command = datetime.now()

        wait_msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="Capturing image...")

        status, status_msg = capture_and_transfer_image(self.config["camera_user"], self.config["camera_ip"], self.config["camera_remote_path"], self.config["camera_local_path"])
        if status != 0:
            text = "Error capturing image: " + status_msg
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            return

        # Delete the last message sent by the bot
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=wait_msg.message_id)

        # Send the image
        img_path = status_msg
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(img_path, 'rb'))


    async def dailyTrashCheck(self, context: CallbackContext) -> None:
        """Check the trash calendar and sends a message if an event for the next day is found."""
        current_trash_can = self.checkTrash()
        if not current_trash_can:
            print("No trash can found for tomorrow.") 
            return

        notification = "Heute Abend bitte rausstellen: " + self.config["ics_trash_cans"][current_trash_can] + getRandomAnimalEmoji()
        await context.bot.send_message(chat_id=context._chat_id, text=notification)
        self.config["waiting_for_disable"] = True
        saveYAML(CONFIG_PATH, self.config)


    async def reminder(self, context: CallbackContext) -> None:
        """Check if task was fullfilled in the meantime, sends reminder if not."""
        if not self.config["waiting_for_disable"]:
            return
        
        text = "Kleine Erinnerung"
        await context.bot.send_message(chat_id=context._chat_id, text=text)       


    async def disable(self, context: CallbackContext) -> None:
        """Unset the flag."""
        self.config["waiting_for_disable"] = False
        saveYAML(CONFIG_PATH, self.config)


def main():
    sir_james_bot = ButlerBot()
    sir_james_bot.startBot()


if __name__ == '__main__':
    main()     
