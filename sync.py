from __future__ import print_function

import datetime

from pygerrit2.rest import GerritRestAPI
from pygerrit2.rest.auth import HTTPBasicAuthFromNetrc

from db import GerritMongoDatabase


ALL_OPTIONS = ['DETAILED_LABELS', 'ALL_REVISIONS', 'ALL_COMMITS',
               'DETAILED_ACCOUNTS', 'MESSAGES', 'COMMIT_FOOTERS']

url = 'https://gerrit-review.googlesource.com'
auth = HTTPBasicAuthFromNetrc(url=url)
gerrit = GerritRestAPI(url=url, auth=auth)
db = GerritMongoDatabase(name='gerrit-review')

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
