from willie import module, web
import json
import random

@module.rule('$nickname:\ (\w+)')
@module.rule('^$nickname\ (\w+)$')

def imgurbot(bot, trigger):
	subreddit = trigger.group(1)
	url = "http://www.reddit.com/r/{0}/hot/.json?limit=20".format(subreddit)
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
		links = []
		iterator = 0
		while (len(links) < 10) and (iterator < len(array)):
			if 'children' in array['data']:
				for child in array['data']['children']:
					iterator = iterator + 1
					if child['data']['domain'] == 'i.imgur.com':	
						if 'over_18' in child['data']:
							links.append(child['data'])

		if (len(links)>0):
			index = random.randint(0,(len(links)-1))
			suffix = ''
			if (links[index]['over_18'] is True):
				suffix = ' [nsfw]'
			bot.say("[{0}] {1} - \"{2}\"{3}".format(subreddit, links[index]['url'], links[index]['title'], suffix))
			return
		else:
			bot.reply("No imgur links amongst hot posts in r/{0} today.".format(subreddit))
