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

async def cmd_mememaker(client, original_message, args):
    if not args:
        await original_message.channel.send("Usage: !mememaker <image url>.{0}".format('|'.join(ALLOWED_EXTENSIONS_LIST)))
        return
    args = args.lstrip('```').rstrip('```').lstrip('`').rstrip('`')
    url, image_extension = args, args[-3:]
    if not is_valid_extension(image_extension):
        await original_message.channel.send("Url must end with .{0}".format('|'.join(ALLOWED_EXTENSIONS_LIST)))
        return
    new_message = await original_message.channel.send('Please wait, manufacturing meme..')
    await original_message.delete()
    try:
        meme_url = await meme_from_url(args)
    except InvalidUrlError as e:
        await new_message.edit(content="Error: url provided is invalid")
        return
    except Exception as e:
        await new_message.edit(content="There was an error processing your command.")
        log.error(e)
        return
    await new_message.edit(content=meme_url)

def is_valid_extension(extension):
    return extension.lower() in ALLOWED_EXTENSIONS_LIST

async def meme_from_url(url):
    async with aiohttp.ClientSession() as session:
        url = "http://memeapi.santamaa.com/memefromurl?url={0}".format(url)
        response = await session.get(url)
        log.debug("%s %s %s %s", response.method, response.url, response.status, await
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