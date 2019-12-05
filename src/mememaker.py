import aiohttp
import logger
import json

log = logger.get("MEMEMAKER")
MEMEAPI_URL = "http://memeapi.santamaa.com/memefromurl"
ALLOWED_EXTENSIONS_LIST = ['png', 'jpg', 'svg']

class InvalidUrlError(Exception):
    pass

class InvalidExtensionError(Exception):
    pass

async def cmd_mememaker(client, message, args):
    if not args:
        await message.channel.send("Usage: !mememaker <image url>.{0}".format('|'.join(ALLOWED_EXTENSIONS_LIST)))
        return
    args = args.lstrip('```').rstrip('```').lstrip('`').rstrip('`')
    url, image_extension = args, args[-3:]
    if not is_valid_extension(image_extension):
        await message.channel.send("Url must end with .{0}".format('|'.join(ALLOWED_EXTENSIONS_LIST)))
        return
    try:
        meme_url = await meme_from_url(args)
    except InvalidUrlError as e:
        await message.channel.send("Error: url provided is invalid")
        return
    except Exception as e:
        await message.channel.send("There was an error processing your command.")
        log.error(e)
        return
    await message.channel.send(meme_url)

def is_valid_extension(extension):
    return extension in ALLOWED_EXTENSIONS_LIST

async def meme_from_url(url):
    async with aiohttp.ClientSession() as session:
        url = "http://memeapi.santamaa.com/memefromurl?url={0}".format(url)
        response = await session.get(url)
        log.info("%s %s %s %s", response.method, response.url, response.status, await
        response.text())
        if response.status not in [200, 404]:
            raise Exception("Error fetching data from mememaker API: HTTP status {0}".format(response.status))
        result = await response.json()
        error, status, return_url = result.get('error', None), result.get('status', None), result.get('url', None)
        if return_url:
            return return_url
        if error:
            if status in [404, 403]:
                raise InvalidUrlError("Invalid URL. Mememaker api HTTP status {0}, error: {1}".format(response.status, error))
        else:
            raise Exception("Error fetching data from mememaker API: HTTP status {0}".format(response.status))


def register(client):
    return {
        "mememaker": cmd_mememaker,
        "makememe": cmd_mememaker,
    }