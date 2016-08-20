# mongo-gerrit

mongo-gerrit is a Python library to sync review data from a
[Gerrit Code Review](https://www.gerritcodereview.com/) server to a local
[MongoDB](https://www.mongodb.com/) database.

## Prerequisites and environment

mongo-gerrit has been developed on OSX with Python 2.7. It should also work
on other platforms, but has not been tested. Python 3 is not supported.

It is assumed that a MongoDB instance is running on the default host and
port (`localhost:27017`).

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

Configuration is done in a Windows-style .ini file named `mongo-gerrit.ini`
which may be located in the current directory or in the user's home folder.

Multiple Gerrit servers may be configured in multiple sections identified by
a `[section]` header. The name of the section corresponds to the name of the
database in MongoDB.

Within each section, the following settings are recognised:

- `url`: Required. The fully qualified URL to the Gerrit server.
- `auth`: Optional. Authentication type. May be `digest` or `basic`. Defaults to
`digest` if not specified.

Configuration is provided for gerrit-review and android-review.

## Usage

To sync review data from the site identified as `gerrit-review`:

```bash
(ENV) $ python sync.py gerrit-review
```

On the first run all changes older than one day are fetched. This may take a
long time on servers with a large number of changes.

On subsequent runs, only the changes that have been updated since the previous
sync will be fetched.

## Limitations, known problems, TODOs

- It's not possible to connect to MongoDB on any address other than the
default `localhost:27017`.

- Review data does not include file informaton as its format is not
accepted by MongoDB.

- It's not possible to provide arbitrary queries to limit the results that
are returned.

- It's not possible to force re-sync of changes. Changes will only be
re-synched if they are updated in Gerrit after the previous sync.
