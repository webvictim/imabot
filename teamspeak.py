"""
reminder.py - Willie Teamspeak Module
Modifications by webvictim <webvictim@gmail.com>
"""

import urllib
import threading
import select
import socket
import time
from willie import module, web

say_channel = "#random"
old_nicks = None
server = "85.236.100.27"
port = 15884

def _readsocket(socket):
    buffer = ""
    terminate = False
    while not terminate:
        try:
            (rlist, wlist, xlist) = select.select([socket], [], [], 0.5)
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
        return sorted(return_list)
    else:
        return return_list

def get_nicks(obfuscated=False):
    nicks = []

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server, port))

    header = _readsocket(s)
    if "specific command" not in header:
        print "Failed to connect for some reason"
        return False

    _writesocket(s, "use sid=5615\r\n")
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
            if 'client_type=0' in item:
                client_subset = item.split()
                for subitem in client_subset:
                    if 'client_nickname' in subitem:
                        heading, nick = subitem.split('=')
                        nicks.append(nick)

    if (obfuscated):
        return obfuscate_list(nicks)
    else:
        return nicks

# crazy threading for real-time updates
def setup(bot):
    def monitor(bot):
        global old_nicks
        while True:
            if old_nicks is not None:        
                print "Checking Teamspeak..."
                nicks = get_nicks()

                change_list = list(set(nicks) - set(old_nicks))
                print "change_list: %s" % (change_list)
                reverse_change_list = list(set(old_nicks) - set(nicks))
                print "reverse_change_list: %s" % (reverse_change_list)

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
            
            time.sleep(60)

    targs = (bot,)
    t = threading.Thread(target=monitor, args=targs)
    t.start()

@module.rule('!ts')
@module.rule('!teamspeak')
def teamspeak_check(bot, trigger):
    """Prints a list of all users currently on Teamspeak."""
    nicks = get_nicks()
    if nicks is False:
        bot.msg(say_channel, "Something's wrong. Sorry :(")
    else:
        old_nicks = nicks
        bot.msg(say_channel, "People on Teamspeak: %s" % (", ".join(obfuscate_list(nicks))))
