from operator import itemgetter

import migration

def test_sequential_version_numbers():
    migrations = migration.find_migrations()
    versions = list(map(itemgetter(0), migrations))

    # Versions start at 1
    assert min(versions) == 1

    # Versions are sequential
    expected = list(range(min(versions), max(versions) + 1))
    assert versions == expected
