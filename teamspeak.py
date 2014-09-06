"""
reminder.py - Willie Teamspeak Module
Written by webvictim <webvictim@gmail.com>
"""

import urllib
import threading
import re
import select
import socket
import time
from willie import module, web

say_channel = "#random"
old_nicks = None
#server = "85.236.100.27"
#port = 15884
#virtual_server = "5615"
#reported_server_details = "85.236.100.27:26307"
server = "37.187.97.208"
port = 10011
virtual_server = "1"
reported_server_details = "ts.webvict.im"

def _readsocket(socket):
    buffer = ""
    terminate = False
    while not terminate:
        try:
            (rlist, wlist, xlist) = select.select([socket], [], [], 1)
            if len(rlist) == 0:
                if len(buffer) == 0:
                    print "Expected something, but got nothing"
                    socket.close()
                else:
                    return buffer

            temp_buffer = socket.recv(4096)

            if len(temp_buffer) == 0:
                return buffer

            buffer = buffer + temp_buffer
        except:
            print "Communication error occurred (recv)"
            socket.close()
            return ""
    return buffer

def _writesocket(socket, data):
    try:
        socket.send(data)
        return True
    except:
        print "Communication error occurred (send)"
        socket.close()
        return False

def _closesocket(socket):
    try:
        socket.close()
        return True
    except:
        print "Couldn't close the socket for some reason"
        return False

def obfuscate_list(a_list, sort_list=True):
    return_list = []
    for nick in a_list:
        return_list.append("%s%s%s" % (nick[0], u"\u200B", nick[1:]))
    if (sort_list):
        return sorted(return_list, key=lambda s: s.lower())
    else:
        return return_list

def get_nicks(obfuscated=False):
    online_nicks = []
    afk_nicks = []
    random_nicks = []

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server, port))

        header = _readsocket(s)
        if "specific command" not in header:
            print "Failed to connect for some reason"
            return False

        _writesocket(s, "use sid={0}\r\n".format(virtual_server))
        sid = _readsocket(s)
        if "error id=0 msg=ok" not in sid:
            print "Error selecting virtual server"
            return False

        _writesocket(s, "clientlist\r\n")
        clientinfo = _readsocket(s)
        if (len(clientinfo) == 0):
            print "Error getting client info"
            return False

        else:
            _closesocket(s)
            clients = clientinfo.split('|')
            for item in clients:
                # actual client
                if 'client_type=0' in item:
                    # afk=16, busy=21, fap lounge=34
                    if 'cid=16' in item or 'cid=21' in item or 'cid=34' in item:
                        client_subset = item.split()
                        for subitem in client_subset:
                            if 'client_nickname' in subitem:
                                heading, nick = subitem.split('=')
                                nick = re.sub('\\\s', ' ', nick)
                                afk_nicks.append(nick)
                    # in #random
                    elif 'cid=1' in item:
                        client_subset = item.split()
                        for subitem in client_subset:
                            if 'client_nickname' in subitem:
                                heading, nick = subitem.split('=')
                                nick = re.sub('\\\s', ' ', nick)
                                random_nicks.append(nick)
                    # in any other channel
                    else:
                        client_subset = item.split()
                        for subitem in client_subset:
                            if 'client_nickname' in subitem:
                                heading, nick = subitem.split('=')
                                nick = re.sub('\\\s', ' ', nick)
                            #if 'client_away=1' in subitem:
                            #    client_status = '[away]'
                            #elif 'client_input_muted=1' in subitem:
                            #    client_status = '[muted]'
                            #    nicks.append("{0} {1}".format(nick, client_status))                        
                                online_nicks.append(nick)
 
        if (obfuscated):
            return obfuscate_list(online_nicks), obfuscate_list(afk_nicks), obfuscate_list(random_nicks)
        else:
            return online_nicks, afk_nicks, random_nicks
    except:
        pass

# crazy threading for real-time updates
# this doesn't work very well so i removed it
def setup(bot):
    def monitor(bot):
        global old_nicks
        while True:
            if old_nicks is not None:        
                print "Checking Teamspeak..."
                nicks = get_nicks()

                change_list = list(set(nicks) - set(old_nicks))
                print "joined: %s" % (change_list)
                reverse_change_list = list(set(old_nicks) - set(nicks))
                print "left: %s" % (reverse_change_list)

                if (len(change_list) > 0):
                    # people joined
                    bot.msg(say_channel, "Joined Teamspeak: %s" % (", ".join(obfuscate_list(change_list))))

                if (len(reverse_change_list) > 0):
                    # people left
                    bot.msg(say_channel, "Left Teamspeak: %s" % (", ".join(obfuscate_list(reverse_change_list))))
                old_nicks = nicks
            else:
                print "Setting old nicks..."
                old_nicks = get_nicks()
                print(old_nicks)
            
            time.sleep(90)

    #targs = (bot,)
    #t = threading.Thread(target=monitor, args=targs)
    #t.start()

@module.rule('^!ts$')
@module.rule('^!teamspeak$')
def teamspeak_check(bot, trigger):
    """Prints a list of all users currently on Teamspeak."""
    online_nicks, afk_nicks, random_nicks = get_nicks()
    if online_nicks is None or afk_nicks is None or random_nicks is None:
        bot.msg(say_channel, "Something's wrong. Sorry :(")
    elif online_nicks is None or afk_nicks is None or random_nicks is None:
        bot.msg(say_channel, "Something's wrong. Sorry :(")
    else:
        old_online_nicks = online_nicks
        old_afk_nicks = afk_nicks
        old_random_nicks = random_nicks
        if len(online_nicks) == 0 and len(afk_nicks) == 0 and len(random_nicks) == 0:
            summary_output = "Nobody online"
        else:
            if len(online_nicks) > 0:
                people_are_online = True
            else:
                people_are_online = False

            if len(afk_nicks) > 0:
                people_are_afk = True
            else:
                people_are_afk = False

            if len(random_nicks) > 0:
                people_in_random = True
            else:
                people_in_random = False

            summary = []

            if people_in_random:
                summary.append("online: %s" % (", ".join(obfuscate_list(random_nicks))))
            if people_are_online:
                summary.append("in other channels: %s" % (", ".join(obfuscate_list(online_nicks))))
            if people_are_afk:
                summary.append("afk/busy: %s" % (", ".join(obfuscate_list(afk_nicks))))

            if not people_are_online and not people_are_afk and not people_in_random:
                summary_output = "Nobody online"
            else:
                summary_output = "People " + " | ".join(summary)

        bot.msg(say_channel, "Teamspeak: %s | %s" % (reported_server_details, summary_output))
