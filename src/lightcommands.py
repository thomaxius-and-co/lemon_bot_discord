from phue import Bridge, PhueRegistrationException
b = None

def register(client):
    return {
        'randombrightness': cmd_randombrightness,
        'connecttohue': cmd_connecttohue
    }

async def cmd_connecttohue(client, message, input):
    if not input:
        await client.send_message(message.channel, "Error: You need to specify hue IP to connect to.")
        return
    if not input.replace('.','').isdigit():
        print(input.strip('.'))
        await client.send_message(message.channel, "Error: IP must be numeric.")
        return
    try:
        b = Bridge(input)
        b.connect()
    except PhueRegistrationException:
        await client.send_message(message.channel, "Error: Connect button has not been pressed for the last 30 seconds.")
        return
    await client.send_message(message.channel, "Connection was probably succesful!")
    return

async def cmd_randombrightness(client, message, _):
    if b.get_light(1, 'on') == False:
        await client.send_message(message.channel, "Error: Light is off.")
        return
    b.set_light(1, 'bri', random.randrange(0,254))
    await client.send_message(message.channel, "Succesfully messed with Thom's light.")
    return
