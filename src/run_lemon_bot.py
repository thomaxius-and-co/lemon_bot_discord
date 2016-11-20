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
import wolframalpha
import threading
import emoji
import osu

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
async def cmd_roll(message, _):
    rand_roll = random.randint(0, 100)
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

# Simple math command.
async def cmd_math(message, arg):
    a,b,c = arg.split(' ')
    if b == '+':
        calculation = int(a) + int(c)
    if b == '-':
        calculation = int(a) - int(c)
    if b == '*':
        calculation = int(a) * int(c)
    if b == '/':
        calculation = int(a) / int(c)
    await client.send_message(message.channel, '%s %s %s is %s' % (a, b, c, calculation))

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
    await client.send_message(message.channel, 'https://github.com/Thomaxius/lemon_bot_discord')

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
            spam = 0
            while spam > 10:
                await client.send_message(message.channel,
                                          'HE HAS DONE IT! %s has won the jackpot! of %s!' % (player, winnings))
                await sleep(1)
                spam =+ 1
    wheel_payload = '%s Bet: $%s --> | ' % (player, bet) + ' - '.join(
        wheel_list) + ' |' + ' Outcome: $%s' % winnings
    await client.send_message(message.channel, wheel_payload)
    while winnings > 0 and not stay:
        doubletimes = +1
        if doubletimes == 5:
            await client.send_message(message.channel,
                                      'You have reached the doubling limit! You won %s' % (winnings))
            stay = True
            break
        await client.send_message(message.channel,
                                  'You won %s! Would you like to double? (Type !double or !take)' % (winnings))
        winnings, stay = await askifdouble(message, winnings)
    if winnings > 0:
        add_money(player, winnings)

def check(message):
    return message.author == message.author

async def askifdouble(message, winnings):
    stay = True
    player = message.author
    answer = await client.wait_for_message(timeout=15, author=player, check=check)
    if answer and answer.content.lower() == '!double':
        await client.send_message(message.channel,
                                  "Type 'heads' or 'tails'")
        answer = await client.wait_for_message(timeout=25, author=player, check=check)
        if answer and answer.content.lower() == 'heads' or answer.content.lower() == 'tails':
            coin = await cmd_coin(message, winnings)
            if coin.lower() == answer.content.lower():
                winnings *= 2
                await client.send_message(message.channel,
                                          "You win! %s" % winnings)
                stay = False
                return winnings, stay
            else:
                await client.send_message(message.channel,
                                          "You lose!")
                winnings = 0
                return winnings, stay
    elif answer is None or answer.content.lower() == '!take' or answer.content.lower() == '!slots': #I'm tired and cannot think of any other way. Just inputting anything to stay sounds a bit messy.
        await client.send_message(message.channel,
                                  "You took the money (%s)" % winnings)
        return winnings, stay
    else:
        return winnings, stay



# Function to set a users bet.
async def cmd_bet(message, amount):
    try:
        amount = int(amount)
        if amount < 0:
            await client.send_message(message.channel, 'You need to enter a positive integer, Example: !bet 5')
            return
    except Exception:
        await client.send_message(message.channel, 'You need to enter a positive integer, Example: !bet 5')
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

async def getcardrank(card, score):
    if card in ['Q', 'K', 'J']:
        rank = 10
        return rank
    if card == 'A' and score > 10:
        rank = 1
        return rank
    if card == 'A' and score < 11:
        rank = 11
        return rank
    else:
        rank = card
    return int(rank)

async def dealcard(cards, score):
    card1 = cards.pop()
    rank = await getcardrank(card1[0], score)
    suit = card1[1]
    return rank, suit

async def dealhand(message, score, cards, firstround=False, player=True, dealer=False):
    if player and firstround:
        card1rank, card1suit = await dealcard(cards, score)
        card2rank, card2suit = await dealcard(cards, score)
        score = card1rank + card2rank
        await sleep(0.2)
        await client.send_message(message.channel,
                                           "DEALER: %s: Your cards: \n"
                                           "%s                     %s\n"
                                           "    %s     and    %s\n"
                                           "        %s                     %s        (%s total) "
                                           "\n Type !hitme for more cards, !stay to stay and !doubledown for double down." % (message.author, card1rank, card2rank, card1suit, card2suit, card1rank, card2rank, score))

        return score
    if player and not firstround:
        card1rank, card1suit = await dealcard(cards, score)
        score += card1rank
        await sleep(0.2)
        await client.send_message(message.channel,
                                  "DEALER: Your card is: \n"
                                  "%s\n"
                                  "    %s\n"
                                  "        %s       total: %s"
                                  "\n Type !hitme for more cards,  !stay to stay and !doubledown for double down." % (
                                      card1rank, card1suit, card1rank, score))
        return score
    if dealer:
        card1rank, card1suit = await dealcard(cards, score)
        if firstround:
            await client.send_message(message.channel,
                                      "DEALER: Dealer's card is:\n"
                                      "%s\n"
                                      "    %s\n"
                                      "        %s" % (
                                      card1rank, card1suit, card1rank))
            return card1rank
        if not firstround:
            score += card1rank
            await sleep(0.2)
            await client.send_message(message.channel,
                                      "DEALER: Dealer's card is: \n"
                                      "%s\n"
                                      "    %s\n"
                                      "        %s\n"
                                      "                total: %s" % (
                                      card1rank, card1suit, card1rank, score))
            return score

async def getresponse(message, score, cards):
    answer = await client.wait_for_message(timeout=25, author=message.author, check=check)
    if answer and answer.content.lower() == '!hitme':
        score = await dealhand(message, score, cards)
        stay = False
        return score, stay
    if answer and answer.content.lower() == '!doubledown':
        stay = 'doubledown'
        score = await dealhand(message, score, cards)
        return score, stay
    elif answer is None or answer.content.lower() == '!stay':
        stay = True
        return score, stay
    stay = False
    return score, stay


async def cmd_blackjack(message, _):
    cards = await makedeck(blackjack=True)
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
    stay = False
    bjlist.append(message.author)
    pscore = 0
    dscore = 0
    dscore = await dealhand(message, dscore, cards, firstround=True, player=False, dealer=True)
    pscore = await dealhand(message, pscore, cards, firstround=True)
    while pscore < 22:
        if stay is True or pscore == 21:
            break
        if stay == 'doubledown':
            bet += bet
            break
        pscore, stay = await getresponse(message, pscore, cards)
    if pscore > 21:
        await sleep(0.2)
        bjlist.remove(message.author)
        winnings = -bet
        add_money(message.author, winnings)
        await client.send_message(message.channel,
                                  'DEALER: %s: Player is BUST! House wins! (Total score: %s) \n You lose $%s' % (
                                  message.author, pscore, bet))
        return
    while 17 > dscore < pscore:
        await sleep(0.2)
        if dscore == pscore:
            break
        dscore = await dealhand(message, dscore, cards, player=False, dealer=True)
    bjlist.remove(message.author)
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
            for rank in ['2', '3', '4', '5', '6', '7', '9', '10', 'J', 'Q', 'K', 'A']:
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
    if len(results) == 0:
        await client.send_message(message.channel, "User %s not found" % user)
        return

    data = results[0]
    username = data["username"]
    rank = int(data["pp_rank"])
    pp = round(float(data["pp_raw"]))
    acc = float(data["accuracy"])

    reply = "%s (#%d) has %d pp and %.2f%% acc" % (username, rank, pp, acc)
    await client.send_message(message.channel, reply)


commands = {
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
}

async def think(message):
    if emoji.THINKING in message.content:
        await client.add_reaction(message, emoji.THINKING)

# Dispacther for messages from the users.
@client.event
async def on_message(message):
    if message.author.bot:
        return

    await think(message)

    cmd, arg = parse_command(message.content)
    if not cmd:
        return

    handler = commands.get(cmd)
    if handler:
      await handler(message, arg)

# Create the local Dirs if needed.
file_bool = os.path.exists("./bot_files")
if not file_bool:
    os.makedirs('./bot_files')
# Simple client login and starting the bot.
client.run(token)
