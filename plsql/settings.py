import os

def rel(path):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# List of packages to dump
PLSQL_PACKAGES = [
    'PLSQLPARSERTESTPACKAGE',
]

# Path to storage of oracle schema objects
PLSQL_SCHEMA_ROOT = '/home/sites/superanimals/db/'


PLSQL_TEMPLATE_DIR =  rel('templates')

# connection parameters
ORA_SID = 'ORCL'
ORA_SCHEMA = 'sa'
ORA_PASSWORD = 'qwqw'
