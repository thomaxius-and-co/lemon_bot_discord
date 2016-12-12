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
import json
import discord
import random
import urllib
import cleverbot
import enchanting_chances as en
from BingTranslator import Translator
from bs4 import BeautifulSoup
from asyncio import sleep
import aiohttp
from difflib import SequenceMatcher
import wolframalpha
import psycopg2
import database as db
import command

import archiver
import casino
import osu
import sqlcommands
import feed

client = discord.Client()
wolframalpha_client = wolframalpha.Client(os.environ['WOLFRAM_ALPHA_APPID'])
API_KEY = os.environ['OPEN_WEATHER_APPID']
token = os.environ['LEMONBOT_TOKEN']
client_id = os.environ['BING_CLIENTID']
client_secret = os.environ['BING_SECRET']

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

languages = ['af', 'ar', 'bs-Latn', 'bg', 'ca', 'zh-CHS', 'zh-CHT', 'hr', 'cs', 'da', 'nl', 'en', 'et', 'fi',
             'fr', 'de', 'el', 'ht', 'he', 'hi', 'mww', 'hu', 'id', 'it',
             'ja', 'sw', 'tlh', 'tlh-Qaak', 'ko', 'lv', 'lt', 'ms', 'mt', 'no', 'fa', 'pl', 'pt',
             'otq', 'ro', 'ru', 'sr-Cyrl', 'sr-Latn', 'sk', 'sl', 'es', 'sv', 'th', 'tr', 'uk', 'ur', 'vi', 'cy', 'yua']

def parse(input):
    args = input.split(' ', 2)
    if len(args) < 3:
        return [None, 'en', input]
    if args[0] in languages and args[1] in languages:
        return args
    return [None, 'en', input]

# function to call the BDO script and relay odds on enchanting.
async def cmd_enchant(client, message, arg):
    try:
        raw_data = arg.split(' ')
        enchanting_results = en.run_the_odds(raw_data[0], raw_data[1])
        await client.send_message(message.channel, enchanting_results)
    except Exception:
        await client.send_message(message.channel, 'Use the Format --> !enchant target_level fail_stacks')

# Function to search for a youtube video and return a link.
async def cmd_youtube(client, message, text_to_search):
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
async def cmd_roll(client, message, arg):
    # Default to !roll 100 because why not
    if arg is None:
        await cmd_roll(client, message, "100")
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
async def cmd_8ball(client, message, question):
    prediction = random.choice(EIGHT_BALL_OPTIONS)
    await client.send_message(message.channel, 'Question: [%s], %s' % (question, prediction))

# Function to get the weather by zip code. using: http://openweathermap.org
# you can get an API key on the web site.
async def cmd_weather(client, message, zip_code):
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
        if input[-1] in '+-/*':
            print("Error: No digit specified after operator (last %s)" % (input[-1]))
            return
        i += 2
        i2 += 2
        if i > (len(input) - 2):
            break
    try:
        return eval(input)
    except Exception:
        await client.send_message(channel, "Error: There is an error in your calculation.")
        return

# Simple math command.
async def cmd_math(client, message, arg):
    if not arg:
        await client.send_message(message.channel, 'You need to specify at least 3 digits, for example !math 5 + 5.)')
        return
    result = await domath(message.channel, arg.replace(" ",""))
    if not result:
        return
    await client.send_message(message.channel, '%s equals to %s' % (arg, result))

async def cmd_translate(client, message, arg):
    if len(arg) > 100: #maybe it's wise to put a limit on the lenght of the translations
        await client.send_message(message.channel, "Your text is too long: Max allowed is 100 characters.")
        return
    fromlang, tolang, input = parse(arg)
    translator = Translator(client_id, client_secret)
    translation = translator.translate(input, tolang, fromlang)
    await client.send_message(message.channel, translation)

# Ask clever bot a question.
async def cmd_cleverbot(client, message, question):
    if not question:
        await client.send_message(message.channel, "You must specify a question!")
    cb1 = cleverbot.Cleverbot()
    answer = cb1.ask(question)
    await client.send_message(message.channel, answer)

# this Spanks the user and calls them out on the server, with an '@' message.
# Format ==> @User has been, INSERT_ITEM_HERE
async def cmd_spank(client, message, target_user):
    punishment = random.choice(SPANK_BANK)
    await client.send_message(message.channel, "%s has been, %s by %s" % (target_user, punishment, message.author))

async def cmd_coin(client, message, _):
    coin = random.choice(["Heads", "Tails"])
    await client.send_message(message.channel, "Just a moment, flipping the coin...")
    await sleep(.5)
    await client.send_message(message.channel, "The coin lands on: %s" % coin)
    return coin

async def cmd_help(client, message, _):
    await client.send_message(message.channel, 'https://github.com/thomaxius-and-co/lemon_bot_discord/blob/master/README.md#commands')

# Function to clear a chat Channel.
async def cmd_clear(client, message, _):
    perms = message.channel.permissions_for(message.author)
    if perms.administrator:
        await client.purge_from(message.channel)
    else:
        await client.send_message(message.channel, 'https://youtu.be/gvdf5n-zI14')

# Delete 50 of bots messages
async def cmd_clearbot(client, message, _):
    #It might be wise to make a separate command for each type of !clear, so there are no chances for mistakes.
    perms = message.channel.permissions_for(message.author)
    def isbot(message):
        return message.author == client.user and message.author.bot #Double check just in case the bot turns sentinent and thinks about deleting everyone's messages
    if perms.administrator:
        await client.purge_from(message.channel, limit=50, check=isbot)
    else:
        await client.send_message(message.channel, 'https://youtu.be/gvdf5n-zI14')

async def cmd_wolframalpha(client, message, query):
    print("Searching WolframAlpha for '%s'" % query)

    await client.send_typing(message.channel)

    try:
        res = wolframalpha_client.query(query)
        answer = next(res.results).text
        await client.send_message(message.channel, answer)
    except ConnectionResetError:
        await client.send_message(message.channel, 'Sorry, WolframAlpha is slow as fuck right now')
    except Exception as e:
        print("ERROR", type(e), e)
        await client.send_message(message.channel, 'I don\'t know how to answer that')

async def cmd_version(client, message, args):
    # todo: Make this function update automatically with some sort of github api.. Version
    # number should be commits divided by 1000.
    await client.send_message(message.channel, "\n".join([
        "Current version of the bot: 0.09",
        "Changelog: Improvements to slots and blackjack",
    ]))

async def cmd_pickone(client, message, args):
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

async def cmd_sql(client, message, arg):
    perms = message.channel.permissions_for(message.author)
    if not perms.administrator:
        await client.send_message(message.channel, 'https://youtu.be/gvdf5n-zI14')
        return

    if arg is None:
        return

    def limit_msg_length(template, content):
        max_len = 2000 - len(template % "")
        return template % content.replace("`", "")[:max_len]

    try:
        with db.connect(readonly = True) as c:
            c.execute(arg)
            results = c.fetchmany(100)
            msg = "\n".join(map(str, results))
            msg = limit_msg_length("```%s```", msg)
            await client.send_message(message.channel, msg)
    except (psycopg2.ProgrammingError, psycopg2.InternalError) as err:
        msg = limit_msg_length("```ERROR: %s```", str(err))
        await client.send_message(message.channel, msg)
        return

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
    'clear': cmd_clear,
    'math': cmd_math,
    'wa': cmd_wolframalpha,
    'translate': cmd_translate,
    'pickone': cmd_pickone,
    'version': cmd_version,
    'clearbot': cmd_clearbot,
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

    cmd, arg = command.parse(message.content)
    if not cmd:
        return
    handler = commands.get(cmd)
    if handler:
        await handler(client, message, arg)
        return
    if ((len(message.content) - 3) > len(max(commands, key = len))):
        #This is to prevent checkspelling being called when someone tries to be funny and, for example, does !flkflklsdklfsdk
        return
    await checkspelling(message.channel, cmd)

# Database schema has to be initialized before running the bot
db.initialize_schema()

for module in [archiver, casino, sqlcommands, osu, feed]:
    commands.update(module.register(client))

client.run(token)
