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
# Improve blackjack

import os
import time
import json
import discord
import random
import urllib
import pickle
import cleverbot
from contextlib import suppress
import enchanting_chances as en
from BingTranslator import Translator
from bs4 import BeautifulSoup
from asyncio import sleep
import aiohttp
from lxml.html.soupparser import fromstring
from difflib import SequenceMatcher
import wolframalpha
import threading
import emoji
import osu
import database as db
import datetime

client = discord.Client()
wolframalpha_client = wolframalpha.Client(os.environ['WOLFRAM_ALPHA_APPID'])
API_KEY = os.environ['OPEN_WEATHER_APPID']
token = os.environ['LEMONBOT_TOKEN']
client_id = os.environ['BING_CLIENTID']
client_secret = os.environ['BING_SECRET']

BANK_PATH = './bot_files/lemon_bot_bank.pkl'
BET_PATH = './bot_files/lemon_bot_bets.pkl'

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

BOT_ANSWERS = ["My choice is:", "I'll choose:", "I'm going with:", "The right choice is definately:",
               "If I had to choose, I'd go with:",
               "This one is obvious. It is:", "This one is easy:", "Stupid question. It's:", "The correct choice is:",
               "Hmm. I'd go with:", "Good question. My choice is:"]
bjlist = []
hicards = ['K','A','J','Q','10']
SLOT_PATTERN = [
    emoji.FOUR_LEAF_CLOVER,
    emoji.FOUR_LEAF_CLOVER,
    emoji.MONEY_BAG,
    emoji.MONEY_BAG,
    emoji.MONEY_BAG,
    emoji.POOP,
    emoji.CHERRIES,
    emoji.LEMON,
    emoji.GRAPES,
    emoji.CHERRIES,
    emoji.LEMON,
    emoji.GRAPES,
    emoji.CHERRIES,
    emoji.LEMON,
    emoji.GRAPES,
    emoji.CHERRIES,
    emoji.LEMON,
    emoji.GRAPES,
    emoji.CHERRIES,
    emoji.LEMON,
    emoji.GRAPES,
    emoji.WATERMELON,
    emoji.WATERMELON,
    emoji.WATERMELON,
    emoji.WATERMELON,
]

def get_balance(user):
    bank = build_dict(BANK_PATH)
    return bank.get(str(user), 0)

def add_money(user, amount):
    total = get_balance(user) + amount
    bank = build_dict(BANK_PATH)
    bank[str(user)] = max(0, total)
    save_obj(bank, BANK_PATH)

def get_bet(user):
    bets = build_dict(BET_PATH)
    return bets.get(str(user), 0)

def set_bet(user, amount):
    bets = build_dict(BET_PATH)
    bets[str(user)] = max(0, amount)
    save_obj(bets, BET_PATH)

def parse(input):
    languages = ['fi', 'en', 'ru', 'se']
    args = input.split(' ', 2)
    if len(args) < 3:
        return ['auto', 'fi', input]
    if args[0] in languages and args[1] in languages:
        return args
    return ['auto', 'fi', input]

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
    cmd, *arg = content.strip('!').split(' ', 1)
    return cmd.lower(), arg[0] if arg else None


# function to call the BDO script and relay odds on enchanting.
async def cmd_enchant(message, arg):
    try:
        raw_data = arg.split(' ')
        enchanting_results = en.run_the_odds(raw_data[0], raw_data[1])
        await client.send_message(message.channel, enchanting_results)
    except Exception:
        await client.send_message(message.channel, 'Use the Format --> !enchant target_level fail_stacks')

# Function to search for a youtube video and return a link.
async def cmd_youtube(message, text_to_search):
    link_list = []
    print('Searching YouTube for: %s' % text_to_search)
    query = urllib.parse.quote(text_to_search)
    url = "https://www.youtube.com/results?search_query=" + query
    async with aiohttp.get(url) as r:
        html = await r.text()
        soup = BeautifulSoup(html, "lxml")
        for vid in soup.findAll(attrs={'class': 'yt-uix-tile-link'}):
            link_list.append('https://www.youtube.com' + vid['href'])
        random_link = random.choice(link_list)
        await client.send_message(message.channel, random_link)

# Rolling the odds for a user.
async def cmd_roll(message, arg):
    # Default to !roll 100 because why not
    if arg is None:
        await cmd_roll(message, "100")
        return

    if not arg.isdigit():
        await client.send_message(message.channel, 'You need to type a number, for example !roll 100.')
        return
    if arg == 0:
        await client.send_message(message.channel, "There must be at least two numbers to choose from.")
        return
    if len(arg) > 20:
        await client.send_message(message.channel, 'Sorry, the maximum amount of digits is 20.')
        return
    rand_roll = random.randint(0, int(arg))
    await client.send_message(message.channel, '%s your roll is %s' % (message.author, rand_roll))

# eight ball function to return the magic of the eight ball.
async def cmd_8ball(message, question):
    prediction = random.choice(EIGHT_BALL_OPTIONS)
    await client.send_message(message.channel, 'Question: [%s], %s' % (question, prediction))

# Function to get the weather by zip code. using: http://openweathermap.org
# you can get an API key on the web site.
async def cmd_weather(message, zip_code):
    if not zip_code:
        await client.send_message(message.channel, "You must specify a city, eq. Säkylä")
        return
    link = 'http://api.openweathermap.org/data/2.5/weather?q=%s&APPID=%s' % (zip_code, API_KEY)
    async with aiohttp.get(link) as r:
        data = await r.json()
        location = data['name']
        F = data['main']['temp'] * 1.8 - 459.67
        C = (F - 32) * 5 / 9
        status = data['weather'][0]['description']
        payload = 'In %s: Weather is: %s, Temp is: %s°C  (%s°F) ' % (location, status, round(C), round(F))
        await client.send_message(message.channel, payload)

async def domath(channel, input):
    if len(input) < 3:
        await client.send_message(channel, "Error: You need to input at least 3 digits, for example !math 5 + 5")
        return
    for char in input:
        if char not in '1234567890+-/*':
            await client.send_message(channel, "Error: Your calculation containts invalid character(s): %s" % char)
            return
    if input[0] in '/*+-':  # Can't make -9 or /9 etc
        await client.send_message(channel, "Error: First digit must be numeric, for example !math 5 + 5.)")
        return
    i = 1
    i2 = 2
    for char in range(len(input) - 1):
        if input[i] not in '+-/*':
            await client.send_message(channel, 'Error: Input after a number must be an operator, '
                                                       'you have: %s and %s.', input[i2], input[i2])
            return
        if input[i2] not in '1234567890':
            await client.send_message(channel, 'Error: Input after operator must be numeric, '
                                                       'you have: %s and %s' % (input[i], input[i2]))
            return
        if input[-1] not in '1234567890':
            await client.send_message(channel, "Error: No digit specified after operator (last %s)" % (input[-1]))
            return
        i += 2
        i2 += 2
        if i > (len(input) - 2):
            break
    return eval(input)

# Simple math command.
async def cmd_math(message, arg):
    if not arg:
        await client.send_message(message.channel, 'You need to specify at least 3 digits, for example !math 5 + 5.)')
        return
    result = await domath(message.channel, arg.replace(" ",""))
    await client.send_message(message.channel, '%s equals to %s' % (arg, result))

async def cmd_translate(message, arg):
    tolang,text = arg.split(' ', 1)
    if len(text) > 100: #maybe it's wise to put a limit on the lenght of the translations
        await client.send_message(message.channel, "Your text is too long: Max allowed is 100 characters.")
        return
    translator = Translator(client_id, client_secret)
    translation = translator.translate(text, tolang)
    await client.send_message(message.channel, translation)

# Ask clever bot a question.
async def cmd_cleverbot(message, question):
    if not question:
        await client.send_message(message.channel, "You must specify a question!")
    cb1 = cleverbot.Cleverbot()
    answer = cb1.ask(question)
    await client.send_message(message.channel, answer)

# this Spanks the user and calls them out on the server, with an '@' message.
# Format ==> @User has been, INSERT_ITEM_HERE
async def cmd_spank(message, target_user):
    punishment = random.choice(SPANK_BANK)
    await client.send_message(message.channel, "%s has been, %s by %s" % (target_user, punishment, message.author))

async def cmd_coin(message, _):
    coin = random.choice(["Heads", "Tails"])
    await client.send_message(message.channel, "Just a moment, flipping the coin...")
    await sleep(.5)
    await client.send_message(message.channel, "The coin lands on: %s" % coin)
    return coin

async def cmd_help(message, _):
    await client.send_message(message.channel, 'https://github.com/thomaxius-and-co/lemon_bot_discord/blob/master/README.md#commands')

# Function to clear a chat Channel.
async def cmd_clear(message, _):
    perms = message.channel.permissions_for(message.author)
    if perms.administrator:
        await client.purge_from(message.channel)
    else:
        await client.send_message(message.channel, 'https://youtu.be/gvdf5n-zI14')

# Delete 50 of bots messages
async def cmd_clearbot(message, _):
    #It might be wise to make a separate command for each type of !clear, so there are no chances for mistakes.
    perms = message.channel.permissions_for(message.author)
    def isbot(message):
        return message.author == client.user and message.author.bot #Double check just in case the bot turns sentinent and thinks about deleting everyone's messages
    if perms.administrator:
        await client.purge_from(message.channel, limit=50, check=isbot)
    else:
        await client.send_message(message.channel, 'https://youtu.be/gvdf5n-zI14')

# Function to play the slots
async def cmd_slots(message, _):
    player = message.author
    wheel_list = []
    results_dict = {}
    count = 1
    stay = False
    winnings = 0
    bet = get_bet(player)
    if bet < 1:
        await client.send_message(message.channel, 'You need set a valid bet, Example: !bet 5')
        return

    balance = get_balance(player)
    if balance == 0:
        await client.send_message(message.channel, 'You need to run the !loan command.')
        return

    if bet > balance:
        await client.send_message(message.channel,
                                       'Your balance of $%s is to low, lower your bet amount of $%s' % (
                                       balance, bet))
        return
    if bet > 1000:
        await client.send_message(message.channel,
                                       'Please lower your bet. (The maximum allowed bet for slots is 1000.)')
        return
    add_money(player, -bet)
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
    for k, v in results_dict.items():
        if (k == emoji.CHERRIES or k == emoji.LEMON or k == emoji.GRAPES) and v == 4:
            winnings = bet * 25
            break
        if (k == emoji.CHERRIES or k == emoji.LEMON or k == emoji.GRAPES) and v == 3:
            winnings = bet * 10
            break
        if (k == emoji.WATERMELON) and v == 3:
            winnings = bet * 20
            break
        if (k == emoji.WATERMELON) and v == 4:
            winnings = bet * 50
            break
        if k == emoji.MONEY_BAG and v == 4:
            winnings = bet * 500
            break
        if k == emoji.MONEY_BAG and v == 3:
            winnings = bet * 100
            break
        if k == emoji.FOUR_LEAF_CLOVER and v == 4:
            winnings = bet * 1000
            break
        if k == emoji.FOUR_LEAF_CLOVER and v == 3:
            winnings = bet * 200
            break
        if k == emoji.POOP and v == 4:
            winnings = bet * 10000
            for spam in range (0, 10):
                await client.send_message(message.channel,
                                          'HE HAS DONE IT! %s has won the jackpot! of %s!' % (player, winnings))
                await sleep(1)
    wheel_payload = '%s Bet: $%s --> | ' % (player, bet) + ' - '.join(
        wheel_list) + ' |' + ' Outcome: $%s' % winnings
    await client.send_message(message.channel, wheel_payload)
    while winnings > 0 and not stay:
        doubletimes = +1
        if doubletimes == 5:
            await client.send_message(message.channel,
                                      'You have reached the doubling limit! You won %s' % (winnings))
            break
        await client.send_message(message.channel,
                                  'You won %s! Would you like to double? (Type !double or !take)' % (winnings))
        winnings, stay = await askifdouble(message, winnings)
    if winnings > 0:
        add_money(player, winnings)

async def askifheadsortails(message, winnings):
    while True:
        answer = await client.wait_for_message(timeout=60, author=message.author, check=check)
        if answer and answer.content.lower() == 'heads' or answer.content.lower() == 'tails':
            coin = await cmd_coin(message, winnings)
            if coin.lower() == answer.content.lower():
                winnings *= 2
                await client.send_message(message.channel,
                                          "You win! $%s" % winnings)
                return winnings
            else:
                await client.send_message(message.channel,
                                          "You lose!")
                winnings = 0
                return winnings
def check(message):
    return message.author == message.author

async def askifdouble(message, winnings):
    stay = True
    player = message.author
    answer = await client.wait_for_message(timeout=15, author=player, check=check)
    if answer and answer.content.lower() == '!double':
        await client.send_message(message.channel,
                                  "Type 'heads' or 'tails'")
        winnings = await askifheadsortails(message, winnings)
        if winnings > 0:
            stay = False
            return winnings, stay
    elif answer is None or answer.content.lower() == '!slots' or answer.content.lower() == '!take':
        await client.send_message(message.channel,
                                  "You took the money ($%s)" % winnings)
        return winnings, stay
    return winnings, stay


async def getrandomdate(date2):
    date1 = datetime.date.today().toordinal()
    date2 = date2
    if date1 == date2:
        fromdate = datetime.datetime.combine(datetime.date.fromordinal(date2), datetime.datetime.min.time())
        return fromdate
    diff = random.randrange(int(date1) - int(date2))
    fromdate = datetime.datetime.combine(datetime.date.fromordinal(date2 + diff), datetime.datetime.min.time())
    return fromdate

async def sanitize(msg, id):
    while id:
        user = await client.get_user_info(id[0])
        msg = msg.replace(id[0], user.name)
        id.remove(id[0])
    return msg.replace('<','').replace('>','')

async def cmd_randomquote(themessage, input):
    channel = themessage.channel
    if input:
        for server in client.servers:
            for channel in server.channels:
                if channel.name == input:
                    channel = channel
                    break
            else:
                await client.send_message(themessage.channel, "Sorry, channel not found: %s, "
                                                              "or you lack the permissions for that channel." % input)
                return
    reply_message = await client.send_message(themessage.channel, 'Please wait while I go and check the archives.')
    hugelist = []
    for x in range(10):
        date = await getrandomdate(channel.created_at.toordinal())
        async for message in client.logs_from(channel, limit=10, after=date):
            if not message.author.bot:
                if len(message.content) > 10:
                    if not message.content.startswith('!'):
                        hugelist.append(message)
    if len(hugelist) == 0:
        msg = 'Sorry, no quotes could be found'
        if input:
            msg = ('Sorry, no quotes could be found from channel: %s' % input)
        await client.edit_message(reply_message, msg)
        return
    message = random.choice(hugelist)
    msg = message.content
    id = message.raw_mentions
    if id:
        msg = await sanitize(msg, id) #made a separate function for this cause henry likes separate functions
    author = message.author
    reply = '%s, -- %s, %s' % (msg, author, message.timestamp.replace(tzinfo=None))
    await client.edit_message(reply_message, reply)

# Function to set a users bet.
async def cmd_bet(message, amount):
    if not amount.isdigit():
        await client.send_message(message.channel,
                                  'Amount must be numeric and positive, for example !bet 10.')
        return
    amount = int(amount)
    if amount < 1:
        await client.send_message(message.channel, 'You need to enter a positive integer, minimum being 1. Example: !bet 5')
        return
    set_bet(message.author, amount)
    await client.send_message(message.channel, '%s, set bet to: %s' % (message.author, amount))

# Function to look at the currently Set bet.
async def cmd_reviewbet(message, _):
    bet = get_bet(message.author)
    await client.send_message(message.channel,
                                       '%s is currently betting: %s' % (message.author, bet))

# function to loan players money -- ONLY UP TO -- > $50 dollars
async def cmd_loan(message, _):
    balance = get_balance(message.author)
    if balance >= 50:
        await client.send_message(message.channel, '%s you have $%s, you do not need a loan.' % (message.author, balance))
        return

    add_money(message.author, 50 - balance)
    if balance == 0:
        await client.send_message(message.channel, '%s, added $50' % message.author)
    else:
        await client.send_message(message.channel, '%s, added up to $50' % message.author)

# Function to look up a users Money!
async def cmd_bank(message, _):
    balance = get_balance(message.author)
    await client.send_message(message.channel, 'User: %s, Balance: $%s' % (message.author, balance))
    if balance == 0:
        await client.send_message(message.channel, "Looks like you don't have any money, try the !loan command.")

async def getcardrank(card, hand, score):
    rank = card
    letter = card
    if card in ['K', 'J', 'Q', '10']:
        rank = 10
    if card == 'A':
        if score > 10:
            rank = 1
            letter = 'a'
        else:
            rank = 11
    if 'A' in hand and (score + int(rank)) > 21:
        score -= 10
        for n, i in enumerate(hand):
            if i == 'A':
                hand[n] = 'a'
    score += int(rank)
    return int(rank), score, hand, letter

async def dealcard(cards, hand, nofcards, score):
    for x in range(nofcards):
        card1 = cards.pop()
        rank, score, hand, letter = await getcardrank(card1[0], hand, score)
        suit = card1[1]
        hand += [rank, suit, letter]
    return hand, score

async def dealhand(message, score, cards, broke, hand, player=True):
    if score == 0:
        if player:
            hand, score = await dealcard(cards, hand, 2, score)
            await sleep(0.2)
            await domessage(message, hand[1], hand[2], hand[4], hand[5], score, broke, firstround=True)
            return score, hand
        else:
            hand, score = await dealcard(cards, hand, 2, score)
            await domessage(message, hand[1], hand[2], None, None, score, None, player=False, firstround=True)
            return hand[0], hand
    else:
        if player:
            hand, score = await dealcard(cards, hand, 1, score)
            await sleep(0.2)
            await domessage(message, hand[-2], hand[-1], None, None, score, broke)
            return score, hand
        else:
            hand, score = await dealcard(cards, hand, 1, score)
            await sleep(0.2)
            await domessage(message, hand[-2], hand[-1], None, None, score, None, player=False)
            return score, hand

async def domessage(message, card1suit, card1letter, card2suit, card2letter, score, broke,
                    firstround=False, player=True):
    if firstround:
        if player:
            msg = 'Available options: !hitme, !stay, !surrender, !doubledown'
            if broke:
                msg = 'Available options: !hitme, !stay, !surrender'
            if score == 21:
                msg = 'Blackjack!'
            await client.send_message(message.channel,
                                      "DEALER: %s: Your cards: \n"
                                      "%s                     %s\n"
                                      "    %s     and    %s\n"
                                      "        %s                     %s        (%s total)\n"
                                      "%s" % (
                                      message.author, card1letter.upper(), card2letter.upper(), card1suit, card2suit, card1letter.upper(),
                                      card2letter.upper(), score, msg))
        else:
            await client.send_message(message.channel,
                                      "DEALER: Dealer's card is:\n"
                                      " %s\n"
                                      "    %s\n"
                                      "        %s" % (
                                          card1letter.upper(), card1suit, card1letter))
    else:
        if player:
            msg = 'Available options: !hitme, !stay'
            await client.send_message(message.channel,
                "DEALER: Your card is: \n"
                "%s\n"
                "    %s\n"
                "         %s       total: %s\n"
                "%s" % (
                    card1letter.upper(), card1suit, card1letter.upper(), score, msg))
        else:
            await client.send_message(message.channel,
                                      "DEALER: Dealer's card is: \n"
                                      "%s\n"
                                      "    %s\n"
                                      "         %s\n"
                                      "                total: %s" % (
                                          card1letter.upper(), card1suit, card1letter.upper(), score))


async def getresponse(message, score, cards, broke, hand):
    answer = await client.wait_for_message(timeout=25, author=message.author, check=check)
    if answer and answer.content.lower() == '!hitme':
        score, hand = await dealhand(message, score, cards, broke, hand)
        stay = False
        return score, stay, hand
    if answer and answer.content.lower() == '!doubledown':
        if broke:
            await client.send_message(message.channel,
                                      "You don't have enough money for doubledown.")
            stay = False
            return score, stay, hand
        if len(hand) > 6:
            await client.send_message(message.channel,
                                      "Doubledown is only available on the first round.")
            stay = False
            return score, stay, hand
        stay = 'doubledown'
        broke = True
        score, hand = await dealhand(message, score, cards, broke, hand)
        return score, stay, hand
    if answer and answer.content.lower() == '!surrender':
        if len(hand) > 6:
            await client.send_message(message.channel,
                                      "Surrender is only available on the first round.")
            stay = False
            return score, stay, hand
        stay = 'surrender'
        return score, stay, hand
    elif answer is None or answer.content.lower() == '!stay':
        stay = True
        return score, stay, hand
    stay = False
    return score, stay, hand


async def cmd_blackjack(message, _):
    broke = False
    blackjack = False
    cards = await makedeck(blackjack=True)
    phand = []
    dhand = []
    if message.author in bjlist:
        await client.send_message(message.channel,
                                  'Cannot play: You have an unfinished game.')
        return
    bet = get_bet(message.author)
    if bet < 1:
        await client.send_message(message.channel, 'You need set a valid bet, Example: !bet 5')
        return

    balance = get_balance(message.author)
    if balance == 0:
        await client.send_message(message.channel, 'You need to run the !loan command.')
        return
    if bet > balance:
        await client.send_message(message.channel,
                                       'Your balance of $%s is to low, lower your bet amount of $%s' % (
                                           balance, bet))
        return
    if bet * 2 > balance:
        broke = True
    stay = False
    bjlist.append(message.author)
    pscore = 0
    dscore = 0
    dscore, dhand = await dealhand(message, dscore, cards, broke, dhand, player=False)
    pscore, phand = await dealhand(message, pscore, cards, broke, phand)
    if pscore == 21:
        blackjack = True
        bet *= 1.5
        if dhand[2] not in hicards:
            await dofinalspam(message, pscore, dscore, int(bet), blackjack=True)
            return
        else:
            dscore += dhand[-3]
            await domessage(message, dhand[-2], dhand[-1], None, None, dscore, broke, player=False)
    while not blackjack:
        if stay is True or pscore == 21 or pscore > 21:
            break
        pscore, stay, phand = await getresponse(message, pscore, cards, broke, phand)
        if stay == 'doubledown':
            bet += bet
            break
        if stay == 'surrender':
            bet /= 2
            await dofinalspam(message, pscore, dscore, int(bet), surrender=True)
            return
    if not blackjack and len(dhand) == 6 and pscore < 21:
        dscore += dhand[-3]
        await domessage(message, dhand[-2], dhand[-1], None, None, dscore, broke, player=False)
    while 17 > dscore < pscore and not blackjack:
        if pscore > 21:
            break
        await sleep(0.2)
        dscore, dhand = await dealhand(message, dscore, cards, broke, dhand, player=False)
        if dscore == pscore and dscore > 16:
            print("If dscore is not over 16, this shouldnt happen", dscore, pscore)
            break
    await dofinalspam(message, pscore, dscore, bet)


async def dofinalspam(message, pscore, dscore, bet, blackjack=False, surrender=False):
    bjlist.remove(message.author)
    if surrender:
        await client.send_message(message.channel,
                                  'DEALER: %s: Player surrenders and receives half of his bet back. ($%s)' % (
                                  message.author, bet))
        winnings = -bet
        add_money(message.author, winnings)
        return

    if pscore > 21:
        await sleep(0.2)
        winnings = -bet
        add_money(message.author, winnings)
        await client.send_message(message.channel,
                                  'DEALER: %s: Player is BUST! House wins! (Total score: %s) \n You lose $%s' % (
                                  message.author, pscore, bet))
        return

    if blackjack:
        await sleep(0.2)
        await client.send_message(message.channel, 'DEALER: %s: Player wins with a blackjack! \n You win $%s' %
                                  (message.author, int(bet)))
        winnings = int(bet)
        add_money(message.author, winnings)
        return

    if dscore > 21:
        await sleep(0.2)
        winnings = bet
        add_money(message.author, winnings)
        await client.send_message(message.channel,
                                  'DEALER: %s: Dealer is bust! Player wins! Player score %s, dealer score %s \n You win $%s' % (
                                  message.author, pscore, dscore, bet))
        return
    if dscore > pscore:
        await sleep(0.2)
        winnings = -bet
        add_money(message.author, winnings)
        await client.send_message(message.channel,
                                  'DEALER: %s: House wins! Player score %s, dealer score %s \n You lose $%s' % (
                                  message.author, pscore, dscore, bet))
        return
    if pscore > dscore:
        await sleep(0.2)
        winnings = bet
        add_money(message.author, winnings)
        await client.send_message(message.channel,
                                  'DEALER: %s: Player wins! Player score %s, dealer score %s \n You win $%s' % (
                                  message.author, pscore, dscore, bet))
    if pscore == dscore:
        await sleep(0.2)
        await client.send_message(message.channel,
                                  'DEALER: %s: It is a push! Player: %s, house %s. Your bet of %s is returned.' % (
                                  message.author, pscore, dscore, bet))
        return

# Function to lookup the money and create a top 5 users.
async def cmd_leader(message, _):
    bank_dict = build_dict(BANK_PATH)
    counter = 0
    leader_list = []
    for key in sorted(bank_dict, key=bank_dict.get, reverse=True)[:5]:
        counter += 1
        leader_list.append('#%s - %s - $%s' % (counter, key, bank_dict[key]))
    await client.send_message(message.channel, '  |  '.join(leader_list))

async def cmd_wolframalpha(message, query):
    print("Searching WolframAlpha for '%s'" % query)

    await client.send_typing(message.channel)

    try:
        res = wolframalpha_client.query(query)
        answer = next(res.results).text
        await client.send_message(message.channel, answer)
    except Exception:
        await client.send_message(message.channel, 'I don\'t know how to answer that')

async def makedeck(blackjack=True):
    cards = []
    value = 1
    if blackjack:
        value = 6
    for x in range(0, value):
        for suit in [emoji.SPADES, emoji.HEARTS, emoji.CLUBS, emoji.DIAMONDS]:
            for rank in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']:
                cards.append((rank, suit))
    random.shuffle(cards)
    return cards

async def cmd_version(message, args):
    # todo: Make this function update automatically with some sort of github api.. Version
    # number should be commits divided by 1000.
    await client.send_message(message.channel, "\n".join([
        "Current version of the bot: 0.09",
        "Changelog: Improvements to slots and blackjack",
    ]))

async def cmd_pickone(message, args):
    if not args:
        await client.send_message(message.channel, 'You need to specify at least 2 arguments separated'
                                                        ' by a comma, for example !pickone pizza, burger.')
        return
    choices = args.split(",")
    if len(choices) < 2:
        await client.send_message(message.channel, 'You need to specify at least 2 arguments separated'
                                                        ' by a comma, for example !pickone pizza, burger.')
        return
    jibbajabba = random.choice(BOT_ANSWERS)
    choice = random.choice(choices)
    await client.send_message(message.channel, '%s %s' % (jibbajabba, choice.strip()))

async def cmd_osu(message, user):
    results = await osu.user(user)
    if not results:
        await client.send_message(message.channel, "User %s not found" % user)
        return

    data = results[0]
    username = data["username"]
    rank = int(data["pp_rank"])
    pp = round(float(data["pp_raw"]))
    acc = float(data["accuracy"])

    reply = "%s (#%d) has %d pp and %.2f%% acc" % (username, rank, pp, acc)
    await client.send_message(message.channel, reply)

async def cmd_sql(message, arg):
    perms = message.channel.permissions_for(message.author)
    if not perms.administrator:
        await client.send_message(message.channel, 'https://youtu.be/gvdf5n-zI14')
        return

    if arg is None:
        return

    with db.connect() as c:
        c.execute(arg)
        results = list(c.fetchmany(10))

    result_strs = map(str, results)
    msg = "\n".join(result_strs)
    await client.send_message(message.channel, "```%s```" % msg)

commands = {
    'sql': cmd_sql,
    'enchant': cmd_enchant,
    'youtube': cmd_youtube,
    'roll': cmd_roll,
    '8ball': cmd_8ball,
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
    'translate': cmd_translate,
    'blackjack': cmd_blackjack,
    'pickone': cmd_pickone,
    'version': cmd_version,
    'clearbot': cmd_clearbot,
    'osu': cmd_osu,
    'randomquote': cmd_randomquote
}

async def suggestcmd(channel, arg, actualcmd):
    await client.send_message(channel,
                              "Command not found: %s - did you mean !%s?" % (arg, actualcmd))

async def checkspelling(channel, arg):
    allcommands = list(commands.items())
    i = 0
    for actualcmd in allcommands:
        similarity = SequenceMatcher(None, allcommands[i][0], arg).quick_ratio()
        if similarity > 0.7:
            actualcmd = allcommands[i][0]
            await suggestcmd(channel, arg, actualcmd)
            return
        i += 1

# Dispacther for messages from the users.
@client.event
async def on_message(message):
    if message.author.bot:
        return

    cmd, arg = parse_command(message.content)
    if not cmd:
        return
    handler = commands.get(cmd)
    if handler:
        await handler(message, arg)
        return
    if ((len(message.content) - 3) > len(max(commands, key = len))):
        #This is to prevent checkspelling being called when someone tries to be funny and, for example, does !flkflklsdklfsdk
        return
    await checkspelling(message.channel, cmd)

@client.event
async def on_ready():
    db.insert_start_time("Server started")

# Create the local Dirs if needed.
file_bool = os.path.exists("./bot_files")
if not file_bool:
    os.makedirs('./bot_files')

# Database schema has to be initialized before running the bot
db.initialize_schema()

# Simple client login and starting the bot.
client.run(token)
