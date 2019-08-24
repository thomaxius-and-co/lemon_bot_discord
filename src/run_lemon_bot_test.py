from test_util import env

import run_lemon_bot

def test_admin_ids_are_strings():
    with env("ADMIN_USER_IDS", "141649488069656576"):
        admins = run_lemon_bot.get_admins()
        assert isinstance(admins[0], int)
        assert admins[0] == 141649488069656576
