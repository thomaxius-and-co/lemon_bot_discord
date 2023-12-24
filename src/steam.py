import random

import command
import steam_api as api

def register():
    return {
        "steam": cmd_steam,
    }

async def cmd_steam(client, message, subcommand):
    cmd, arg = command.parse(subcommand, prefix="")

    subcommands = {
        "common": cmd_steam_common,
    }

    handler = subcommands.get(cmd, cmd_steam_common)
    await handler(client, message, arg)


async def cmd_steam_common(client, message, args):
    usage = (
        "Usage: `!steam common <username1>, <username2>, ..., <usernameN>`\n"
        "Figures out common games for given steam users to play\n"
    )


    def valid(args):
        return len(args.split(" ")) >= 2

    if not valid(args):
        await message.channel.send(usage)
        return

    usernames = args.split(" ")
    steamids = []
    for username in usernames:
        steamid = await api.steamid(username)
        if steamid is None:
            await message.channel.send("Username {username} is not valid".format(username=username))
            return
        steamids.append(steamid)

    owned_game_sets = []
    for steamid in steamids:
        owned_games = await api.owned_games(steamid)
        appids = set(game.appid for game in owned_games)
        owned_game_sets.append(appids)

    common_app_ids = set.intersection(*owned_game_sets)
    selected = random.sample(common_app_ids, min(10, len(common_app_ids)))

    if len(selected) > 0:
        game_names = []
        for appid in selected:
            details = await api.appdetails(appid)
            game_names.append(details["name"])


        msg = "Found the following common games:\n{0}".format("\n".join(game_names))
        await message.channel.send(msg)
    else:
        msg = "Unfortunately I didn't find any common games"
        await message.channel.send(msg)
