"""
kickvote.py - Willie Democracy Module
Written by webvictim <webvictim@gmail.com>
"""

import os
from willie import module, web, tools

votes = {}
vote_threshold = 3
ban_duration = "1h"

kick_bot = "ChanServ"
kick_command = "BAN {0} +{3} {1} You were democratically kickvoted by {2}!"

# whitelisted channels that the bot can run in
kickvote_whitelist = ['#random','#gus','#general']

#@module.rule('!votekick (\S+)')
#@module.rule('!vk (\S+)')
@module.rule('!kickvote (\S+)')
@module.rule('!kv (\S+)')
def process_vote(bot, trigger):
    """Processes a vote for a person and acts on it if necessary."""
    vote_nick = trigger.group(1)

    # don't run unless this is in a channel
    if '#' not in trigger.sender:
        return

    channel = trigger.sender
    if channel not in kickvote_whitelist:
        return

    # find the nick of the person being voted for on the channel
    if vote_nick in bot.privileges[channel].keys():
        vote_nick = vote_nick.lower()
        if (has_voted_for(channel, trigger.nick, vote_nick)):
            bot.reply("You've already voted against {0}.".format(vote_nick))
            return
        else:
            if add_vote(channel, trigger.nick, vote_nick):
                bot.reply("Vote for {0} registered.".format(vote_nick))
            else:
                bot.say("Something went wrong. Whoops!")
                
        # count all votes to check if we need to kick
        vote_counts = get_vote_counts(channel)
        if (vote_counts is not None):
            for (nick, actual_vote_count) in vote_counts.iteritems():
                if (actual_vote_count >= vote_threshold):
                    kick_voters = format_voter_list_for_kick(who_voted_for(channel, nick))
                    bot.say("{0}, you are the weakest link. Goodbye!".format(nick))
                    # do actual kick here
                    bot.msg(kick_bot, kick_command.format(channel, nick, kick_voters, ban_duration))
                    remove_all_votes_for(channel, nick)
    else:
        bot.reply("I can't find {0} on the channel.".format(vote_nick))

@module.rule('^!kickvote$')
@module.rule('^!kv$')
def kickvote_info(bot, trigger):
    bot.say("Syntax: !kickvote <nick> or !kv <nick> - registers a vote to kick a given nick from the channel. If that nick receives {0} votes in total, they will be banned from the channel for {1}. You can remove a vote with !unkickvote <nick> or !ukv <nick>. !kickvotestatus shows current vote counts.".format(vote_threshold, ban_duration))

#@module.rule('!unvotekick (\S+)')
#@module.rule('!uvk (\S+)')
@module.rule('!unkickvote (\S+)')
@module.rule('!ukv (\S+)')
def process_unvote(bot, trigger):
    """Processes an unvote for a person and acts on it if necessary."""
    # don't run unless this is in a channel
    if '#' not in trigger.sender:
        return
    
    channel = trigger.sender
    if channel not in kickvote_whitelist:
        return
    vote_nick = trigger.group(1)

    # find the nick of the person being voted for on the channel
    if vote_nick in bot.privileges[channel].keys():
        vote_nick = vote_nick.lower()
        if remove_vote(channel, trigger.nick, vote_nick):
            bot.reply("Vote unregistered.")
        else:
            bot.reply("You haven't voted for {0}.".format(vote_nick))
    else:
        bot.reply("I can't find {0} on the channel.".format(vote_nick))

@module.rule('!votestatus')
@module.rule('!kickvotestatus')
#@module.rule('!votekickstatus')
#@#module.rule('!kvstatus')
#@module.rule('!vkstatus')
#@module.rule('!vks')
#@module.rule('!kvs')
#@module.rule('!vs')
#@module.rule('!ks')
def votestatus(bot, trigger):
    if '#' not in trigger.sender:
        return
    channel = trigger.sender
    if channel not in kickvote_whitelist:
        return

    """Format a nice listing of all the current votes and display it."""
    replies = []
    vote_counts = get_vote_counts(channel)
    if (vote_counts) is not None:
        for (nick, actual_vote_count) in vote_counts.iteritems():
            voter_list = who_voted_for(channel, nick)
            replies.append("{0}: {1} ({2})".format(nick, actual_vote_count, ", ".join(sorted(voter_list)))) 
        bot.say("Vote status - {0}".format(", ".join(replies)))
    else:
        bot.say("All is calm.")

@module.event('NICK')
@module.rule('.*')
# this is most definitely not thread safe
@module.thread(False)
@module.unblockable
def nick_tracker(bot, trigger):
    """Track and process nick changes."""
    channel = trigger.sender
    if channel not in kickvote_whitelist:
        return
    old_nick = trigger.nick.lower()
    new_nick = tools.Nick(trigger).lower()
    counts = replace_votes(channel, old_nick, new_nick)
    print "{0} renicked to {1} on {2} - votes_from changed = {3}, votes_against changed = {4}".format(old_nick, new_nick, channel, counts['votes_from_affected'], counts['votes_against_affected'])

@module.event('PART')
@module.event('KICK')
@module.event('QUIT')
@module.rule('.*')
def leave_tracker(bot, trigger):
    """Removes all votes for a nick if it somehow leaves the channel."""
    channel = trigger.sender
    if channel not in kickvote_whitelist:
        return
    nick_affected = trigger.nick.lower()
    removed_count = remove_all_votes_for(channel, nick_affected)
    print "{0} is gone from {1}, {2} votes removed.".format(nick_affected, channel, removed_count)

@module.event('JOIN')
@module.rule('.*')
def create_vote_list(bot, trigger):
    """Create a list for each channel when the bot joins."""
    channel = trigger.sender
    if channel not in kickvote_whitelist:
        return
    try:
        if trigger.nick == bot.nick and votes[channel]:
            pass
    except KeyError:
        global votes
        votes[channel] = []
        print "Initialised list for {0}".format(channel)

# implement decaying votes?
# feh, needs time support, fuck it

######################
## helper functions ##
######################

# sum up votes and return a dictionary with target nick -> vote count pairs
def get_vote_counts(channel):
    vote_counts = {}
    if (len(votes[channel]) > 0):
        for vote_dict in votes[channel]:
            for (vote_from, vote_against) in vote_dict.iteritems():
                try:
                    vote_counts[vote_against] = vote_counts[vote_against] + 1
                except KeyError:
                    vote_counts[vote_against] = 1
        return vote_counts
    else:
        return None

# remove a vote from the global list
# returns True on success, False on failure
def remove_vote(channel, remove_vote_from, remove_vote_against):
    vote_pair = {remove_vote_from: remove_vote_against}
    for vote_dict in votes[channel]:
        for (vote_from, vote_against) in vote_dict.iteritems():
            if vote_from == remove_vote_from and vote_against == remove_vote_against:
                votes[channel].remove(vote_pair)
                return True
    return False

# remote all votes for a given nick from the global list
# returns the total number of votes it removed
def remove_all_votes_for(channel, remove_votes_against):
    votes_removed = 0
    votes_copy = list(votes[channel])
    for vote_pairs in votes_copy:
        for (vote_from, vote_against) in vote_pairs.iteritems():
            if (vote_against == remove_votes_against):
                remove_vote(channel, vote_from, vote_against)
                votes_removed = votes_removed + 1
    return votes_removed

# add a vote to the global list
# returns True on success, False if there was already a vote existing from that nick
def add_vote(channel, add_vote_from, add_vote_against):
    vote_pair = {add_vote_from: add_vote_against}
    for vote_dict in votes[channel]:
        for (vote_from, vote_against) in vote_dict.iteritems():
            if vote_from == add_vote_from and vote_against == add_vote_against:
                return False 
    votes[channel].append(vote_pair)
    return True

# check whether a given nick has voted for another
# returns True if they have, False if they haven't
def has_voted_for(channel, has_vote_from, has_vote_against):
    vote_pair = {has_vote_from, has_vote_against}
    for vote_dict in votes[channel]:
        for (vote_from, vote_against) in vote_dict.iteritems():
            if vote_from == has_vote_from and vote_against == has_vote_against:
                return True
    return False

# get a list of all the nicks who voted for the given nick
# returns a list of nicks on success or None on failure
def who_voted_for(channel, has_vote_against):
    vote_list = []
    for vote_dict in votes[channel]:
        for (vote_from, vote_against) in vote_dict.iteritems():
            if (vote_against == has_vote_against):
                vote_list.append(vote_from)
    if (len(vote_list) > 0):
        return vote_list
    else:
        return None

# replaces all references to the old nick with a new nick
# returns a dictionary containing counts of votes from and votes against which were affected
def replace_votes(channel, old_nick, new_nick):
    votes_from_affected = 0
    votes_against_affected = 0
    for vote_dict in votes[channel]:
        for (vote_from, vote_against) in vote_dict.iteritems():
            if vote_from == old_nick:
                add_vote(channel, new_nick, vote_against)
                remove_vote(channel, old_nick, vote_against)
                votes_from_affected = votes_from_affected + 1
            elif vote_against == old_nick:
                add_vote(channel, vote_from, new_nick)
                remove_vote(channel, vote_from, old_nick)
                votes_against_affected = votes_against_affected + 1
    return {'votes_from_affected': votes_from_affected, 'votes_against_affected': votes_against_affected}

# takes a list of voters and formats them nicely for a kick message
# returns a formatted string
def format_voter_list_for_kick(voter_list):
    try:
        if (len(voter_list) > 1):
            voter_list = sorted(voter_list)
            string = ", ".join(voter_list[:-1])
            string = string + " and " + voter_list[-1]
            return string
        else:
            return "{0}".format(voter_list[0])
    except ValueError, KeyError:
        return "someone"
