intermittent-tracker
====================

To develop locally:

```sh
$ python3 -m venv .venv
$ . .venv/bin/activate
$ pip install -e .
$ cp config.json.example config.json
$ python3 -m intermittent_tracker.flask_server
```

To run tests:

```sh
$ . .venv/bin/activate
$ python3 -m intermittent_tracker.tests
```
