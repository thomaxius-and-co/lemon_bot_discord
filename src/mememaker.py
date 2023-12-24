from contextlib import suppress
import aiohttp
import discord
import logger
import json

log = logger.get("MEMEMAKER")
MEMEAPI_URL = "http://memeapi.santamaa.com/memefromurl"
ALLOWED_EXTENSIONS_LIST = ['png', 'jpg', 'svg']
AVAILABLE_MEMES = ['niske', 'carl']


class InvalidUrlError(Exception):
    pass


class InvalidExtensionError(Exception):
    pass


def valid(args):
    return (len(args.split(" ")) == 2)


def image_properties_from_arg(args) -> [str, str]:
    args = args.lstrip('```').rstrip('```').lstrip('`').rstrip('`')
    url, image_extension = args, args[-3:]
    return url, image_extension


async def cmd_mememaker(client, original_message, args):
    if not valid(args):
        await original_message.channel.send(
            f"Usage: !mememaker <image url>.{'|'.join(ALLOWED_EXTENSIONS_LIST)} <meme name>\nValid meme names: {', '.join(AVAILABLE_MEMES)}")
        return
    template_url_arg, meme_name = args.split(' ')
    url, image_extension = image_properties_from_arg(template_url_arg)
    if not is_valid_extension(image_extension):
        await original_message.channel.send("Url must end with .{0}".format('|'.join(ALLOWED_EXTENSIONS_LIST)))
        return
    new_message = await original_message.channel.send('Please wait, manufacturing meme..')

    # It's OK if the bot doesn't have permissions to delete the command
    # message. In private chat there isn't even an option to give the bot such
    # permission.
    with suppress(discord.errors.Forbidden):
        await original_message.delete()
    try:
        meme_url = await meme_from_url(url, meme_name)
        await new_message.edit(content=meme_url)
    except InvalidUrlError as e:
        await new_message.edit(content="Error: Provided url is invalid")
    except Exception as e:
        log.error(e)
        await new_message.edit(content="There was an error processing your command.")


def is_valid_extension(extension):
    return extension.lower() in ALLOWED_EXTENSIONS_LIST


async def meme_from_url(url, meme):
    async with aiohttp.ClientSession() as session:
        url = f"http://memeapi.santamaa.com/memefromurl?url={url}&meme={meme}"
        response = await session.get(url)
        log.debug({
            "requestMethod": response.method,
            "requestUrl": str(response.url),
            "responseStatus": response.status,
            "responseBody": await response.text(),
        })
        if response.status not in [200, 404]:
            raise Exception("Error fetching data from mememaker API: HTTP status {0}".format(response.status))
        result = await response.json()
        error, status, return_url = result.get('error', None), result.get('status', None), result.get('url', None)
        if return_url:
            return return_url
        if error:
            if status in [404, 403]:
                raise InvalidUrlError(
                    "Invalid URL. Mememaker api HTTP status {0}, error: {1}".format(response.status, error))
        else:
            raise Exception("Error fetching data from mememaker API: HTTP status {0}".format(response.status))


def register():
    return {
        "mememaker": cmd_mememaker,
        "makememe": cmd_mememaker,
    }
