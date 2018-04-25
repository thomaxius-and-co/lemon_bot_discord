async def exec(log, tx):
    await tx.execute("""
        CREATE TABlE nokia_health_link (
            user_id text PRIMARY KEY REFERENCES discord_user(user_id),
            access_token text NOT NULL,
            refresh_token text NOT NULL,
            original jsonb NOT NULL,
            changed timestamp without time zone NOT NULL,
            created timestamp without time zone DEFAULT current_timestamp NOT NULL
        );
    """)
