async def exec(log, tx):
    # Add foreign key constraints to make sure data references are valid
    await tx.execute("""
        ALTER TABLE casino_account
        ADD FOREIGN KEY (user_id) REFERENCES discord_user (user_id);

        ALTER TABLE casino_bet
        ADD FOREIGN KEY (user_id) REFERENCES discord_user (user_id);

        ALTER TABLE reminder
        ADD FOREIGN KEY (user_id) REFERENCES discord_user (user_id);

        ALTER TABLE casino_stats
        ADD FOREIGN KEY (user_id) REFERENCES discord_user (user_id);

        ALTER TABLE whosaidit_stats
        ADD FOREIGN KEY (user_id) REFERENCES discord_user (user_id);

        ALTER TABLE channel_archiver_status
        ADD FOREIGN KEY (message_id) REFERENCES message (message_id);
    """)

