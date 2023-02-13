intermittent-tracker
====================

To develop locally:

```sh
$ python3 -m venv .venv
$ . .venv/bin/activate
$ pip install -e . -r requirements.txt
$ cp config.json.example config.json
$ FLASK_DEBUG=1 python3 -m intermittent_tracker.flask_server
```

To run tests:

```sh
$ . .venv/bin/activate
$ python3 -m intermittent_tracker.tests
```

To generate a `dashboard_secret` for config.json:

```sh
$ python3 -c 'import secrets; print(secrets.token_urlsafe())'
```

To update the pinned dependencies in the lockfile:

```sh
$ pip freeze --exclude-editable > requirements.txt
```

## Compatibility

* Python 3.7+
* SQLite 3.22.0+
    * Ubuntu 18.04 LTS has libsqlite3-0 = 3.22.0

## SQLite guidelines

* don’t use [UPSERT](https://sqlite.org/lang_upsert.html) aka INSERT ON CONFLICT (unavailable < SQLite 3.24.0)
* don’t use [generated columns](https://sqlite.org/gencol.html) (unavailable < SQLite 3.31.0)
* don’t use [JSON functions](https://sqlite.org/json1.html) (optional < SQLite 3.38.0+)
* give each table foo a `"foo_id" INTEGER PRIMARY KEY` with exactly that syntax ([rowid alias](https://sqlite.org/lang_createtable.html#rowids_and_the_integer_primary_key))
    * having a rowid alias means you can use Cursor.lastrowid, and ensures rowid is stable under VACUUM
    * `"foo"."foo_id"` is a bit redundant, but `"id"` can get accidentally shadowed in row dicts
    * non-rowid primary keys like (path,subtest) are cute, but they waste space and misbehave on NULL
* NULL in sqlite behaves like NaN sometimes, so if treating NULL as an ordinary column value:
    * compare those columns with IS, not = (the latter yields NULL if either side is NULL)
    * ok to create non-UNIQUE indexes involving those columns (NULL can be indexed)
    * ok to GROUP BY those columns (NULL values are equal in this context)
    * ok to SELECT DISTINCT those columns (NULL values are equal in this context)
    * don’t create UNIQUE indexes involving those columns (they won’t do what you want)
    * don’t create UNIQUE constraints involving those columns (they won’t do what you want)
    * don’t create PRIMARY KEY constraints involving those columns (they won’t do what you want)
    * don’t create FOREIGN KEY constraints involving those columns (they won’t do what you want)
* when writing schema migrations:
    * check the [SQLite guide to schema changes](https://sqlite.org/lang_altertable.html#making_other_kinds_of_table_schema_changes)
    * if new columns can’t be filled in SQLite alone (e.g. crc32), make them NULL and update in application code
    * don’t modify old migrations that have been deployed to production
