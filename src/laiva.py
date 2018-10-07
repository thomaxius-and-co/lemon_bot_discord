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
    if (laiva - timedelta(days=149)) < now:
        template += "\n**Laiva pokemon of the day:** %s" % pokemon[delta.days]

    msg = template.format(*delta_to_tuple(delta))
    await client.send_message(message.channel, msg)

