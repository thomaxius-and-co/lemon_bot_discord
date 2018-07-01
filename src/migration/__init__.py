from operator import itemgetter
import importlib
import os
import pkgutil

import logger

log = logger.get("MIGRATION")

async def run_migrations(tx):
    all_migrations = find_migrations()
    version = await get_current_schema_version(tx)
    if not version:
        await init_migration_table(tx, migrations)
        return

    log.info("Current schema version is {0}".format(version))

    migrations, new_version = find_new_migrations(all_migrations, version)

    if len(migrations) > 0:
        for version, module in migrations:
            name = module.__name__[len("migration."):]
            log.info("Running migration {0}".format(name))
            await module.exec(log, tx)

        await insert_version(tx, new_version)

    log.info("Schema is in up to date")

async def init_migration_table(tx, migrations):
    max_version = max(map(itemgetter(0), migrations))
    log.info("Migration table not initialized. Initializing at version {0}".format(max_version))
    await tx.execute("""
        CREATE TABLE schema_version (
            version NUMERIC NOT NULL,
            upgraded TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
    """)
    await insert_version(tx, max_version)

async def insert_version(tx, new_version):
    await tx.execute("INSERT INTO schema_version (version) VALUES ($1)", new_version)

def find_new_migrations(migrations, version):
    new_migrations = list(filter(is_newer_than(version), migrations))
    log.info("Found {0} migrations of which {1} are new".format(len(migrations), len(new_migrations)))
    return new_migrations, max(map(itemgetter(0), new_migrations), default=version)

def find_migrations():
    path = os.path.dirname(__file__)
    return sorted(map(load_module, pkgutil.iter_modules([path])), key=itemgetter(0))

def load_module(module_info):
    module_name = module_info[1]
    version = int(module_name.split("-")[0])
    imported_module = importlib.import_module("migration." + module_name)
    return version, imported_module

def is_newer_than(current_version):
    return lambda x: x[0] > current_version

async def get_current_schema_version(tx):
    if await table_exists(tx, "schema_version"):
        result = await tx.fetchrow("SELECT max(version)::bigint FROM schema_version")
        return result[0] if result is not None else 0
    else:
        return 0

async def table_exists(tx, table_name):
    rows = await tx.fetch("SELECT * FROM information_schema.tables WHERE table_name = $1", table_name)
    return bool(len(rows))
