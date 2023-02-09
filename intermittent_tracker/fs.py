import os


def mkdir_data():
    try:
        os.mkdir(working_path('data'))
    except FileExistsError:
        pass


def working_path(path):
    """Get the path to some file in the running instance state."""
    return path


def package_path(path):
    """Get the path to some file shipped with the package."""
    return os.path.join(os.path.dirname(__file__), path)


CONFIG_PATH = working_path('config.json')
ISSUES_JSON_PATH = working_path('data/issues.json')
DASHBOARD_SQLITE_PATH = working_path('data/dashboard.sqlite')
SCHEMA_PATH = package_path('schema')
STATIC_PATH = package_path('static')  # this is the default in flask
TESTS_JSON_PATH = package_path('tests.json')
