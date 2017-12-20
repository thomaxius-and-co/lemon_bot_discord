from util import grouped

async def exec(log, tx):
    id_map = await build_id_map(tx)
    for guild_id, message_ids in id_map.items():
        log.info("Found %d messages that should have guild_id %s", len(message_ids), guild_id)
        for batch in grouped(message_ids, 1000):
            await update_messages(log, tx, guild_id, batch)

    log.info("Messages with guild_id: %d", await tx.fetchval("SELECT count(*) FROM message WHERE guild_id IS NOT NULL"))
    log.info("Messages without guild_id: %d", await tx.fetchval("SELECT count(*) FROM message WHERE guild_id IS NULL"))

async def build_id_map(tx):
    ids = await tx.fetch("""
        SELECT message.message_id, channel_archiver_status.guild_id
        FROM message
        JOIN channel_archiver_status
        ON message.m->>'channel_id' = channel_archiver_status.channel_id
        WHERE message.guild_id IS NULL AND channel_archiver_status.guild_id IS NOT NULL
    """)

    id_map = {}
    for message_id, guild_id in ids:
        if not guild_id in id_map:
            id_map[guild_id] = []
        id_map[guild_id].append(message_id)
    return id_map

async def update_messages(log, tx, guild_id, message_ids):
    log.info("Setting guild_id %s on %d messages", guild_id, len(message_ids))
    await tx.execute("""
        UPDATE message
        SET guild_id = $1
        WHERE message_id = ANY($2)
    """, guild_id, message_ids)
