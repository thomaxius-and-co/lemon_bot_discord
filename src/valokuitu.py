def register(client):
    return {
        "valokuitu": cmd_valokuitu,
    }

async def cmd_valokuitu(client, message, query):
    await client.send_message(message.channel, "Valokuitu will be installed tomorrow")
