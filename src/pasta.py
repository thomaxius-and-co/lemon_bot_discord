def register(client):
  util.start_task_thread(task(client))
  return {
    "pasta": cmd_pasta,
  }

pastas = {
  "suihkun": "Nyt täytyy kyllä myöntää etten jaksanut lukea ollenkaan ja veikkaan ongelmasi olevan jotain täyttä hevonvitunpaskaa.\n\nMene suihkuun ja nukkumaan. Huomenna töihin. Muuta neuvoa ei tule.",
}

async def cmd_pasta(client, message, pasta_name):
  if pasta_name in pastas:
    await message.channel.send(pastas.get(pasta_name))
