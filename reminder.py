"""
reminder.py - Willie Reminder Module
Modifications by webvictim <webvictim@gmail.com>
"""

import os
import re
import time
import threading
import codecs
from datetime import datetime
from willie import module, web

def filename(self):
    name = self.nick + '-' + self.config.host + '.reminders.db'
    return os.path.join(self.config.dotdir, name)

def load_database(name):
    data = {}
    if os.path.isfile(name):
        f = codecs.open(name, 'r', encoding='utf-8')
        for line in f:
            unixtime, channel, nick, target_nick, message = line.split('\t')
            message = message.rstrip('\n')
            t = int(float(unixtime))  # WTFs going on here?
            reminder = (channel, nick, target_nick, message)
            try:
                data[t].append(reminder)
            except KeyError:
                data[t] = [reminder]
        f.close()
    return data

def dump_database(name, data):
    f = codecs.open(name, 'w', encoding='utf-8')
    try:
        for unixtime, reminders in data.iteritems():
            for channel, nick, target_nick, message in reminders:
                f.write('{0}\t{1}\t{2}\t{3}\t{4}\n'.format(unixtime, channel, nick, target_nick, message))
        f.close()
    except RuntimeError:
        pass

def setup(bot):
    bot.rfn = filename(bot)
    bot.rdb = load_database(bot.rfn)

# this is pretty inefficient as it runs through the entire list once for
# every message that gets sent to any channel that the bot is part of
# better way would be to make the reminders keyed on nick and just check that
@module.rule('.*')
def reminder_check(bot, trigger):
    """Runs on every incoming message to see whether we have any reminders to give to the given nickname."""
    unixtimes = [int(key) for key in bot.rdb]
    if unixtimes:
        for unixtime in unixtimes:
            for (channel, nick, target_nick, message) in bot.rdb[unixtime]:
                # does this nick have any reminders?
                if (target_nick == trigger.nick):
                    # rewrite the sender if it's yourself
                    if nick == target_nick:
                        nick = 'you'
                    # send the reminder message to whatever channel the person spoke in
                    bot.msg(trigger.sender, "{0}, {1} asked me to remind you: {2}".format(target_nick, nick, message))
                    del bot.rdb[unixtime]
        dump_database(bot.rfn, bot.rdb)

#def remind_help(bot, trigger):
#    return bot.say("Syntax: !remind <nick> <message>")

@module.rule("!remind$")
@module.rule("!remind ([\S]+)\ (.*)")
@module.rule("remind (me)\ (.*)")
def remind(bot, trigger):
    """Gives the given nick a reminder next time they speak."""
    try:
        target_nick = trigger.group(1)
        message = trigger.group(2)
    except IndexError:
        return bot.reply("Syntax: !remind <nick> <message>")

    if target_nick == "me":
        target_nick = trigger.nick; 
    
    create_reminder(bot, trigger, target_nick, message)

def create_reminder(bot, trigger, target_nick, message):
    t = int(time.time())
    reminder = (trigger.sender, trigger.nick, target_nick, message)
    try:
        bot.rdb[t].append(reminder)
    except KeyError:
        bot.rdb[t] = [reminder]

    dump_database(bot.rfn, bot.rdb)
    bot.reply('Reminder remembered.')
