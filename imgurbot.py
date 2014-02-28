from willie import module, web
import json
import random
import time
from operator import itemgetter

bad_nicks = ['Paradox']
last_seen = {}
users = {}
allowed_per_minute = 5

class User(object):
    def __init__(self, user):
        self.user = user
        self.posts = []

    def posted(self):
        self.posts.append(int(time.time()))

    def is_douchebag(self):
        total = 0
        for t in self.posts:
            if int(time.time()) - t <= 60:
                total += 1
            else:
                self.posts.pop(t)
        if total >= allowed_per_minute:
            return total
        return False

@module.rule('$nickname:\ (\w+)')
@module.rule('^$nickname\ (\w+)$')
def imgurbot(bot, trigger):
    nickname = trigger.nick
    if not users.has_key(nickname):
        users[nickname] = User(nickname)
    else:
        users[nickname].posted()
    douchebag = users[nickname].is_douchebag()
    if douchebag == 5:
        bot.reply("Slow down there cowboy.")
        return
    elif douchebag > 5:
        return

    mode = "hot"

    if nickname in bad_nicks:
        mode="controversial"

    subreddit = trigger.group(1)
    url = "http://www.reddit.com/r/{0}/search.json?q=site%3Aimgur.com&restrict_sr=on&sort={1}&t=all".format(subreddit, mode)
    get = web.get(url, timeout=5)

    try:
        array = json.loads(get)
    except ValueError:
        bot.reply("{0} doesn't look like a subreddit to me.".format(subreddit))
        return

    if 'error' in array:
        if array['error'] == 404:
            bot.reply("{0} isn\'t a real subreddit.".format(subreddit))
            return
        elif array['error'] == 403:
            bot.reply("{0} is a private subreddit.".format(subreddit))
            return
        else:
            bot.reply("Unknown error. Whoops.")
            return
    else:
        if not last_seen.has_key(subreddit):
            last_seen[subreddit] = {}
        links = []
        iterator = 0
        while (len(links) < 10) and (iterator < len(array)):
            if 'children' in array['data']:
                for child in array['data']['children']:
                    iterator = iterator + 1
                    if child['data']['domain'] == 'i.imgur.com':    
                        if 'over_18' in child['data']:
                            id = child['data']['id']
                            if last_seen[subreddit].has_key(id):
                                child['data']['lastseen'] = last_seen[subreddit][id]
                            else:
                                child['data']['lastseen'] = 0
                            links.append(child['data'])
        if (len(links)>0):
            links = sorted(links, key=itemgetter('lastseen'))
            last_seen[subreddit][links[0]['id']] = int(time.time())
            suffix = ''
            if (links[0]['over_18'] is True):
                suffix = ' [nsfw]'
            bot.say("[{0}] {1} - \"{2}\"{3}".format(subreddit, links[0]['url'], links[0]['title'], suffix))
            return
        else:
            bot.reply("No imgur links amongst hot posts in r/{0} today.".format(subreddit))
