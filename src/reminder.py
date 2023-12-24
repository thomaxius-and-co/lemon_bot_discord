import asyncio

import parsedatetime
from datetime import datetime
from time_util import to_utc, to_helsinki, as_utc, as_helsinki
import discord

import emoji
import database as db
import util
import logger

log = logger.get("REMINDER")

def register():
    log.info("Registering")
    return {
        "remind": cmd_reminder,
        "remindme": cmd_reminder,
        "todo": cmd_reminder,
    }

async def cmd_reminder(client, message, text):
    reminder = parse_reminder(text)
    if reminder is None:
        reply = "Sorry {message.author.mention}, I couldn't figure out the time for your reminder.".format(message=message)
        await message.channel.send(reply)
        await message.add_reaction(emoji.CROSS_MARK)
        return

    await add_reminder(message.author.id, reminder.time, reminder.text, reminder.original_text)

    reply = "Hello, {0}! I'll remind you about `{1}` at `{2}`!".format(
        message.author.mention, reminder.text, to_helsinki(reminder.time))
    await message.channel.send(reply)

async def add_reminder(user_id, time, text, original_text):
    await db.execute("""
        INSERT INTO reminder(user_id, ts, text, original_text)
        VALUES ($1, $2, $3, $4)
    """, str(user_id), time.replace(tzinfo=None), text, original_text)


IGNORED_DISCORD_ERROR_CODES = [
    50007, # Cannot send messages to this user
]

async def process_next_reminder(client):
    async with db.transaction() as tx:
        reminders = await tx.fetch("""
            SELECT reminder_id, user_id, text
            FROM reminder
            WHERE ts < current_timestamp AND reminded = false
            ORDER BY ts ASC
        """)
        if len(reminders) == 0:
            return

        log.info("Sending {0} reminders".format(len(reminders)))

        for id, user_id, text in reminders:
            msg = "Hello! I'm here to remind you about `{0}`".format(text)
            user = await client.fetch_user(int(user_id))
            try:
                await user.send(msg)
            except discord.errors.HTTPException as e:
                if e.code in IGNORED_DISCORD_ERROR_CODES:
                    log.info("Ignoring Discord error response %s", e)
                else:
                    raise e

            await tx.execute("""
                UPDATE reminder
                SET reminded = true
                WHERE reminder_id = $1
            """, id)

def parse_reminder(text):
    cal = parsedatetime.Calendar()

    source_time = to_helsinki(as_utc(datetime.now()))
    time_expressions = cal.nlp(text, source_time)
    time_expressions = time_expressions if time_expressions else []

    reminders = map(lambda p: Reminder(text, p), time_expressions)
    reminders_in_priority_order = sorted(reminders, key=lambda r: r.priorty)
    return next(iter(reminders_in_priority_order), None)

class Reminder:
    def __init__(self, original_text, time_expression):
        time, flags, start, end, time_text = time_expression

        self.original_text = original_text
        self.time_text = time_text
        self.time = to_utc(as_helsinki(time))

        self.text = self.strip_middle(original_text, start, end)

        prefix = start == 0
        postfix = end == len(original_text)
        self.priorty = 1 if postfix else (2 if prefix else 3)

    def strip_middle(self, text, start, end):
        return text[:start].strip() + " " + text[end:].strip()
