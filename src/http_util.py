import aiohttp

async def get(url, headers=None):
    async with aiohttp.ClientSession() as client:
        return await client.get(url, headers=headers)

async def post(url, data=None):
    async with aiohttp.ClientSession() as client:
        return await client.post(url, data=data)
