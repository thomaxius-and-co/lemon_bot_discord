#!/usr/bin/python 

# This will be a bot that will add a search feature and others to the discord app.


# TODO LIST
# Black Stone Calc, already have the code
# Help commands, link to the git hub page.
# Search engine, youtube, google(gif, image), wikipedia, wolfram. these should all quey a server.
# command when the bot name is said

import sys
import discord
import random 
import urllib2
import enchanting_chances as en
from bs4 import BeautifulSoup, SoupStrainer

client = discord.Client()
client.login('', '')

# Function to search for a youtube video and return a link. 
def youtube_search(text_to_search, message):
    link_list = []
    print 'Searching YouTube for: %s' % text_to_search
    #url = urllib2.Request("https://www.youtube.com/results?search_query=" + text_to_search)
    query = urllib2.quote(text_to_search)
    url = "https://www.youtube.com/results?search_query=" + query
    response = urllib2.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, 'html_parser')
    for vid in soup.findAll(attrs={'class':'yt-uix-tile-link'}):
            print 'https://www.youtube.com' + vid['href']
            link_list.append('https://www.youtube.com' + vid['href'])
    random_num = random.randint(0, len(link_list) - 1)
    client.send_message(message.channel, link_list[random_num])

# Scrape a page and return a single link
def get_url(page):
    return



@client.event
def on_message(message):
    if message.content.startswith('!enchant'):
        try:
            raw_data = message.content.strip('!enchant ').split(' ')
            enchanting_results = en.run_the_odds(raw_data[0],raw_data[1])
            client.send_message(message.channel, enchanting_results)
        except Exception:
            client.send_message(message.channel, 'Use the Format --> !enchant target_level fail_stacks')
    if message.content.startswith('!youtube'):
        youtube_search(message.content.strip('!youtube '), message)

@client.event
def on_ready():
    client.accept_invite('')
    client.run()

def main():
    on_ready()

if __name__ == "__main__":
    sys.exit(main())
