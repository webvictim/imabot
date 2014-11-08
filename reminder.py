"""
reminder.py - Willie Reminder Module
Modifications by webvictim <webvictim@gmail.com>
Further Modifications by jcrza
"""

import os
import re
import time
import threading
import codecs
from datetime import datetime
from willie import module, web

def filename(self):
    name = self.nick + '-' + self.config.user + '.reminders.db'
    return os.path.join(self.config.dotdir, name)

def load_database(name):
    data = {}
    if os.path.isfile(name):
        f = codecs.open(name, 'r', encoding='utf-8')
        for line in f:
            db_key, unixtime, channel, nick, message = line.split('\t')
            message = message.rstrip('\n')
            reminder = (unixtime, channel, nick, message)
            try:
                data[db_key].append(reminder)
            except KeyError:
                data[db_key] = [reminder]
        f.close()
    return data

def dump_database(name, data):
    f = codecs.open(name, 'w', encoding='utf-8')
    try:
        for db_key, reminders in data.iteritems():
            for unixtime, channel, nick, message in reminders:
                f.write('%s\t%s\t%s\t%s\t%s\n' % (nick, unixtime, channel, nick, message))
        f.close()
    except RuntimeError:
        pass

def setup(bot):
    bot.rfn = filename(bot)
    bot.rdb = load_database(bot.rfn)

@module.rule('^(?!\!remind$).*')
def reminder_check(bot, trigger):
    """Runs on every incoming message to see whether we have any reminders to give to the given nickname."""
    db_keys = [key for key in bot.rdb]
    if db_keys:
        if trigger.nick in sorted(db_keys):
            for (unixtime, channel, nick, message) in bot.rdb[trigger.nick]:
                # rewrite the sender if it's yourself
                if nick == trigger.nick:
                    nick = 'you'
                # send the reminder message to whatever channel the person spoke in
                bot.msg(trigger.sender, "%s, %s asked me to remind you: %s" % (trigger.nick, nick, message))
            del bot.rdb[trigger.nick]
            dump_database(bot.rfn, bot.rdb)

@module.rule("!remind$")
@module.rule("!remind ([\S,]+)\ (.*)")
def remind(bot, trigger):
    """Gives the given nick a reminder next time they speak."""
    try:
        target_nick = trigger.group(1)
        message = trigger.group(2)
    except IndexError:
        return bot.reply("Syntax: !remind <nick>[,<nick>...] <message>")

    if target_nick == "me":
        target_nick = trigger.nick; 

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
        unixtime = int(time.time())
        reminder = (unixtime, trigger.sender, trigger.nick, message)
        try:
            bot.rdb[nick_to_remind].append(reminder)
        except KeyError:
            bot.rdb[nick_to_remind] = [reminder]

        reminder_counter += 1
        dump_database(bot.rfn, bot.rdb)

    if reminder_counter > 1:
        bot.reply("%s reminders remembered." % reminder_counter)
    else:
        bot.reply('Reminder remembered.')
