async def exec(log, tx):
    # Change discriminator to user_id in casino_bets and casino_account
    await tx.execute("""
        -- Create user_id column in casino_bet and fill it with data
        ALTER TABLE casino_bet ADD COLUMN user_id TEXT;
        UPDATE casino_bet SET user_id = (
          SELECT m->'author'->>'id'
          FROM message
          WHERE concat(m->'author'->>'username', '#', m->'author'->>'discriminator') = discriminator
          LIMIT 1
        );
        ALTER TABLE casino_bet ALTER COLUMN user_id SET NOT NULL;

        -- Change casino_bet primary key from discriminator to user_id
        ALTER TABLE casino_bet DROP CONSTRAINT casino_bet_pkey;
        ALTER TABLE casino_bet ADD PRIMARY KEY (user_id);

        -- Drop discriminator column
        ALTER TABLE casino_bet DROP COLUMN discriminator;

        -- Create user_id column in casino_account and fill it with data
        ALTER TABLE casino_account ADD COLUMN user_id TEXT;
        UPDATE casino_account SET user_id = (
          SELECT m->'author'->>'id'
          FROM message
          WHERE concat(m->'author'->>'username', '#', m->'author'->>'discriminator') = discriminator
          LIMIT 1
        );
        ALTER TABLE casino_bet ALTER COLUMN user_id SET NOT NULL;

        -- Change casino_account primary key from discriminator to user_id
        ALTER TABLE casino_account DROP CONSTRAINT casino_account_pkey;
        ALTER TABLE casino_account ADD PRIMARY KEY (user_id);

        -- Drop discriminator column
        ALTER TABLE casino_account DROP COLUMN discriminator;
    """)
