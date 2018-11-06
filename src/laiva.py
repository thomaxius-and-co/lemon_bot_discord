from datetime import datetime, timedelta
from math import floor

from time_util import as_helsinki, as_utc, to_utc

pokemon = ["Bulbasaur","Ivysaur","Venusaur","Charmander","Charmeleon","Charizard","Squirtle","Wartortle","Blastoise",
           "Caterpie","Metapod","Butterfree","Weedle","Kakuna","Beedrill","Pidgey","Pidgeotto","Pidgeot","Rattata",
           "Raticate","Spearow","Fearow","Ekans","Arbok","Pikachu","Raichu","Sandshrew","Sandslash","Nidoran","Nidorina",
           "Nidoqueen","Nidoran","Nidorino","Nidoking","Clefairy","Clefable","Vulpix","Ninetales","Jigglypuff","Wigglytuff",
           "Zubat","Golbat","Oddish","Gloom","Vileplume","Paras","Parasect","Venonat","Venomoth","Diglett","Dugtrio",
           "Meowth","Persian","Psyduck","Golduck","Mankey","Primeape","Growlithe","Arcanine","Poliwag","Poliwhirl",
           "Poliwrath","Abra","Kadabra","Alakazam","Machop","Machoke","Machamp","Bellsprout","Weepinbell","Victreebel",
           "Tentacool","Tentacruel","Geodude","Graveler","Golem","Ponyta","Rapidash","Slowpoke","Slowbro","Magnemite",
           "Magneton","Farfetch'd","Doduo","Dodrio","Seel","Dewgong","Grimer","Muk","Shellder","Cloyster","Gastly",
           "Haunter","Gengar","Onix","Drowzee","Hypno","Krabby","Kingler","Voltorb","Electrode","Exeggcute","Exeggutor",
           "Cubone","Marowak","Hitmonlee","Hitmonchan","Lickitung","Koffing","Weezing","Rhyhorn","Rhydon","Chansey","Tangela",
           "Kangaskhan","Horsea","Seadra","Goldeen","Seaking","Staryu","Starmie","Mr. Mime","Scyther","Jynx","Electabuzz",
           "Magmar","Pinsir","Tauros","Magikarp","Gyarados","Lapras","Ditto","Eevee","Vaporeon","Jolteon","Flareon","Porygon",
           "Omanyte","Omastar","Kabuto","Kabutops","Aerodactyl","Snorlax","Articuno","Zapdos","Moltres","Dratini","Dragonair",
           "Dragonite","Mewtwo","Mew"]



memes = [
"11KCaw9IayKXbJ21uvH1qWA0Vc-CQNF45",
"1tOAAPZqfoYOXxSir3YfGMvh6py5LfvSg",
"19tFMKLVqyTy7uAYokfc0AxtTLUIPMjjx",
"1bp6TFdPY-coYbleNlx1C2zOyXuFtFzg7",
"1rbP_OmusEHxgwIi7WA1qgA8CKvHfnrE7",
"1Uc-hrexmPEf807G63AUCOMGAzPHebJ77",
"14-CWGtgUIKraTsMYQV9DEMyVFGho4wCZ",
"1BUCRPupZ7TXBFXzsEi7JQACpV-Znq6wr",
"1_rFwWLfkLJLeGXaPHp0Imf0b5K-YvZp7",
"1vs1L1pmfV-nrBCyxcdwybwFwawiOperp",
"1Qf2rE9Nf6BYO_i0vviS3ItdGzNYgTyGf",
"1rppIlxAFpKdAGfahcpLcAg6wIScR0IGx",
"1y4zOCM31JHk79dxc370y2eVEOlblSYAC",
"1Wf_3-lzjbYGfiNdyPV8RpE2t23ZaiG2v",
"1k9q5CQ_FDD4nBdASGby65HponRVeUi4F",
"1rkQDXDhRDeq9k1DbtFrJPjrfpxtKYivy",
"1_rot7lgNeO6T9N-GgRM79e2oZS8xTgap",
"1clKLX3lNJgbwqjHDHO1HyOb1W_PwYrBz",
"1F0euMeicBz5cEzVXnznf66jb6z2mPiTj",
"1wxQBLGZbvxQUoeGzWy4EbHUMJl1DNKcQ",
"1N4eZ3E0I5GpPCUuUy7j82qWJBTyM5U-A",
"1V5VkexmeOaB9YOiN2ZqDlVOr_R-284Q0",
"14d_nBA50HbwEERee5yc0iH0FvZwY9a3E"]

def register(client):
    return {
        "laiva": cmd_laiva,
        "laivalle": cmd_laiva,
    }

def delta_to_tuple(delta):
    days = delta.days
    s = delta.seconds
    seconds = s % 60
    m = floor((s - seconds) / 60)
    minutes = m % 60
    h = floor((m - minutes) / 60)
    hours = h
    return (days, hours, minutes, seconds)

async def get_laiva_meme_of_the_day(day):
    return "https://drive.google.com/file/d/" + memes[day] + "/view?usp=sharing"

async def cmd_laiva(client, message, _):
    laiva = to_utc(as_helsinki(datetime(2018, 11, 9, 17, 0)))
    laivaover = to_utc(as_helsinki(datetime(2018, 11, 11, 10, 30)))
    now = as_utc(datetime.now())
    now_to_last_laivaover = now - laivaover


    if (laiva < now) and (laivaover > now):
        await client.send_message(message.channel, "Laiva is currently happening!!")
        return

    if ((laivaover + timedelta(days=1)) < now) and laiva < now:
        await client.send_message(message.channel, ("**Last laiva ended:** {0} days, {1} hours, {2} minutes, {3} seconds ago, **next laiva:** TBA.")
                                  .format(*delta_to_tuple(now_to_last_laivaover)))
        return

    if laivaover < now:
        await client.send_message(message.channel, "Laiva is already over, but paha olo remains.")
    delta = laiva - now

    template = "Time left until 'The laiva to end all laivas': {0} days, {1} hours, {2} minutes, {3} seconds!!"
    if (laiva - timedelta(days=len(pokemon)-1)) < now:
        template += "\n**Laiva pokemon of the day:** %s" % pokemon[delta.days]
    if (laiva - timedelta(days=len(memes)-1)) < now:
        template += "\n**Laiva meme of the day**:\n%s" % await get_laiva_meme_of_the_day(delta.days)

    msg = template.format(*delta_to_tuple(delta))
    await client.send_message(message.channel, msg)

