def register(client):
    return {
        "valokuitu": cmd_valokuitu,
    }

async def cmd_valokuitu(client, message, _):
    await client.send_message(message.channel, "Valokuitu has already arrived, but tarve paremmasta remains")

