from __future__ import print_function

import datetime

from pygerrit2.rest import GerritRestAPI
from pygerrit2.rest.auth import HTTPBasicAuthFromNetrc
from pymongo import MongoClient, ASCENDING

ALL_OPTIONS = ['DETAILED_LABELS', 'ALL_REVISIONS', 'ALL_COMMITS',
               'DETAILED_ACCOUNTS', 'MESSAGES', 'COMMIT_FOOTERS']


class GerritMongoDatabase:
    def __init__(self, name):
        client = MongoClient()
        self.name = name
        db = client[self.name]
        self.changes = db.changes
        self.meta = db.meta
        self.changes.create_index([('id', ASCENDING)], unique=True)
        self.meta.create_index([('name', ASCENDING)], unique=True)

    def get_last_update(self):
        metadata = self.meta.find_one({'name': self.name})
        if metadata:
            return metadata['last-update']
        return None

    def set_last_update(self, timestamp):
        update_filter = {'name': self.name}
        update = {'name': self.name, 'last-update': timestamp}
        self.meta.replace_one(update_filter, update, upsert=True)

    def update_change(self, change):
        self.changes.replace_one(
            {'id': change['id']},
            change,
            bypass_document_validation=True,
            upsert=True)

    def change_count(self):
        return self.changes.count()


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
