"""
reminder.py - Willie Reminder Module
Modifications by webvictim <webvictim@gmail.com>
"""

import os
import re
import pickle
import time
from datetime import datetime
from willie import module, web

# list of ignored nicks
ignored_nicks = ['mcbot']

def filename(self):
    name = self.nick + '-' + self.config.user + '.reminders-pickle.db'
    return os.path.join(self.config.dotdir, name)

def load_database(name):
    try:
        return pickle.load(open(name, "rb"))
    except IOError:
        return {}

def dump_database(name, data):
    pickle.dump(data, open(name, "wb"))

def setup(bot):
    bot.fn = filename(bot)
    bot.rdb = load_database(bot.fn)

# this is pretty inefficient as it runs through the entire list once for
# every message that gets sent to any channel that the bot is part of
# better way would be to make the reminders keyed on nick and just check that
@module.rule('^(?!@remind|!remind).*')
#@module.rule('.*')
def reminder_check(bot, trigger):
    check_nick = trigger.nick.lower()
    if (trigger.nick in ignored_nicks):
        return
    """Runs on every incoming message to see whether we have any reminders to give to the given nickname."""
    had_reminder = False
    if bot.rdb.has_key(check_nick):
        for reminder in bot.rdb[check_nick]:
            had_reminder = True
            if reminder['from'].lower() == check_nick:
                reminder['from'] = 'you'
            bot.msg(trigger.sender, "%s, %s asked me to remind you: %s" % (trigger.nick, reminder['from'], reminder['message']))
    if had_reminder:
        discard = bot.rdb.pop(trigger.nick, None)
    dump_database(bot.fn, bot.rdb)

@module.rule("!remind$")
@module.rule("!remind ([\S,]+)\ (.*)")
def remind(bot, trigger):
    if "#" not in trigger.sender:
        bot.msg(trigger.sender, "Only works in channels, dickface.")
        return

    """Gives the given nick a reminder next time they speak."""
    try:
        target_nick = trigger.group(1)
        message = trigger.group(2)
    except IndexError:
        return bot.reply("Syntax: !remind <nick>[,<nick>...] <message>")

    if target_nick == "me":
        target_nick = trigger.nick 

    if "," in target_nick:
        # skip blank values (this usually happens when called like 
        # !remind nick1, nick2 rather than !remind nick1,nick2)
        target_nicks = filter(None, target_nick.split(","))
    else:
        target_nicks = [target_nick]

    create_reminder(bot, trigger, target_nicks, message)

def create_reminder(bot, trigger, target_nick_list, message):
    reminder_counter = 0
    # built-in deduplication
    for nick_to_remind in list(set(target_nick_list)):
        lowercase_nick = nick_to_remind.lower()
        data = {'time': int(time.time() * 1000), 'channel': trigger.sender, 'from': trigger.nick, 'to': nick_to_remind, 'message': message }
        try:
            bot.rdb[lowercase_nick].append(data)
        except KeyError:
            bot.rdb[lowercase_nick] = [data]

        reminder_counter += 1
    dump_database(bot.fn, bot.rdb)

    if reminder_counter > 1:
        bot.reply("%s reminders remembered." % reminder_counter)
    else:
        bot.reply('Reminder remembered.')
