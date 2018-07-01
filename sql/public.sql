CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Discord
CREATE TABLE discord_user (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    raw JSONB NOT NULL
);

CREATE TABLE message (
    message_id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    guild_id TEXT,
    user_id TEXT NOT NULL,
    m JSONB NOT NULL,
    ts TIMESTAMP NOT NULL,
    bot BOOL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES discord_user (user_id)
);

CREATE INDEX message_content_trgm_idx ON message USING GIN (content gin_trgm_ops);
CREATE INDEX message_ts_date_idx ON message ((ts::date));
CREATE INDEX message_bot_idx ON message (bot);

CREATE TABLE resetdate (nextresetdate TIMESTAMP NOT NULL);

CREATE TABLE censored_words (
    message_id TEXT NOT NULL,
    censored_words TEXT NOT NULL,
    exchannel_id TEXT,
    info_message TEXT,
    FOREIGN KEY (message_id) REFERENCES message (message_id)
);

-- Statistics
CREATE TABLE statistics (
    statistics_id TEXT PRIMARY KEY,
    content JSONB NOT NULL,
    changed TIMESTAMP NOT NULL DEFAULT current_timestamp
);

-- Archiver
CREATE TABLE channel_archiver_status (
    guild_id TEXT,
    channel_id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL
);

-- SQL madness
CREATE TABLE custom_trophies (
    message_id TEXT NOT NULL,
    trophy_name TEXT NOT NULL,
    trophy_conditions TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES message (message_id)
);

CREATE TABLE excluded_users (
    excluded_user_id TEXT NOT NULL,
    added_by_id TEXT NOT NULL,
    FOREIGN KEY (excluded_user_id) REFERENCES discord_user (user_id),
    FOREIGN KEY (added_by_id) REFERENCES discord_user (user_id)
);

-- Casino
CREATE TABLE casino_account (
    user_id TEXT PRIMARY KEY,
    balance NUMERIC NOT NULL,
    FOREIGN KEY (user_id) REFERENCES discord_user (user_id)
);

CREATE TABLE casino_bet (
    user_id TEXT PRIMARY KEY,
    bet NUMERIC NOT NULL,
    FOREIGN KEY (user_id) REFERENCES discord_user (user_id)
);

CREATE TABLE casino_stats (
    user_id TEXT PRIMARY KEY,
    wins_bj NUMERIC NOT NULL DEFAULT 0,
    wins_slots NUMERIC NOT NULL DEFAULT 0,
    losses_slots NUMERIC NOT NULL DEFAULT 0,
    losses_bj NUMERIC NOT NULL DEFAULT 0,
    ties NUMERIC NOT NULL DEFAULT 0,
    surrenders NUMERIC NOT NULL DEFAULT 0,
    moneyspent_bj NUMERIC NOT NULL DEFAULT 0,
    moneyspent_slots NUMERIC NOT NULL DEFAULT 0,
    moneywon_bj NUMERIC NOT NULL DEFAULT 0,
    moneywon_slots NUMERIC NOT NULL DEFAULT 0,
    biggestwin_slots NUMERIC NOT NULL DEFAULT 0,
    bj_blackjack NUMERIC NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES discord_user (user_id)
);

CREATE TABLE whosaidit_stats (
    user_id TEXT PRIMARY KEY,
    correct NUMERIC NOT NULL DEFAULT 0,
    wrong NUMERIC NOT NULL DEFAULT 0,
    moneyspent NUMERIC NOT NULL DEFAULT 0,
    streak NUMERIC NOT NULL DEFAULT 0,
    record NUMERIC NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES discord_user (user_id)
);

CREATE TABLE whosaidit_stats_history (
    user_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    quote TEXT NOT NULL,
    correctname TEXT NOT NULL,
    playeranswer TEXT NOT NULL,
    correct NUMERIC NOT NULL DEFAULT 0,
    streak NUMERIC NOT NULL DEFAULT 0,
    losestreak NUMERIC NOT NULL DEFAULT 0,
    time TIMESTAMP NOT NULL,
    week NUMERIC NOT NULL,
    -- TODO PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES discord_user (user_id),
    FOREIGN KEY (message_id) REFERENCES message (message_id)
);

CREATE TABLE whosaidit_weekly_winners (
    user_id TEXT NOT NULL,
    wins NUMERIC NOT NULL DEFAULT 0,
    losses NUMERIC NOT NULL DEFAULT 0,
    time TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES discord_user (user_id)
);

CREATE TABLE casino_jackpot (jackpot NUMERIC NOT NULL DEFAULT 0);

INSERT INTO casino_jackpot (jackpot) VALUES (0);

CREATE TABLE casino_jackpot_history (
    user_id TEXT PRIMARY KEY,
    jackpot NUMERIC NOT NULL DEFAULT 0,
    date NUMERIC NOT NULL DEFAULT 0
    -- TODO: FOREIGN KEY (user_id) REFERENCES discord_user (user_id)
);

-- Feed
CREATE TABLE feed (
    feed_id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    last_entry TIMESTAMP DEFAULT current_timestamp,
    channel_id TEXT NOT NULL,
    UNIQUE (url)
);

-- Reminder
CREATE TABLE reminder (
    reminder_id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    ts TIMESTAMP NOT NULL,
    text TEXT NOT NULL,
    original_text TEXT NOT NULL,
    reminded BOOL NOT NULL DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES discord_user (user_id)
);

-- osu!
CREATE TABLE osu_pp (
    osu_pp_id SERIAL PRIMARY KEY,
    osu_user_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    standard_pp NUMERIC NOT NULL,
    standard_rank INT NOT NULL,
    mania_pp NUMERIC NOT NULL,
    mania_rank INT NOT NULL,
    changed TIMESTAMP NOT NULL,
    UNIQUE (osu_user_id, channel_id) -- TODO: guild_id instead
);

-- FACEIT
CREATE TABLE faceit_player (
    id SERIAL PRIMARY KEY,
    faceit_guid TEXT NOT NULL,
    faceit_nickname TEXT NOT NULL,
    UNIQUE (faceit_guid)
);

CREATE TABLE faceit_guild_ranking (
    guild_id TEXT NOT NULL,
    faceit_guid TEXT NOT NULL REFERENCES faceit_player (faceit_guid),
    custom_nickname TEXT,
    PRIMARY KEY (guild_id, faceit_guid)
);

CREATE TABLE faceit_live_stats (
    faceit_guid TEXT NOT NULL REFERENCES faceit_player (faceit_guid),
    faceit_elo BIGINT NOT NULL,
    faceit_skill BIGINT NOT NULL,
    faceit_ranking BIGINT,
    changed TIMESTAMP NOT NULL
);

CREATE TABLE faceit_notification_channel (
    guild_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL
);

CREATE TABlE faceit_aliases (
	faceit_guid TEXT NOT NULL REFERENCES faceit_player (faceit_guid),
	faceit_nickname TEXT NOT NULL, 
	added timestamp without time zone DEFAULT current_timestamp NOT NULL
);

-- Nokia Health
CREATE TABLE nokia_health_link (
    user_id TEXT PRIMARY KEY REFERENCES discord_user (user_id),
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    original JSONB NOT NULL,
    changed TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    created TIMESTAMP WITHOUT TIME ZONE DEFAULT current_timestamp NOT NULL
);
