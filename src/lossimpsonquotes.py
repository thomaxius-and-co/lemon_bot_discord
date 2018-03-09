import lossimpsonapi

async def cmd_simpsons_quote(client, message, _):
    quote, author, picture = await lossimpsonapi.get_quote()
    await client.send_message(message.channel, "\n*" + quote + "*" + "\n- " + author + '\n' + picture)


def register(client):
    return {
        'simpsonsquote' :cmd_simpsons_quote,
        'sq' : cmd_simpsons_quote
    }