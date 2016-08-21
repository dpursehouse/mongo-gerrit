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
located either in the user's home folder or the current directory.

### Global settings

Global settings are configured under the `settings` section.

```yaml
settings:
 query-options:
   - OPTION_NAME
   - OPTION_NAME
   - ...
```

- `query-options`: Options to be passed to Gerrit's [change query REST API]
(https://gerrit-documentation.storage.googleapis.com/Documentation/2.12.3/rest-api-changes.html#list-changes).
If not set, defaults to include almost all options (as arbitrarily decided by
the author). May be overridden per site.

### Gerrit server settings

Settings for individual gerrit servers are configured in blocks under the
`sites` section.

```yaml
sites:
 site-name:
   url: https://example.com/review/
   auth: basic
   query-options:
     - OPTION_NAME
     - OPTION_NAME
```

- `site-name`: Unique identifier for this site. This will be used as the
database name in MongoDb.
- `url`: Required. The fully qualified URL to the Gerrit server.
- `auth`: Optional. Authentication type. May be `digest` or `basic`. Defaults to
`digest` if not specified.
- `query-options`: Optional. If specified, overrides the options defined in
the global settings.

The `mongo-gerrit.yml` file included in the repository defines configurations
for [gerrit-review](https://gerrit-review.googlesource.com) and
[android-review](https://android-review.googlesource.com).

## Usage

To sync review data from the site identified as `gerrit-review`:

```bash
(ENV) $ python sync.py gerrit-review
```

On the first run all changes older than one day are fetched. This may take a
long time on servers with a large number of changes.

On subsequent runs, only the changes that have been updated since the previous
sync will be fetched.

By default mongo-gerrit connects to MongoDB on the default hostname and
port (`localhost:27017`). Use `--database-hostname` and `--database-port` to
use a different location.

## Limitations, known problems, TODOs

- Review data does not include file information as its format is not
accepted by MongoDB.

- It's not possible to provide arbitrary queries to limit the results that
are returned.

- It's not possible to force re-sync of changes. Changes will only be
re-synched if they are updated in Gerrit after the previous sync.
