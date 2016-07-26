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
# Limiter for the Slots, so you cant spam them. Maybe your arm is Tired wait a
# little bit. ?
# Zork Adventure game, in a channel of its own.
# TODO -- EASY MODE - Norm the messages so users can send any caps.

#########################################
# Casino - Idea

# !blackjack -- author has X and X for a total of X, Commands !stand, !hit,
# and !doubledown.
#########################################

import os
import time
import json
import discord
import random
import urllib2
import requests
import pickle
import cleverbot
import enchanting_chances as en
from bs4 import BeautifulSoup

# Disables the SSL warning, that is printed to the console.
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
client = discord.Client()
BANK_PATH = './bot_files/lemon_bot_bank.pkl'
BET_PATH = './bot_files/lemon_bot_bets.pkl'
ACC_PATH = './bot_files/lemon_bot_accnum.pkl'

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

SLOT_PATTERN = [':four_leaf_clover:', ':"moneybag":', ':cherries:', ':lemon:', ':grapes:', ':poop:']

API_KEY = ''

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


# Function to clear a chat Channel.
def clear_chat_channel(message):
    counter = 0
    all_messages = client.messages
    target_channel = message.channel
    for message_step in all_messages:
        if message_step.channel == target_channel:
            client.delete_message(message_step)
            counter += 1
    client.send_message(message.channel, 'I have removed %s old messages' % counter)


# Save the dict Object
def save_obj(dict, file_path):
    with open(file_path, 'wb') as f:
        pickle.dump(dict, f, pickle.HIGHEST_PROTOCOL)

# Load the pickle Object
def load_obj(file_path):
    file_bool = os.path.isfile(file_path)
    if file_bool:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    else:
        return None


# Build Dict and return
def build_dict(file_path):
    path_bool = os.path.isfile(file_path)
    if not path_bool:
        data_dict = {}
    else:
        data_dict = load_obj(file_path)
    return data_dict


# Function to play the slots
def play_slots(author, message):
    wheel_list = []
    results_dict = {}
    count = 1
    winnings = 0
    bet_dict = build_dict(BET_PATH)
    if bet_dict.get(str(author)):
        set_bet = bet_dict.get(str(author))
    else:
        client.send_message(message.channel, 'You need to set a bet with the !bet command, Example: !bet 10')
        return
    bank_dict = build_dict(BANK_PATH)
    if bank_dict.get(str(author)):
        balance = bank_dict.get(str(author))
    else:
        client.send_message(message.channel, 'You need to run the !loan command.')
        return
    if set_bet > balance:
        client.send_message(message.channel, 'Your balance of $%s is to low, lower your bet amount of $%s' % (balance, set_bet))
        return
    while count <= 4:
        wheel_pick = SLOT_PATTERN[random.randint(0, len(SLOT_PATTERN) - 1)]
        wheel_list.append(wheel_pick)
        count += 1
    last_step = ''
    for wheel_step in wheel_list:
        if not results_dict.get(wheel_step):
            results_dict[wheel_step] = 1
        if results_dict.get(wheel_step) and last_step == wheel_step:
            data = results_dict.get(wheel_step)
            results_dict[wheel_step] = data + 1
        last_step = wheel_step
    for k, v in results_dict.iteritems():
        if (k == ':cherries:' or k == ':lemon:' or k == ':grapes:') and v == 4:
            winnings = set_bet * 50
            break
        if (k == ':cherries:' or k == ':lemon:' or k == ':grapes:') and v == 3:
            winnings = set_bet * 25
            break
        if k == ':"moneybag":' and v == 4:
            winnings = set_bet * 500
            break
        if k == ':"moneybag":' and v == 3:
            winnings = set_bet * 100
            break
        if k == ':four_leaf_clover:' and v == 4:
            winnings = set_bet * 1000
            break
        if k == ':four_leaf_clover:' and v == 3:
            winnings = set_bet * 200
            break
        else:
            winnings = -set_bet
    wheel_payload = '%s Bet: $%s --> | ' %( author, set_bet) + ' - '.join(wheel_list) + ' |' + ' Outcome: $%s' % winnings
    client.send_message(message.channel, wheel_payload)
    result = int(bank_dict.get(str(author))) + int(winnings)
    if result <= 0:
        bank_dict[str(author)] = 0
    else:
        bank_dict[str(author)] = result
    save_obj(bank_dict, BANK_PATH)


# Function to set a users bet.
def set_bet(author, message):
    amount = message.content.replace('!bet ', '')
    try:
        amount = int(amount)
    except Exception:
        client.send_message(message.channel, 'You need to enter an integer, Example: !bet 5')
        return
    file_bool = os.path.isfile(BET_PATH)
    if not file_bool:
        data_dict = {}
    else:
        data_dict = load_obj(BET_PATH)
    client.send_message(message.channel, '%s, set bet to: %s' % (author, amount))
    data_dict[str(author)] = amount
    save_obj(data_dict, BET_PATH)

# Function to look at the currently Set bet.
def review_bet(author, message):
    bet_dict = build_dict(BET_PATH)
    if bet_dict.get(str(author)):
        client.send_message(message.channel, '%s is currently betting: %s' % (author, bet_dict.get(str(author))))
    else:
        client.send_message(message.channel, '%s your bet is not Set, use the !bet command.' % (author))



# function to loan players money -- ONLY UP TO -- > $50 dollars
def loan_money(author, message):
    bank_dict = build_dict(BANK_PATH)
    if bank_dict.get(str(author)):
        money = bank_dict.get(str(author))
        if money >= 50:
            client.send_message(message.channel, '%s you have $%s, you do not need a loan.' % (author, money))
            return
        else:
            bank_dict[str(author)] = 50
            client.send_message(message.channel, '%s, added up to $50' % author)
    else:
        bank_dict[str(author)] = 50
        client.send_message(message.channel, '%s, added $50' % author)
    save_obj(bank_dict, BANK_PATH)


# Function to look up a users Money!
def bank_lookup(author, message):
    acc_dict = build_dict(ACC_PATH)
    if acc_dict.get(str(author)):
        account_number = acc_dict.get(str(author))
    else:
        account_number = random.randint(0,999999999)
        acc_dict[str(author)] = account_number
    bank_dict = build_dict(BANK_PATH)
    if str(author) in bank_dict.keys():
        balance = bank_dict.get(str(author))
        client.send_message(message.channel, 'User: %s, Account-#: %s, Balance: $%s' % (author, account_number, balance))
    if not str(author) in bank_dict.keys():
        client.send_message(message.channel, "Looks like you don't have an Account, try the !loan command.")
    save_obj(acc_dict, ACC_PATH)

#Function to lookup the money and create a top 5 users.
def leader_lookup(author, message):
    bank_dict = build_dict(BANK_PATH)
    counter = 0
    leader_list = []
    for key in sorted(bank_dict, key=bank_dict.get, reverse=True)[:5]:
        counter += 1
        leader_list.append('#%s - %s - $%s' % (counter, key, bank_dict[key]))
    client.send_message(message.channel, '  |  '.join(leader_list))

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
    else:
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
def roll_odds(author, message):
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
        roll_odds(author, message)
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
    if message.content.startswith('!slots'):
        play_slots(author, message)
    if message.content.startswith('!clear'):
        clear_chat_channel(message)
    if message.content.startswith('!bet'):
        set_bet(author, message)
    if message.content.startswith('!reviewbet'):
        review_bet(author, message)
    if message.content.startswith('!loan'):
        loan_money(author, message)
    if message.content.startswith('!bank'):
        bank_lookup(author, message)
    if message.content.startswith('!leader'):
        leader_lookup(author, message)



# Create the local Dirs if needed.
file_bool = os.path.exists("./bot_files")
if not file_bool:
    os.system('mkdir ./bot_files')
# Simple client login and starting the bot.
client.login('', '')
client.run()
