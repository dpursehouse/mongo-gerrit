from __future__ import print_function

import datetime
import sys
from argparse import ArgumentParser
from ConfigParser import ConfigParser
from os.path import expanduser

from pygerrit2.rest import GerritRestAPI
from pygerrit2.rest.auth import HTTPBasicAuthFromNetrc, HTTPDigestAuthFromNetrc

from db import GerritMongoDatabase


ALL_OPTIONS = ['DETAILED_LABELS', 'ALL_REVISIONS', 'ALL_COMMITS',
               'DETAILED_ACCOUNTS', 'MESSAGES', 'COMMIT_FOOTERS']
AUTH_METHODS = {
    'basic': HTTPBasicAuthFromNetrc,
    'digest': HTTPDigestAuthFromNetrc
}


def get_setting(config, site, setting):
    value = config.get(site, setting)
    if not value:
        print("missing setting %d for site %d" % (setting, site),
              file=sys.stderr)
        exit(1)
    return value

def get_setting_with_default(config, site, setting, default):
    value = config.get(site, setting)
    if not value:
        value = default
    return value


config = ConfigParser()
config.read(['mongo-gerrit.ini', expanduser('~/mongo-gerrit.ini')])

parser = ArgumentParser()
parser.add_argument("site", help="Name of the Gerrit site to sync")
args = parser.parse_args()

site = args.site
if not config.has_section(site):
    print("no config for site %s" % site, file=sys.stderr)
    exit(1)

url = get_setting(config, site, 'url')
auth = get_setting_with_default(config, site, 'auth', 'digest')
if auth not in AUTH_METHODS:
    print("invalid authentication method %s" % auth, file=sys.stderr)
    exit(1)

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
