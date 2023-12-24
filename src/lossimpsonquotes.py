import lossimpsonapi

async def cmd_simpsons_quote(client, message, _):
    quote, author, picture = await lossimpsonapi.get_quote()
    await message.channel.send("\n*" + quote + "*" + "\n- " + author + '\n' + picture)


def register():
    return {
        'simpsonsquote' :cmd_simpsons_quote,
        'sq' : cmd_simpsons_quote
    }