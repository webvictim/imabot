from willie import module, web
import HTMLParser
import re
import urllib
hp = HTMLParser.HTMLParser()

class TFLN:
    def __init__(self, text_id, area_code, area_info, actual_text):
        self.text_id = text_id
        self.area_code = area_code
        self.area_info = area_info
        self.actual_text = actual_text

    def render(self):
        return ("TFLN: %s (%s) - \"%s\"" % (self.area_info, self.area_code, self.actual_text))

# texts we've already seen 
candidates = []
already_seen_ids = []
last_page_number = 1

area_regex = re.compile('<h3><a href="/Texts-From-Areacode-([\d]+).html">\([\d]+\): <span>View more from (.*)</span></a></h3>')
text_regex = re.compile('<p><a href="/Text-Replies-([\d]+).html">(.*)</a></p>')

def fetch_tfln():
    global last_page_number

    new_page = []
    print "Fetching TFLN"
    last_page_number = last_page_number + 1
    url = "http://textsfromlastnight.com/texts-from-last-night/page:%s/type:Best/span:Week" % last_page_number
    html = urllib.urlopen(url).readlines()
    lines = iter(html)

    for line in lines:
        if area_regex.match(line):
            area_matches = area_regex.search(line).groups()
            area_code = area_matches[0]
            area_info = area_matches[1]
            next_line = next(lines)

            if text_regex.match(next_line):
                text_matches = text_regex.search(next_line).groups()
                text_id = text_matches[0]
                actual_text = hp.unescape(text_matches[1])
                tfln = TFLN(text_id, area_code, area_info, actual_text)
                print tfln.text_id
                new_page.append(tfln)

    return new_page

# get a text from the central list
# if we've used them all, get some new ones
def get_tfln():
    global candidates

    if len(candidates) == 0:
        candidates = fetch_tfln()

    for candidate in candidates:
        if (candidate.text_id not in already_seen_ids):
            already_seen_ids.append(candidate.text_id)
            print "showing ID %s" % candidate.text_id
            return candidate

    # if we didn't already send anything back, get some more and go again
    candidates = fetch_tfln()
    get_tfln()
           
@module.rule('^!tfln$')
def show_tfln(bot, trigger):
    retry_counter = 3

    while retry_counter > 0:
        content = get_tfln()
        if not content:
            retry_counter -= 1
        else:
            bot.say(content.render())
            break

    if retry_counter == 0:
        bot.reply("Sorry, can't get TFLN. Try later.")
    return
