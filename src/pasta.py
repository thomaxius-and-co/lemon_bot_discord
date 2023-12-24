def register():
  return {
    "pasta": cmd_pasta,
  }

pastas = {
  "suihkuun": "Nyt täytyy kyllä myöntää etten jaksanut lukea ollenkaan ja veikkaan ongelmasi olevan jotain täyttä hevonvitunpaskaa.\n\nMene suihkuun ja nukkumaan. Huomenna töihin. Muuta neuvoa ei tule.",
}

async def cmd_pasta(client, message, pasta_name):
  if pasta_name in pastas:
    await message.channel.send(pastas.get(pasta_name))
