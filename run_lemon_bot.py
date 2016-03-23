#!/usr/bin/python
# This is a Text based discord Bot that will interface with users via commands
# given from the text channels in discord.

# ################### Copyright (c) 2016 RamCommunity #################
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do so


# TODO LIST
#########################################
# google search
# wiki search
#########################################

import time
import json
import discord
import random
import urllib2
import requests
import cleverbot
import enchanting_chances as en
from bs4 import BeautifulSoup

# Disables the SSL warning, that is printed to the console.
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
client = discord.Client()

EIGHT_BALL_OPTIONS = ["It is certain", "It is decidedly so", "Without a doubt",
                      "Yes definitely", "You may rely on it", "As I see it yes",
                      "Most likely", "Outlook good", "Yes",
                      "Signs point to yes", "Reply hazy try again",
                      "Ask again later", "Better not tell you now",
                      "Cannot predict now", "Concentrate and ask again",
                      "Don't count on it", "My reply is no",
                      "My sources say no", "Outlook not so good",
                      "Very doubtful"]

SPANK_BANK = ['spanked', 'clobbered', 'paddled', 'whipped', 'punished',
              'caned', 'thrashed', 'smacked']

API_KEY = 'e8b843957be984dee5f1966d4df6ecc5'


# Function to search for a youtube video and return a link.
def youtube_search(message):
    link_list = []
    text_to_search = message.content.replace('!youtube', '')
    print 'Searching YouTube for: %s' % text_to_search
    query = urllib2.quote(text_to_search)
    url = "https://www.youtube.com/results?search_query=" + query
    response = urllib2.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, "lxml")
    for vid in soup.findAll(attrs={'class': 'yt-uix-tile-link'}):
            link_list.append('https://www.youtube.com' + vid['href'])
    random_num = random.randint(0, len(link_list) - 1)
    client.send_message(message.channel, link_list[random_num])


# Function to get the weather by zip code. using: http://openweathermap.org
# you can get an API key on the web site.
def get_weather(message):
    zip_code = message.content.replace('!weather', '')
    link = 'http://api.openweathermap.org/data/2.5/weather?q=%s&APPID=%s' % (zip_code, API_KEY)
    r = requests.get(link)
    data = json.loads(r.text)
    location = data['name']
    temp = data['main']['temp'] * 1.8 - 459.67
    status = data['weather'][0]['description']
    payload = 'In %s: Weather is: %s, Temp is: %s' % (location, status, temp)
    client.send_message(message.channel, payload)


# function to make the bot join a server.
def bot_join(message):
    join_url = message.content.strip('!join ')
    client.accept_invite(join_url)
    client.send_message(message.channel, 'Joining the Server! ^_^')


# Ask clever bot a question.
def ask_clever_bot(message):
    question = message.content.replace('!cleverbot', '')
    cb1 = cleverbot.Cleverbot()
    answer = cb1.ask(question)
    client.send_message(message.channel, answer)


# this Spanks the user and calls them out on the server, with an '@' message.
# Format ==> @User has been, INSERT_ITEM_HERE
def spank_user(message, author):
    target_user = message.content.replace('!spank ', '')
    punishment = SPANK_BANK[random.randint(0, len(SPANK_BANK) - 1)]
    client.send_message(message.channel, "%s has been, %s by %s" % (target_user, punishment, author))


# Simple 50/50 coin toss
def coin_toss(message):
    outcome = random.randint(0,1)
    if outcome == 0:
        outcome = "Heads"
    if outcome == 1:
        outcome = "Tails"
    client.send_message(message.channel, "Just a moment, flipping the coin...")
    time.sleep(.5)
    client.send_message(message.channel, "The coin Shows, %s" % outcome)


# function to call the BDO script and relay odds on enchanting.
def bdo_enchant(message):
    try:
        raw_data = message.content.strip('!enchant ').split(' ')
        enchanting_results = en.run_the_odds(raw_data[0], raw_data[1])
        client.send_message(message.channel, enchanting_results)
    except Exception:
        client.send_message(message.channel, 'Use the Format --> !enchant target_level fail_stacks')


# Rolling the odds for a user.
def roll_odds(message):
    rand_roll = random.randint(0, 100)
    client.send_message(message.channel, '%s your roll is %s' % (author, rand_roll))


# eight ball function to return the magic of the eight ball.
def eight_ball(message):
    question = message.content.strip('!8ball')
    prediction = random.randint(0, len(EIGHT_BALL_OPTIONS) - 1)
    client.send_message(message.channel, 'Question: [%s], %s' % (question, EIGHT_BALL_OPTIONS[prediction]))


# Dispacther for messages from the users.
@client.event
def on_message(message):
    author = message.author
    if message.content.startswith('!enchant'):
        bdo_enchant(message)
    if message.content.startswith('!youtube'):
        youtube_search(message)
    if message.content.startswith('!roll'):
        roll_odds(message)
    if message.content.startswith('!8ball'):
        eight_ball(message)
    if message.content.startswith('!join'):
        bot_join(message)
    if message.content.startswith('!weather'):
        get_weather(message)
    if message.content.startswith('!cleverbot'):
        ask_clever_bot(message)
    if message.content.startswith('!spank'):
        spank_user(message, author)
    if message.content.startswith('!coin'):
        coin_toss(message)
    if message.content.startswith('!help'):
        client.send_message(message.channel, 'https://github.com/lemon65/discord_bot#commands')

# Simple client login and starting the bot.
client.login('lemon65.twitch@gmail.com', 'Dragon_4545')
client.run()
