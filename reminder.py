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
    name = self.nick + '-' + self.config.user + '.reminders.db'
    return os.path.join(self.config.dotdir, name)

def load_database(name):
    data = {}
    if os.path.isfile(name):
        f = codecs.open(name, 'r', encoding='utf-8')
        for line in f:
            db_key, unixtime, channel, nick, target_nick, message = line.split('\t')
            message = message.rstrip('\n')
            #t = int(float(unixtime))  # WTFs going on here?
            reminder = (channel, nick, target_nick, message)
            try:
                #data[t].append(reminder)
                data[db_key].append(reminder)
            except KeyError:
                #data[t] = [reminder]
                data[db_key] = [reminder]
        f.close()
    return data

def dump_database(name, data):
    f = codecs.open(name, 'w', encoding='utf-8')
    try:
        for db_key, reminders in data.iteritems():
            for unixtime, channel, nick, target_nick, message in reminders:
                #f.write('{0}\t{1}\t{2}\t{3}\t{4}\n'.format(unixtime, channel, nick, target_nick, message))
                db_key = "_".join([str(unixtime), str(channel), str(nick), str(target_nick)])
                f.write('%s\t%s\t%s\t%s\t%s\t%s\n' % (db_key, unixtime, channel, nick, target_nick, message))

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
    #unixtimes = [int(key) for key in bot.rdb]
    db_keys = [key for key in bot.rdb]
    if db_keys:
        for db_key in sorted(db_keys):
            for (unixtime, channel, nick, target_nick, message) in bot.rdb[db_key]:
                # does this nick have any reminders?
                if (target_nick == trigger.nick):
                    # rewrite the sender if it's yourself
                    if nick == target_nick:
                        nick = 'you'
                    # send the reminder message to whatever channel the person spoke in
                    #bot.msg(trigger.sender, "{0}, {1} asked me to remind you: {2}".format(target_nick, nick, message))
                    bot.msg(trigger.sender, "%s, %s asked me to remind you: %s" % (target_nick, nick, message))
                    del bot.rdb[db_key]
        dump_database(bot.rfn, bot.rdb)

@module.rule("!remind$")
@module.rule("!remind ([\S,]+)\ (.*)")
#@module.rule("remind (me)\ (.*)")
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
        db_key = '_'.join([str(unixtime), str(trigger.sender), str(trigger.nick), str(nick_to_remind)])
        reminder = (unixtime, trigger.sender, trigger.nick, nick_to_remind, message)
        try:
            bot.rdb[db_key].append(reminder)
        except KeyError:
            bot.rdb[db_key] = [reminder]

        reminder_counter += 1
        dump_database(bot.rfn, bot.rdb)

    if reminder_counter > 1:
        bot.reply("%s reminders remembered." % reminder_counter)
    else:
        bot.reply('Reminder remembered.')

