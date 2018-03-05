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
import enchanting_chances as en
from BingTranslator import Translator
import asyncio
from asyncio import sleep
import aiohttp
import difflib
import wolframalpha
import database as db
import command
import util
import zlib
import archiver
import casino
import osu
import sqlcommands
import feed
import reminder
import youtube
import lan
import laiva
import steam
import anssicommands
import awards
import logger
import faceit_commands
import muutto
import statistics
import crypto
import status
import emojicommands

log = logger.get("BOT")

client = discord.Client()
wolframalpha_client = wolframalpha.Client(os.environ['WOLFRAM_ALPHA_APPID'])
API_KEY = os.environ['OPEN_WEATHER_APPID']
token = os.environ['LEMONBOT_TOKEN']
bing_client_id = os.environ['BING_CLIENTID']
bing_client_secret = os.environ['BING_SECRET']
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
        await client.send_message(message.channel, 'Use the Format --> ```!enchant target_level fail_stacks```')

# Rolling the odds for a user.
async def cmd_roll(client, message, arg):
    usage = (
        "Usage: `!roll <max>`\n"
        "Rolls a number in range `[0, max]`. Value `max` defaults to `100` if not given.\n"
    )

    # Default to !roll 100 because why not
    arg = arg or '100'

    def valid(arg):
        return arg.isdigit() and int(arg) >= 1

    if not valid(arg):
        await client.send_message(message.channel, usage)
        return

    rand_roll = random.randint(0, int(arg))
    await client.send_message(message.channel, '%s your roll is %s.' % (message.author.name, rand_roll))

# eight ball function to return the magic of the eight ball.
async def cmd_8ball(client, message, question):
    prediction = random.choice(EIGHT_BALL_OPTIONS)
    await client.send_message(message.channel, 'Question: [%s], %s.' % (question, prediction))

# Function to get the weather by zip code. using: http://openweathermap.org
# you can get an API key on the web site.
async def cmd_weather(client, message, zip_code):
    if not zip_code:
        await client.send_message(message.channel, "You must specify a city, eq. Säkylä.")
        return
    link = 'http://api.openweathermap.org/data/2.5/weather?q=%s&APPID=%s' % (zip_code, API_KEY)
    async with aiohttp.ClientSession() as session:
        r = await session.get(link)
        data = await r.json()
        location = data['name']
        F = data['main']['temp'] * 1.8 - 459.67
        C = (F - 32) * 5 / 9
        status = data['weather'][0]['description']
        payload = 'In %s: Weather is: %s, Temp is: %s°C  (%s°F) ' % (location, status, round(C), round(F))
        await client.send_message(message.channel, payload)

async def domath(channel, input):
    if len(input) < 3:
        await client.send_message(channel, "Error: You need to input at least 3 digits, for example: ```!math 5 + 5```")
        return
    for char in input:
        if char not in '1234567890+-/*()^':
            await client.send_message(channel, "Error: Your calculation containts invalid character(s): %s" % char)
            return
    if input[0] in '/*+-':  # Can't make -9 or /9 etc
        await client.send_message(channel, "Error: First digit must be numeric, for example: ```!math 5 + 5```")
        return
    i = 1
    i2 = 2
    for char in range(len(input) - 1):
        if input[-1] in '+-/*':
            log.info("Error: No digit specified after operator (last %s).", input[-1])
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

async def cmd_help(client, message, _):
        await client.send_message(message.channel,
                                  'https://github.com/thomaxius-and-co/lemon_bot_discord/blob/master/README.md#commands')

# Simple math command.
async def cmd_math(client, message, arg):
    if not arg:
        await client.send_message(message.channel,
                                  'You need to specify at least 3 digits, for example: ```!math 5 + 5```')
        return
    result = await domath(message.channel, arg.replace(" ", ""))
    if not result:
        return
    await client.send_message(message.channel, '%s equals to %s' % (arg, result))

async def cmd_translate(client, message, arg):
    usage = (
        "Usage: `!translate [<from> <to>] <text>`\n"
        "If `to` and `from` are not set, automatic detection is attempted and the text translated to english.\n"
        "Maximum of 100 characters is allowed.\n"
    )

    def valid(arg):
        return 0 < len(arg) < 100

    arg = arg.strip()
    if not valid(arg):
        await client.send_message(message.channel, usage)
        return

    fromlang, tolang, input = parse(arg)
    translator = Translator(bing_client_id, client_secret)
    translation = translator.translate(input, tolang, fromlang)
    await client.send_message(message.channel, translation)


# this Spanks the user and calls them out on the server, with an '@' message.
# Format ==> @User has been, INSERT_ITEM_HERE
async def cmd_spank(client, message, target_user):
    punishment = random.choice(SPANK_BANK)
    await client.send_message(message.channel, "%s has been, %s by %s." % (target_user, punishment, message.author.name))

async def cmd_countchars(client, message, input):
    if input:
        await client.send_message(message.channel, "%s: %s character(s), %s word(s)." % (message.author, len(input), len(input.split(" "))))
    else:
        await client.send_message(message.channel, "Usage: !countchars <character(s) and word(s) to be counted>.")

async def cmd_coin(client, message, _):
    coin = random.choice(["Heads", "Tails"])
    await client.send_message(message.channel, "Just a moment, flipping the coin...")
    await sleep(.5)
    await client.send_message(message.channel, "The coin lands on: %s." % coin)
    return coin

# Delete 50 messages from channel
async def cmd_clear(client, message, arg):
    limit = 10
    perms = message.channel.permissions_for(message.author)
    botperms = message.channel.permissions_for(message.channel.server.me)
    if not perms.administrator:
        await client.send_message(message.channel, 'https://youtu.be/gvdf5n-zI14')
        log.info("!CLEAR: User %s access denied" % message.author)
        return
    if not botperms.manage_messages:
        await client.send_message(message.channel, "Error: bot doesn't have permission to manage messages.")
        return
    if arg and arg.isdigit():
        if int(arg) < 1:
            await client.send_message(message.channel, "You need to input a positive amount.")
            return
        limit = int(arg)
    await client.send_message(message.channel, "This will delete %s messages from the channel. Type 'yes' to confirm, "
                                               "or 'no' to cancel." % limit)
    answer = await client.wait_for_message(timeout=60, author=message.author)
    if answer and answer.content.lower() == 'yes':
        try:
            await client.purge_from(message.channel, limit=limit + 3)
            await client.send_message(message.channel,
                                      "%s messages succesfully deleted." % limit)
            log.info("!CLEAR: %s deleted %s messages." % (message.author, limit))
        except discord.errors.HTTPException as e:
            if e.text == "You can only bulk delete messages that are under 14 days old.":
                await client.send_message(message.channel, "You can only delete messages from the past 14 days - "
                                                           " please lower your message amount.")
    elif answer is None or answer.content.lower() == 'no':
        await client.send_message(message.channel,
                                  "Deletion of messages cancelled.")
    return

# Delete 50 of bots messages
async def cmd_clearbot(client, message, arg):
    # It might be wise to make a separate command for each type of !clear, so there are less chances for mistakes.
    limit = 10
    perms = message.channel.permissions_for(message.author)
    botperms = message.channel.permissions_for(message.channel.server.me)

    def isbot(message):
        return message.author == client.user and message.author.bot  # Double check just in case the bot turns sentinent and thinks about deleting everyone's messages

    if not perms.administrator:
        await client.send_message(message.channel, 'https://youtu.be/gvdf5n-zI14')
        return
    if not botperms.manage_messages:
        await client.send_message(message.channel, "Error: bot doesn't have permission to manage messages.")
        return
    if arg and arg.isdigit():
        limit = int(arg)
    await client.send_message(message.channel,
                              "This will delete %s of **bot's** messages from the channel. Type 'yes' to confirm, "
                              "or 'no' to cancel." % limit)
    answer = await client.wait_for_message(timeout=60, author=message.author)
    if answer and answer.content.lower() == 'yes':
        try:
            await client.purge_from(message.channel, limit=limit + 3, check=isbot)
            await client.send_message(message.channel,
                                      "%s bot messages succesfully deleted." % limit)
            log.info("!CLEARBOT: %s deleted %s bot messages." % (message.author, limit))
        except discord.errors.HTTPException as e:
            if e.text == "You can only bulk delete messages that are under 14 days old.":
                await client.send_message(message.channel, "You can only delete messages from the past 14 days - "
                                                           " please lower your message amount.")
    elif answer is None or answer.content.lower() == 'no':
        await client.send_message(message.channel,
                                  "Deletion of messages cancelled.")
    return

async def cmd_wolframalpha(client, message, query):
    usage = (
        "Usage: `!wa <query>`\n"
        "Searches WolframAlpha with given query\n"
    )

    def valid(query):
        return len(query.strip()) > 0

    log.info("Searching WolframAlpha for '%s'", query)

    if not valid(query):
        await client.send_message(message.channel, usage)
        return

    await client.send_typing(message.channel)

    try:
        res = wolframalpha_client.query(query)
        answer = next(res.results).text
        await client.send_message(message.channel, answer)
    except ConnectionResetError:
        await client.send_message(message.channel, 'Sorry, WolframAlpha is slow as fuck right now.')
    except Exception as e:
        log.error("Error querying WolframAlpha: {0} {1}".format(type(e), e))
        await client.send_message(message.channel, 'I don\'t know how to answer that.')

async def cmd_version(client, message, args):
    # todo: Make this function update automatically with some sort of github api.. Version
    # number should be commits divided by 1000.
    await client.send_message(message.channel, "\n".join([
        "Current version of the bot: 0.09",
        "Changelog: Improvements to slots and blackjack",
    ]))

def pos_in_string(string, arg):
    return string.find(arg)

async def cmd_add_censored_word(client, message, input):
    perms = message.channel.permissions_for(message.author)
    if not perms.administrator:
        await client.send_message(message.channel, 'You do not have permissions for this command.')
        return
    if not input or (not input[0:6].startswith('words=')):
        await client.send_message(message.channel, 'Usage: !addcensoredword **words**=word1, word2, word3, word4 '
                                                   '**exchannel**=Main **infomessage**=Profanity is not allowed.\n '
                                                   'If no channel or message is specified, no channels will be '
                                                   'excluded and default info message will be used.')
        return
    bannedwords, exchannel, infomessage = parse_censored_word_message(input)
    if ("!deletecensoredwords") in bannedwords.lower() or ("!listcensoredwords" in bannedwords.lower()):
        await client.send_message(message.channel, 'You cannot define these commands as censored words.')
        return
    if exchannel:
        exchannel_id = await get_channel_info(exchannel)
        if not exchannel_id:
            msg = "Error: Channel doesn't exist, or the bot doesn't have permission for that channel."
            if '_' in exchannel:
                msg += '\nTry converting underscores to spaces, for example: game_of_thrones -> game of thrones.'
            await client.send_message(message.channel, msg)
            return
    if not exchannel:
        exchannel_id = None
    if not bannedwords:
        await client.send_message(message.channel, "You must specify words to ban.")
        return

    if (pos_in_string(input, "infomessage=") < pos_in_string(input, "exchannel=")) and (
                    "infomessage=" in input and "exchannel=" in input):
        await client.send_message(message.channel, "You must use the following format: \n"
                                                   "!addcensoredword **words**=<word1>, <word2>, ..., <wordN> "
                                                   "**exchannel**=<channel to be excluded> **infomessage**=<message>\n"
                                                   "You can define just **exchannel** or **infomessage**, or both.")
        return
    await sleep(1)
    await add_censored_word_into_database(bannedwords, message.id, exchannel_id, infomessage)
    await client.send_message(message.channel, 'Succesfully defined a new censored word entry.')
    return

async def get_channel_info(user_channel_name):
    channels = client.get_all_channels()
    for channel in channels:
        if channel.name.lower() == user_channel_name.lower():
            return channel.id
    return False #If channel doesn't exist

async def edit_channel_bitrate(bitrate):
    voice_channels = [c for c in client.get_all_channels() if c.type == discord.ChannelType.voice]
    succesfully_edited_channels = []
    unsuccesfully_edited_channels = []
    skipped_channels = []
    for channel in voice_channels:
        try:
            await sleep(0.2)
            if channel.bitrate != bitrate:
                await client.edit_channel(channel, bitrate=bitrate)
                succesfully_edited_channels.append(channel)
            else:
                skipped_channels.append(channel)
        except discord.Forbidden:
            unsuccesfully_edited_channels.append(channel)
    return len(succesfully_edited_channels), len(unsuccesfully_edited_channels), len(skipped_channels)

async def cmd_edit_channel_kbps(client, message, input):
    perms = message.channel.permissions_for(message.author)
    if not perms.administrator:
        await client.send_message(message.channel, "You do not have sufficient permissions.")
        return
    if not input or not input.isdigit() or not (8000 <= int(input) <= 96000):
        await client.send_message(message.channel, 'You need to specify channel bitrate between 8000-96000.')
        return
    num_of_succesfully_edited_channels, num_of_unsuccesfully_edited_channels, num_of_skipped_channels = await edit_channel_bitrate(int(input))
    msg = ("Changed bitrate of %s channels, skipped %s channel(s)." % (num_of_succesfully_edited_channels, num_of_skipped_channels)) if (num_of_unsuccesfully_edited_channels == 0) \
        else ("Changed bitrate of %s channel(s), skipped %s, failed %s\n(The bot is probably lacking manage permissions for some channel(s)."
              % (num_of_succesfully_edited_channels, num_of_skipped_channels, num_of_unsuccesfully_edited_channels))
    await client.send_message(message.channel, msg)





def parse_censored_word_message(unparsed_arg):
    channelindex = unparsed_arg.find('exchannel=')
    words_end = channelindex if channelindex != -1 else len(unparsed_arg)
    messageindex = unparsed_arg.find('infomessage=')
    words = unparsed_arg[6:words_end].rstrip()
    if not words:
        return None, None, None
    channel_end = messageindex if messageindex != -1 else len(unparsed_arg)
    channel = unparsed_arg[(words_end + len('exchannel=')):channel_end].rstrip() if channelindex != -1 else ''
    infomessage = unparsed_arg[messageindex + len('infomessage='):].rstrip() if messageindex != -1 else ''
    return words, channel, infomessage

async def add_censored_word_into_database(censored_words, message_id, exchannel_id=None, infomessage=None):
    await db.execute("""
        INSERT INTO censored_words AS a
        (message_id, censored_words, exchannel_id, info_message)
        VALUES ($1, $2, $3, $4)""", message_id, censored_words, exchannel_id, infomessage)
    log.info('Defined a new censored word: censored words: %s, exchannel: %s, infomessage %s, message_id %s', censored_words, exchannel_id, infomessage, message_id)

async def get_censored_words():
    return await db.fetch("""
        SELECT 
            *
        FROM
            censored_words
        """)

async def cmd_pickone(client, message, args):
    usage = (
        "Usage: `!pickone <opt1>, <opt2>, ..., <optN>`\n"
        "Chooses one of the given comma separated options\n"
    )

    def valid(args):
        return len(args.split(",")) >= 2

    if not valid(args):
        await client.send_message(message.channel, usage)
        return

    choices = args.split(",")
    if len(choices) == 2:
        if random.randrange(0, 30) == 1:
            await client.send_message(message.channel, 'Why not have both? :thinking:')
            return
    jibbajabba = random.choice(BOT_ANSWERS)
    choice = random.choice(choices)
    await client.send_message(message.channel, '%s %s' % (jibbajabba, choice.strip()))

async def cmd_list_censored_words(client, message, _):
    perms = message.channel.permissions_for(message.author)
    if not perms.administrator:
        await client.send_message(message.channel, "You do not have sufficient permissions.")
        return
    censored_word_entries = await get_censored_words()
    if not censored_word_entries:
        await client.send_message(message.channel, "No censored words have been defined.")
        return
    else:
        msg = ''
        i = 1
        for row in censored_word_entries:
            censored_words = ' **Censored words:** ' + row['censored_words']
            info_message = (' **Info message:** ' + row['info_message']) if row['info_message'] else ''
            exchannel = (' **Excluded channel:** ' + row['exchannel_id']) if row['exchannel_id'] else ''
            ID = str(i) + ':'
            if len((msg + ID + censored_words + info_message + exchannel + '\n')) >= 2000:
                await client.send_message(message.channel, msg)
                msg = ''
            msg += ID + censored_words + info_message + exchannel + '\n'
            i += 1
        await client.send_message(message.channel, msg)

async def cmd_del_censored_words(client, message, arg):
    perms = message.channel.permissions_for(message.author)
    if not perms.administrator:
        await client.send_message(message.channel, "You do not have sufficient permissions.")
        return
    if not arg or not arg.isdigit():
        await client.send_message(message.channel, "You must specify an ID to delete, eq. !deletecensoredwords 1. "
                                                   "Use !listcensoredwords to find out the correct ID.")
        return
    censored_word_entries = await get_censored_words()
    if not censored_word_entries:
        await client.send_message(message.channel, "No censored words have been defined.")
        return
    else:
        index = int(arg) - 1
        if index > len(censored_word_entries) - 1 or int(
                arg) == 0:  # While defining 0 as an ID works, we don't want that heh
            await client.send_message(message.channel, "No such ID in list.")
            return
        await delete_censored_words_from_database(censored_word_entries[index]['message_id'])
        await client.send_message(message.channel, "Censored word succesfully deleted.")
        return

async def delete_censored_words_from_database(message_id):
    await db.execute("DELETE from censored_words where message_id like $1", message_id)

async def cmd_sql(client, message, query):
    usage = (
        "Usage: `!sql <query>`\n"
    )

    def valid(query):
        return len(query) > 0

    perms = message.channel.permissions_for(message.author)
    if not perms.administrator:
        await client.send_message(message.channel, 'https://youtu.be/gvdf5n-zI14')
        return

    query = query.strip()
    if not valid(query):
        await client.send_message(message.channel, usage)
        return

    def limit_msg_length(template, content):
        max_len = 2000 - len(template % "")
        return template % content.replace("`", "")[:max_len]

    try:
        async with db.transaction(readonly=True) as tx:
            cur = await tx.cursor(query)
            results = await cur.fetch(100)
            msg = "\n".join(map(str, results))
            msg = limit_msg_length("```%s```", msg)
            await client.send_message(message.channel, msg)
    except Exception as err:
        msg = limit_msg_length("```ERROR: %s```", str(err))
        await client.send_message(message.channel, msg)
        return

async def cmd_randomcolor(client, message, _):
    # Credits to colorcombos.com
    char = '0123456789ABCDEF'
    randchars = ''.join(random.choice(char) for _ in range(6))
    link = 'http://www.colorcombos.com/images/colors/%s.png' % randchars
    await client.send_message(message.channel, link)

async def do_censored_words_check(client, message):
    message_words = message.content.split(' ')
    illegal_messages = await get_censored_words()
    if not illegal_messages:
        return True
    for row in illegal_messages:
        for word in message_words:
            if word and [badword for badword in row['censored_words'].split(',') if badword.strip().lower() == word.strip().lower()]:
                info_message = row['info_message'] + "\nIllegal word: " + word if row[
                    'info_message'] else "Your message containts forbidden word(s), and it was removed." + "\nIllegal word: " + word
                if not row['exchannel_id']:
                    await sleep(1)  # To prevent ratelimit from being reached
                    await client.delete_message(message)
                    await client.send_message(message.author, info_message)
                    return False
                if row['exchannel_id'] and await wrong_channel_for_this_word(message.channel.id, row['exchannel_id']):
                    await sleep(1)  # To prevent ratelimit from being reached
                    await client.delete_message(message)
                    await client.send_message(message.author, info_message)
                    return False
    return True

async def wrong_channel_for_this_word(current_message_channel_id, database_channel_id):
    return current_message_channel_id != database_channel_id

commands = {
    'sql': cmd_sql,
    'enchant': cmd_enchant,
    'roll': cmd_roll,
    '8ball': cmd_8ball,
    'weather': cmd_weather,
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
    'randomcolor': cmd_randomcolor,
    'addcensoredwords': cmd_add_censored_word,
    'listcensoredwords': cmd_list_censored_words,
    'deletecensoredwords': cmd_del_censored_words,
    'editkbpsofchannels': cmd_edit_channel_kbps,
    'countchars': cmd_countchars
}

def parse_raw_msg(msg):
    if isinstance(msg, bytes):
        msg = zlib.decompress(msg, 15, 10490000)
        msg = msg.decode('utf-8')
    return json.loads(msg)

@client.event
async def on_socket_raw_receive(raw_msg):
    msg = parse_raw_msg(raw_msg)

    type = msg.get("t", None)
    data = msg.get("d", None)

    if (type == "MESSAGE_CREATE"):
        log.info("Insta-archiving a new message")
        guild_id = await db.fetchval("SELECT guild_id FROM channel_archiver_status WHERE channel_id = $1", data["channel_id"])
        await archiver.insert_message(db, guild_id, data)

    elif (type == "GUILD_CREATE"):
        log.info("Updating users from GUILD_CREATE event")
        members = data.get("members", [])
        users = [m.get("user") for m in members]
        await upsert_users(users)

    elif (type == "GUILD_MEMBER_UPDATE"):
        log.info("Updating user from GUILD_MEMBER_UPDATE event")
        user = data.get("user")
        await upsert_users([user])

    elif (type == "PRESENCE_UPDATE"):
        log.info("Updating user from PRESENCE_UPDATE event")
        user = data.get("user")
        await upsert_users([user])

def is_full_user(user):
    # XXX: Do we want to require discriminator and avatar also?
    attrs = ["id", "username"]
    return all(attr in user for attr in attrs)

async def upsert_users(users):
    if not all(is_full_user(user) for user in users):
        log.info("Not all users were full")
        return

    async with db.transaction() as tx:
        for user in users:
            log.info("Updating user {0}".format(user))
            await tx.execute("""
                INSERT INTO discord_user
                (user_id, name, raw)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    raw = EXCLUDED.raw
            """, user.get("id"), user.get("username"), json.dumps(user))

# Dispacther for messages from the users.
@client.event
async def on_message(message):
    content = message.content
    try:
        if message.author.bot:
            return


        censor_check_passed = await do_censored_words_check(client, message)

        cmd, arg = command.parse(content)
        if not cmd or not censor_check_passed:
            return

        handler = commands.get(cmd)
        if not handler:
            handler = commands.get(autocorrect_command(cmd))

        if handler:
            await handler(client, message, arg)
            return

    except Exception:
        await util.log_exception(log)

def autocorrect_command(cmd):
    matches = difflib.get_close_matches(cmd, commands.keys(), n=1, cutoff=0.7)
    if len(matches) > 0:
        return matches[0]

@client.event
async def on_ready():
    await client.change_presence(game=discord.Game(name='is not working | I am your worker. I am your slave.'))
    await status.main(client)

if __name__ == "__main__":
    logger.init()

    # Database schema has to be initialized before running the bot
    loop = asyncio.get_event_loop()
    loop.run_until_complete(db.initialize_schema())
    loop.run_until_complete(awards.main())
    loop.run_until_complete(crypto.main())

    for module in [casino, sqlcommands, osu, feed, reminder, youtube, lan, steam, anssicommands, awards, laiva, faceit_commands, muutto, statistics, crypto, status, emojicommands]:
        commands.update(module.register(client))

    client.run(token)
