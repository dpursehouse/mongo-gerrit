# mongo-gerrit

mongo-gerrit is a Python library to sync review data from a
[Gerrit Code Review](https://www.gerritcodereview.com/) server to a local
[MongoDB](https://www.mongodb.com/) database.

## Prerequisites and environment

mongo-gerrit has been developed on OSX with Python 2.7. It should also work
on other platforms, but has not been tested. Python 3 is not supported.

It is assumed that a MongoDB instance is running. If it's not running on the
default host and port (`localhost:27017`), this can be specified.

## Installation

mongo-gerrit is not distributed as a package. To install it, clone the source
code from the Github repository.

After cloning the source code, set up a virtual environment and install the
dependencies:

```bash
$ cd mongo-gerrit
$ virtualenv ENV
$ source ./ENV/bin/activate
(ENV) $ pip install -r requirements.txt
```

## Configuration

Configuration is done in a YAML file named `mongo-gerrit.yml` which may be
located either in the user's home folder or in the current directory.

The `mongo-gerrit.yml` file included in the repository defines configurations
for [gerrit-review](https://gerrit-review.googlesource.com) and
[android-review](https://android-review.googlesource.com) and default global
settings with reasonable values (as arbitrarily decided by the author).

### Global settings

Global settings are configured under the `settings` section.

```yaml
settings:
 query-options:
   - OPTION_NAME
   - OPTION_NAME
   - ...
 query-batch-size: 1000
 default-query: "age:1day"
```

- `query-options`: Options to be passed to Gerrit's [change query REST API]
(https://gerrit-documentation.storage.googleapis.com/Documentation/2.12.3/rest-api-changes.html#list-changes).
If not set, defaults to include almost all available options. The options
`CURRENT_FILES` and `ALL_FILES` are not supported; if these are given, they
will not be used.
- `query-batch-size`: Number of changes to query per batch. This should not be
set to a value that exceeds the [query limit]
(https://gerrit-documentation.storage.googleapis.com/Documentation/2.12.3/access-control.html#capability_queryLimit)
configured on the server. If not set, defaults to 500 which is the default
query limit on an out-of-the-box Gerrit installation.
- `default-query`: Default query to use on initial sync. If not set, defaults
to `age:1day`.

All global settings may be overridden per server in the `sites` section (described
below).

### Gerrit server settings

Settings for individual Gerrit servers are configured in blocks under the
`sites` section.

```yaml
sites:
 site-name:
   url: https://example.com/review/
   auth: basic
   query-options:
     - OPTION_NAME
     - OPTION_NAME
   query-batch-size: 300
   default-query: "owner:self"
```

- `site-name`: Unique identifier for this site. This will be used as the
database name in MongoDb.
- `url`: Required. The fully qualified URL to the Gerrit server.
- `auth`: Optional. Authentication type. May be `digest` or `basic`. Defaults to
`digest` if not specified.

## Usage

To sync review data from the site identified as `gerrit-review`:

```bash
(ENV) $ python sync.py gerrit-review
```

On the first run all changes found by the default query are fetched. This may take
a long time if the query results in a large number of changes.

On subsequent runs, only the changes that have been updated since the previous
sync will be fetched.

By default mongo-gerrit connects to MongoDB on the default hostname and
port (`localhost:27017`). Use `--database-hostname` and `--database-port` to
use a different location.

## Limitations, known problems, TODOs

- It's not possible to provide arbitrary queries to limit the results that
are returned.

- It's not possible to force re-sync of changes. Changes will only be
re-synched if they are updated in Gerrit after the previous sync.
