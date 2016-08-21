import datetime
import logging
import sys
from argparse import ArgumentParser
from os.path import expanduser, isfile, join

import yaml
from pygerrit2.rest import GerritRestAPI
from pygerrit2.rest.auth import HTTPBasicAuthFromNetrc, HTTPDigestAuthFromNetrc

from db import GerritMongoDatabase


DEFAULT_QUERY_OPTIONS = ['DETAILED_LABELS', 'ALL_REVISIONS', 'ALL_COMMITS',
                         'DETAILED_ACCOUNTS', 'MESSAGES', 'COMMIT_FOOTERS']
DEFAULT_QUERY_BATCH_SIZE = 500
DEFAULT_QUERY = "age:1day"
AUTH_METHODS = {
    'basic': HTTPBasicAuthFromNetrc,
    'digest': HTTPDigestAuthFromNetrc
}
CONFIG_FILENAME = 'mongo-gerrit.yml'


def fatal(message):
    logging.error(message)
    sys.exit(1)


def get_setting(config, site, setting):
    if setting not in config['sites'][site]:
        fatal("missing setting %d for site %d" % (setting, site))
    return config['sites'][site][setting]


def get_optional_setting(config, site, setting, default):
    if setting in config['sites'][site]:
        return config['sites'][site][setting]
    if 'settings' in config and setting in config['settings']:
        return config['settings'][setting]
    return default


parser = ArgumentParser()
parser.add_argument("site", help="Name of the Gerrit site to sync")
parser.add_argument("--verbose", action="store_true",
                    help="Enable verbose (debug) logging")
group = parser.add_argument_group("database")
group.add_argument("--database-hostname", action="store", default="localhost",
                   dest="host", metavar="HOSTNAME", help="MongoDB hostname")
group.add_argument("--database-port", action="store", default=27017, type=int,
                   dest="port", metavar="PORT", help="MongoDB port")
args = parser.parse_args()

FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
level = logging.DEBUG if args.verbose else logging.INFO
logging.basicConfig(format=FORMAT, level=level)

config_file = join(expanduser('~'), CONFIG_FILENAME)
if not isfile(config_file):
    config_file = CONFIG_FILENAME
    if not isfile(config_file):
        fatal('no config file')

try:
    with open(config_file) as f:
        config = yaml.load(f)
except Exception as e:
    fatal('error opening config file: %s' % e)

if config is None or "sites" not in config:
    fatal("no sites configured")

site = args.site
if site not in config['sites']:
    fatal("no config for site %s" % site)

url = get_setting(config, site, 'url')
auth = get_optional_setting(config, site, 'auth', 'digest')
if auth not in AUTH_METHODS:
    fatal("invalid authentication method %s" % auth)

query_options = get_optional_setting(config, site,
                                     'query-options',
                                     DEFAULT_QUERY_OPTIONS)
batch_size = get_optional_setting(config, site, 'query-batch-size',
                                  DEFAULT_QUERY_BATCH_SIZE)

try:
    gerrit = GerritRestAPI(url=url, auth=AUTH_METHODS[auth](url=url))
except ValueError as e:
    fatal("unable to configure Gerrit API: %s" % e)

db = GerritMongoDatabase(name=site, host=args.host, port=args.port)

last_update = db.get_last_update()
if last_update:
    terms = ["since:\"%s\"" % last_update]
else:
    default_query = get_optional_setting(config, site,
                                         'default-query', DEFAULT_QUERY)
    if not default_query:
        fatal('no default query configured')
    terms = [default_query]

term_string = "?q=" + "+".join(terms)
start_time = datetime.datetime.utcnow()
start = 0
more_changes = True
while more_changes:
    query = "&".join([term_string] +
                     ["S=%d" % start, "n=%d" % batch_size] +
                     ["o=%s" % o for o in query_options])
    logging.debug(query)

    results = gerrit.get("/changes/" + query)
    count = len(results)
    logging.info("fetched %d changes" % count)
    if count:
        for change in results:
            print(change['id'])
            db.update_change(change)
        more_changes = '_more_changes' in results[-1]
        start += batch_size
    else:
        more_changes = False

logging.info("database contains %d change records" % db.change_count())
db.set_last_update(start_time)
