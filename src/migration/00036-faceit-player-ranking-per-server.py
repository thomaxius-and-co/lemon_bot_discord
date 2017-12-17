async def exec(log, tx):
    # Rename faceit_guild_players_list to more descriptive faceit_player
    await tx.execute("ALTER TABLE faceit_guild_players_list RENAME TO faceit_player")

    # Remove unused columns from faceit_player table
    await tx.execute("ALTER TABLE faceit_player DROP COLUMN message_id")
    await tx.execute("ALTER TABLE faceit_player DROP COLUMN spam_channel_id")
    await tx.execute("ALTER TABLE faceit_player DROP COLUMN custom_nickname")
    await tx.execute("ALTER TABLE faceit_player DROP COLUMN deleted")

    # faceit_guild_ranking is a mapping between faceit player and a server
    await tx.execute("""
        CREATE TABLE faceit_guild_ranking (
            guild_id TEXT NOT NULL,
            faceit_guid TEXT NOT NULL REFERENCES faceit_player (faceit_guid),
            custom_nickname TEXT,
            PRIMARY KEY (guild_id, faceit_guid)
        )
    """)

    # Discord channel to spam elo changes to. Only one per Discord guild.
    await tx.execute("""
        CREATE TABLE faceit_notification_channel (
            guild_id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL
        )
    """)
