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
import urllib3
import urllib.request
import requests
import pickle
import cleverbot
import urllib.parse
import enchanting_chances as en
from bs4 import BeautifulSoup
import asyncio
from lxml.html.soupparser import fromstring
import wolframalpha

# Disables the SSL warning, that is printed to the console.
import requests.packages.urllib3

requests.packages.urllib3.disable_warnings()
client = discord.Client()
wolframalpha_client = wolframalpha.Client(os.environ['WOLFRAM_ALPHA_APPID'])
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


def parse_command(content):
    if not content.startswith('!'):
        return None, None
    if content.startswith('!math'): #Math command needs 3 arguments, so I implemented this for now
        cmd, *arg = content.strip('!').split(' ', 3)
        print(arg)
        return cmd, arg
    cmd, *arg = content.strip('!').split(' ', 1)
    return cmd.lower(), arg[0] if arg else None


# function to call the BDO script and relay odds on enchanting.
@asyncio.coroutine
def cmd_enchant(message, arg):
    try:
        raw_data = arg.split(' ')
        enchanting_results = en.run_the_odds(raw_data[0], raw_data[1])
        yield from client.send_message(message.channel, enchanting_results)
    except Exception:
        yield from client.send_message(message.channel, 'Use the Format --> !enchant target_level fail_stacks')

# Function to search for a youtube video and return a link.
@asyncio.coroutine
def cmd_youtube(message, text_to_search):
    link_list = []
    print('Searching YouTube for: %s' % text_to_search)
    query = urllib.parse.quote(text_to_search)
    url = "https://www.youtube.com/results?search_query=" + query
    response = urllib.request.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, "lxml")
    for vid in soup.findAll(attrs={'class': 'yt-uix-tile-link'}):
        link_list.append('https://www.youtube.com' + vid['href'])
    random_link = random.choice(link_list)
    yield from client.send_message(message.channel, random_link)

# Rolling the odds for a user.
@asyncio.coroutine
def cmd_roll(message, _):
    rand_roll = random.randint(0, 100)
    yield from client.send_message(message.channel, '%s your roll is %s' % (message.author, rand_roll))

# eight ball function to return the magic of the eight ball.
@asyncio.coroutine
def cmd_8ball(message, question):
    prediction = random.choice(EIGHT_BALL_OPTIONS)
    yield from client.send_message(message.channel,
                                   'Question: [%s], %s' % (question, prediction))

# function to make the bot join a server.
@asyncio.coroutine
def cmd_join(message, join_url):
    client.accept_invite(join_url)
    yield from client.send_message(message.channel, 'Joining the Server! ^_^')

# Function to get the weather by zip code. using: http://openweathermap.org
# you can get an API key on the web site.
@asyncio.coroutine
def cmd_weather(message, zip_code):
    if not zip_code:
        yield from client.send_message(message.channel, "You must specify a city, eq. Säkylä")
        return
    link = 'http://api.openweathermap.org/data/2.5/weather?q=%s&APPID=%s' % (zip_code, API_KEY)
    r = requests.get(link)
    data = json.loads(r.text)
    location = data['name']
    F = data['main']['temp'] * 1.8 - 459.67
    C = (F - 32) * 5 / 9
    status = data['weather'][0]['description']
    payload = 'In %s: Weather is: %s, Temp is: %s°C  (%s°F) ' % (location, status, round(C), round(F))
    yield from client.send_message(message.channel, payload)

@asyncio.coroutine
# Simple math command.
def cmd_math(message, arg):
    a = arg[0]
    b = arg[1]
    c = arg[2]
    if b == '+':
        calculation = int(a) + int(c)
    if b == '-':
        calculation = int(a) - int(c)
    if b == '*':
        calculation = int(a) * int(c)
    if b == '/' or b == 'x':
        calculation = int(a) / int(c)
    yield from client.send_message(message.channel, '%s %s %s is %s' % (a, b, c, calculation))

# Ask clever bot a question.
@asyncio.coroutine
def cmd_cleverbot(message, question):
    cb1 = cleverbot.Cleverbot()
    answer = cb1.ask(question)
    yield from client.send_message(message.channel, answer)

# this Spanks the user and calls them out on the server, with an '@' message.
# Format ==> @User has been, INSERT_ITEM_HERE
@asyncio.coroutine
def cmd_spank(message, target_user):
    punishment = random.choice(SPANK_BANK)
    yield from client.send_message(message.channel, "%s has been, %s by %s" % (target_user, punishment, message.author))

@asyncio.coroutine
def cmd_coin(message, _):
    outcome = random.choice(["Heads", "Tails"])
    yield from client.send_message(message.channel, "Just a moment, flipping the coin...")
    print("test")
    time.sleep(.5)
    yield from client.send_message(message.channel, "The coin lands on: %s" % outcome)

@asyncio.coroutine
def cmd_help(message, _):
    yield from client.send_message(message.channel, 'https://github.com/lemon65/discord_bot#commands')

# Function to clear a chat Channel.
@asyncio.coroutine
def cmd_clear(message, _):
    counter = 0
    all_messages = client.messages
    target_channel = message.channel
    for message_step in all_messages:
        if message_step.channel == target_channel:
            client.delete_message(message_step)
            counter += 1
    yield from client.send_message(message.channel, 'I have removed %s old messages' % counter)

# Function to play the slots
@asyncio.coroutine
def cmd_slots(message, _):
    wheel_list = []
    results_dict = {}
    count = 1
    winnings = 0
    bet_dict = build_dict(BET_PATH)
    if bet_dict.get(str(message.author)):
        set_bet = bet_dict.get(str(message.author))
    else:
        yield from client.send_message(message.channel,
                                       'You need to set a bet with the !bet command, Example: !bet 10')
        return
    bank_dict = build_dict(BANK_PATH)
    if bank_dict.get(str(message.author)):
        balance = bank_dict.get(str(message.author))
    else:
        yield from client.send_message(message.channel, 'You need to run the !loan command.')
        return
    if set_bet > balance:
        yield from client.send_message(message.channel,
                                       'Your balance of $%s is to low, lower your bet amount of $%s' % (
                                       balance, set_bet))
        return
    while count <= 4:
        wheel_pick = random.choice(SLOT_PATTERN)
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
    wheel_payload = '%s Bet: $%s --> | ' % (message.author, set_bet) + ' - '.join(
        wheel_list) + ' |' + ' Outcome: $%s' % winnings
    yield from client.send_message(message.channel, wheel_payload)
    result = int(bank_dict.get(str(message.author))) + int(winnings)
    if result <= 0:
        bank_dict[str(message.author)] = 0
    else:
        bank_dict[str(message.author)] = result
    save_obj(bank_dict, BANK_PATH)

# Function to set a users bet.
@asyncio.coroutine
def cmd_bet(message, amount):
    try:
        amount = int(amount)
    except Exception:
        yield from client.send_message(message.channel, 'You need to enter an integer, Example: !bet 5')
        return
    file_bool = os.path.isfile(BET_PATH)
    if not file_bool:
        data_dict = {}
    else:
        data_dict = load_obj(BET_PATH)
    yield from client.send_message(message.channel, '%s, set bet to: %s' % (message.author, amount))
    data_dict[str(message.author)] = amount
    save_obj(data_dict, BET_PATH)

# Function to look at the currently Set bet.
@asyncio.coroutine
def cmd_reviewbet(message, _):
    bet_dict = build_dict(BET_PATH)
    if bet_dict.get(str(message.author)):
        yield from client.send_message(message.channel,
                                       '%s is currently betting: %s' % (message.author, bet_dict.get(str(message.author))))
    else:
        yield from client.send_message(message.channel, '%s your bet is not Set, use the !bet command.' % (message.author))

# function to loan players money -- ONLY UP TO -- > $50 dollars
@asyncio.coroutine
def cmd_loan(message, _):
    bank_dict = build_dict(BANK_PATH)
    if bank_dict.get(str(message.author)):
        money = bank_dict.get(str(message.author))
        if money >= 50:
            yield from client.send_message(message.channel,
                                           '%s you have $%s, you do not need a loan.' % (message.author, money))
            return
        else:
            bank_dict[str(message.author)] = 50
            yield from client.send_message(message.channel, '%s, added up to $50' % message.author)
    else:
        bank_dict[str(message.author)] = 50
        yield from client.send_message(message.channel, '%s, added $50' % message.author)
    save_obj(bank_dict, BANK_PATH)

# Function to look up a users Money!
@asyncio.coroutine
def cmd_bank(message, _):
    acc_dict = build_dict(ACC_PATH)
    if acc_dict.get(str(message.author)):
        account_number = acc_dict.get(str(message.author))
    else:
        account_number = random.randint(0, 999999999)
        acc_dict[str(message.author)] = account_number
    bank_dict = build_dict(BANK_PATH)
    if str(message.author) in bank_dict.keys():
        balance = bank_dict.get(str(message.author))
        yield from client.send_message(message.channel,
                                       'User: %s, Account-#: %s, Balance: $%s' % (message.author, account_number, balance))
    if not str(message.author) in bank_dict.keys():
        yield from client.send_message(message.channel,
                                       "Looks like you don't have an Account, try the !loan command.")
    save_obj(acc_dict, ACC_PATH)

# Function to lookup the money and create a top 5 users.
@asyncio.coroutine
def cmd_leader(message, _):
    bank_dict = build_dict(BANK_PATH)
    counter = 0
    leader_list = []
    for key in sorted(bank_dict, key=bank_dict.get, reverse=True)[:5]:
        counter += 1
        leader_list.append('#%s - %s - $%s' % (counter, key, bank_dict[key]))
    yield from client.send_message(message.channel, '  |  '.join(leader_list))

def cmd_wolframalpha(message, query):
    print("Searching WolframAlpha for '%s'" % query)

    yield from client.send_typing(message.channel)

    try:
        res = wolframalpha_client.query(query)
        answer = next(res.results).text
        yield from client.send_message(message.channel, answer)
    except Exception:
        yield from client.send_message(message.channel, 'I don\'t know how to answer that')

commands = {
    'enchant': cmd_enchant,
    'youtube': cmd_youtube,
    'roll': cmd_roll,
    '8ball': cmd_8ball,
    'join': cmd_join,
    'weather': cmd_weather,
    'cleverbot': cmd_cleverbot,
    'spank': cmd_spank,
    'coin': cmd_coin,
    'help': cmd_help,
    'slots': cmd_slots,
    'clear': cmd_clear,
    'bet': cmd_bet,
    'reviewbet': cmd_reviewbet,
    'loan': cmd_loan,
    'bank': cmd_bank,
    'leader': cmd_leader,
    'math': cmd_math,
    'wa': cmd_wolframalpha,
}

# Dispacther for messages from the users.
@client.async_event
def on_message(message):
    if message.author.bot:
        return

    cmd, arg = parse_command(message.content)
    if not cmd:
        return

    handler = commands.get(cmd)
    if handler:
      yield from handler(message, arg)


# Create the local Dirs if needed.
file_bool = os.path.exists("./bot_files")
if not file_bool:
    os.makedirs('./bot_files')
# Simple client login and starting the bot.
client.run('')
