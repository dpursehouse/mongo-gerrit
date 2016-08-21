from __future__ import print_function

import datetime
import sys
from argparse import ArgumentParser
from os.path import expanduser, isfile, join

import yaml
from pygerrit2.rest import GerritRestAPI
from pygerrit2.rest.auth import HTTPBasicAuthFromNetrc, HTTPDigestAuthFromNetrc

from db import GerritMongoDatabase


ALL_OPTIONS = ['DETAILED_LABELS', 'ALL_REVISIONS', 'ALL_COMMITS',
               'DETAILED_ACCOUNTS', 'MESSAGES', 'COMMIT_FOOTERS']
AUTH_METHODS = {
    'basic': HTTPBasicAuthFromNetrc,
    'digest': HTTPDigestAuthFromNetrc
}
CONFIG_FILENAME = 'mongo-gerrit.yml'


def fatal(message):
    print(message, file=sys.stderr)
    sys.exit(1)


def get_setting(config, site, setting):
    if setting not in config['sites'][site]:
        fatal("missing setting %d for site %d" % (setting, site))
    return config['sites'][site][setting]


def get_setting_with_default(config, site, setting, default):
    if setting in config['sites'][site]:
        return config['sites'][site][setting]
    return default


config_file = CONFIG_FILENAME
if not isfile(config_file):
    config_file = join(expanduser('~'), CONFIG_FILENAME)
    if not isfile(config_file):
        fatal('no config file')

try:
    with open("mongo-gerrit.yml") as f:
        config = yaml.load(f)
except Exception as e:
    fatal('error opening config file: %s' % e)

if "sites" not in config:
    fatal("no sites configured")

parser = ArgumentParser()
parser.add_argument("site", help="Name of the Gerrit site to sync")
args = parser.parse_args()

site = args.site
if site not in config['sites']:
    fatal("no config for site %s" % site)

url = get_setting(config, site, 'url')
auth = get_setting_with_default(config, site, 'auth', 'digest')
if auth not in AUTH_METHODS:
    fatal("invalid authentication method %s" % auth)

gerrit = GerritRestAPI(url=url, auth=AUTH_METHODS[auth](url=url))
db = GerritMongoDatabase(name=site)

last_update = db.get_last_update()
if last_update:
    terms = ["since:\"%s\"" % last_update]
else:
    terms = ["age:1day"]

term_string = "?q=" + "+".join(terms)
print(term_string)

start_time = datetime.datetime.utcnow()
start = 0
limit = 300
more_changes = True
while more_changes:
    query = "&".join([term_string] +
                     ["S=%d" % start, "n=%d" % limit] +
                     ["o=%s" % o for o in ALL_OPTIONS])
    print(query)

    results = gerrit.get("/changes/" + query)
    count = len(results)
    print("fetched %d changes" % count)
    if count:
        for change in results:
            print(change['id'])
            db.update_change(change)
        more_changes = '_more_changes' in results[-1]
        start += limit
    else:
        more_changes = False

print("database contains %d change records" % db.change_count())
db.set_last_update(start_time)
