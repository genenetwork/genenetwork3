# genenetwork3

[![GeneNetwork3 CI
badge](https://ci.genenetwork.org/badge/genenetwork3.svg)](https://ci.genenetwork.org/jobs/genenetwork3)
[![GeneNetwork3 all tests CI
badge](https://ci.genenetwork.org/badge/genenetwork3-all-tests.svg)](https://ci.genenetwork.org/jobs/genenetwork3-all-tests)

GeneNetwork3 REST API for data science and machine learning

GeneNetwork3 is a light-weight back-end that serves different front-ends, including the GeneNetwork2 web UI.
Transports happen in multiple ways:

1. A REST API
2. Direct python library calls (using PYTHONPATH)

The main advantage is that the code is not cluttered by UX output and starting the webserver and running tests is *easier* than using GeneNetwork2. It allows for using Jupyter Notebooks and Pluto Notebooks as front-ends as well as using the API from R etc.

A continuously deployed instance of genenetwork3 is available at
[https://cd.genenetwork.org/](https://cd.genenetwork.org/). This instance is
redeployed on every commit provided that the [continuous integration
tests](https://ci.genenetwork.org/jobs/genenetwork3) pass.

## Configuration

The system comes with some default configurations found in **"gn3/settings.py"**
relative to the repository root.

To overwrite these settings without changing the file, you can provide a path in
the `GN3_CONF` environment variable, to a file containing those variables whose
values you want to change.

The `GN3_CONF` variable allows you to have your own environment-specific
configurations rather than being forced to conform to the defaults.

## Installation

#### GNU Guix packages

Install GNU Guix - this can be done on every running Linux system.

There are at least three ways to start GeneNetwork3 with GNU Guix:

1. Create an environment with `guix shell`
2. Create a container with `guix shell -C`
3. Use a profile and shell settings with `source ~/opt/genenetwork3/etc/profile`
4. Use the guix system container with GN3 directory mounted in

At this point we use all three for different purposes. In all cases you'll most likely need the mysql database.

#### Create an environment:

Simply load up the environment (for development purposes):

```bash
guix shell -Df guix.scm
```

Also, make sure you have the guix-bioinformatics channel set up correctly and this should work

```bash
guix shell --expose=$HOME/genotype_files/ -Df guix.scm
python3
  import redis
```

Check if guix and guix-bioinformatics channel are up-to-date with

```
guix describe
```

#### Run a Guix container with network

Containers provide full isolation from the underlying distribution. Very useful for figuring out any dependency issues:

```
guix shell -C --network --expose=$HOME/genotype_files/ -Df guix.scm
```

#### Using a Guix profile (or rolling back)

A guix profile is different from a Guix shell - it has less isolation from the underlying distribution.

Create a new profile with

```
guix package -i genenetwork3 -p ~/opt/genenetwork3
```

and load the profile settings with

```
source ~/opt/genenetwork3/etc/profile
start server...
```

Note that GN2 profiles include the GN3 profile (!). To roll genenetwork3 back you can use either in the same fashion (probably best to start a new shell first)

```
bash
source ~/opt/genenetwork2-older-version/etc/profile
set|grep store
run tests, server etc...
```

#### Troubleshooting Guix packages

If you get a Guix error, such as `ice-9/boot-9.scm:1669:16: In procedure raise-exception:
error: python-sqlalchemy-stubs: unbound variable` it typically means an update to guix latest is required (i.e., guix pull):

```
guix pull
source ~/.config/guix/current/etc/profile
```

and try again. Also make sure your ~/guix-bioinformatics is up to date.

See also instructions in [.guix.scm](.guix.scm).

#### Setting necessary configurations

These configurations should be set in an external config file, pointed to with the environment variable GN3_CONF.

- SPARQL_ENDPOINT (ex: "http://localhost:9082/sparql")
- XAPIAN_DB_PATH (ex: "/export/data/genenetwork/xapian")
- TMPDIR
- SPARQL_USER
- SPARQL_ENDPOINT (ex: "http://localhost:9082/sparql-auth/")
- GN3_SECRETS

TMPDIR also needs to be set correctly for the R script(s) because they pass results on as files on the local system (previously there was an issue with it being set to /tmp instead of ~/genenetwork3/tmp). Note that the Guix build system should take care of the paths.

### Secrets

All of GN3's secret parameters are found inside the "GN3_SECRETS".  This file should contain the following:

```
SPARQL_USER = "dba"
SPARQL_PASSWORD = "dba"
SPARQL_AUTH_URI="http://localhost:8890/sparql-auth/"
SPARQL_CRUD_AUTH_URI="http://localhost:8890/sparql-graph-crud-auth"
FAHAMU_AUTH_TOKEN="XXXXXX"
```

Note: The sparql configurations are important for running tests I.e. `pytest -k rdf`.

### Setting up Virtuoso for Local Development

GN3 uses Virtuoso to:

- Fetch metadata for the Xapian indexing script
- Fetch metadata for some end-points
- Test SPARQL queries for some unit tests

Local development setup instructions can be found [here](https://issues.genenetwork.org/topics/engineering/working-with-virtuoso-locally), while a more comprehensive tutorial is available [here](https://issues.genenetwork.org/topics/systems/virtuoso).

## Command-Line Utility Scripts

This project has a number of utility scripts that are needed in specific cirscumstances, and whose purpose is to support the operation of this application in one way or another. Have a look at the [Scripts.md file](./docs/Scripts.md] to see the details for each of the scripts that are available.

## Example cURL Commands for OAuth2

In this section, we present some example request to the API using cURL to
acquire the token(s) and access resources.

### Request Token

```sh
curl -X POST http://localhost:8080/api/oauth2/token \
    -F "username=test@development.user" -F "password=testpasswd" \
    -F "grant_type=password" \
    -F "client_id=0bbfca82-d73f-4bd4-a140-5ae7abb4a64d" \
    -F "client_secret=yadabadaboo" \
    -F "scope=profile group role resource register-client user introspect migrate-data"
```

### Access a Resource

Once you have acquired a token as above, we can now access a resource with, for
example:

```sh
curl -X GET -H "Authorization: Bearer L3Q5mvehQeSUNQQbFLfrcUEdEyoknyblXWxlpKkvdl" \
    "http://localhost:8080/api/oauth2/group/members/8f8d7640-5d51-4445-ad68-7ab217439804"
```

to get all the members of a group with the ID
`8f8d7640-5d51-4445-ad68-7ab217439804`

or:

```sh
curl -X POST "http://localhost:8080/api/oauth2/user/register" \
    -F "email=a_new@users.email" -F "password=apasswd" \
    -F "confirm_password=apasswd"
```

where
`L3Q5mvehQeSUNQQbFLfrcUEdEyoknyblXWxlpKkvdl` is the token you got in the
**Request Token** section above.

## Running Tests

(assuming you are in a guix container; otherwise use venv!)

To run tests:

```bash
export AUTHLIB_INSECURE_TRANSPORT=true
export OAUTH2_ACCESS_TOKEN_GENERATOR="tests.unit.auth.test_token.gen_token"
pytest
```

To specify unit-tests:

```bash
export AUTHLIB_INSECURE_TRANSPORT=true
export OAUTH2_ACCESS_TOKEN_GENERATOR="tests.unit.auth.test_token.gen_token"
pytest -k unit_test
```

Running pylint:
```bash
pylint $(find . -name '*.py' | xargs)
```

Running mypy(type-checker):

```bash
mypy --show-error-codes .
```

## Running the GN3 web service

To spin up the server on its own (for development):

```bash
export FLASK_DEBUG=1
export FLASK_APP="main.py"
flask run --port=8080
```

And test with

```
curl localhost:8080/api/version
"1.0"
```

To run with gunicorn

```
gunicorn --bind 0.0.0.0:8080 wsgi:app
```

consider the following options for development `--bind 0.0.0.0:$SERVER_PORT --workers=1 --timeout 180 --reload wsgi`.

And for the scalable production version run

```
gunicorn --bind 0.0.0.0:8080 --workers 8 --keep-alive 6000 --max-requests 10 --max-requests-jitter 5 --timeout 1200 wsgi:app
```

(see also the [.guix_deploy](./.guix_deploy) script)

## Using python-pip

IMPORTANT NOTE: we do not recommend using pip tools, use Guix instead

1. Prepare your system. You need to make you have python > 3.8, and
   the ability to install modules.
2. Create and enter your virtualenv:

```bash
virtualenv --python python3 venv
. venv/bin/activate
```
3. Install the required packages

```bash
# The --ignore-installed flag forces packages to
# get installed in the venv even if they existed
# in the global env
pip install -r requirements.txt --ignore-installed
```

#### A note on dependencies

Make sure that the dependencies in the `requirements.txt` file match those in
guix. To freeze dependencies:

```bash
# Consistent way to ensure you don't capture globally
# installed packages
pip freeze --path venv/lib/python3.8/site-packages > requirements.txt

```

## Logging

During development, there is periodically need to log what the application is
doing to help resolve issues.

The logging system [was initialised](https://github.com/genenetwork/genenetwork3/commit/95f067a542424b76022595a74d660a7e84158f38)
to help with this.

Now, you can simply use the `current_app.logger.*` logging methods to log out
any information you desire: e.g.

```python
from flask import current_app

...

def some_function(arg1, arg2, **args, **kwargs):
    ...
    current_app.logger.debug(f"THE KWARGS: {kwargs}")
    ...
```

## Genotype Files

You can get the genotype files from http://ipfs.genenetwork.org/ipfs/QmXQy3DAUWJuYxubLHLkPMNCEVq1oV7844xWG2d1GSPFPL and save them on your host machine at, say `$HOME/genotype_files` with something like:

```bash
$ mkdir -p $HOME/genotype_files
$ cd $HOME/genotype_files
$ yes | 7z x genotype_files.tar.7z
$ tar xf genotype_files.tar
```

The `genotype_files.tar.7z` file seems to only contain the **BXD.geno** genotype file.

## QTLReaper (rust-qtlreaper) and Trait Files

To run QTL computations, this system makes use of the [rust-qtlreaper](https://github.com/chfi/rust-qtlreaper.git) utility.

To do this, the system needs to export the trait data into a tab-separated file, that can then be passed to the utility using the `--traits` option. For more information about the available options, please [see the rust-qtlreaper](https://github.com/chfi/rust-qtlreaper.git) repository.

### Traits File Format

The traits file begins with a header row/line with the column headers. The first column in the file has the header **"Trait"**. Every other column has a header for one of the strains in consideration.

Under the **"Trait"** column, the traits are numbered from **T1** to **T<n>** where **<n>** is the count of the total number of traits in consideration.

As an example, you could end up with a trait file like the following:

```txt
Trait	BXD27	BXD32	DBA/2J	BXD21	...
T1	10.5735	9.27408	9.48255	9.18253	...
T2	6.4471	6.7191	5.98015	6.68051	...
...
```

It is very important that the column header names for the strains correspond to the genotype file used.

## Partial Correlations

The partial correlations feature depends on the following external systems to run correctly:

- Redis: Acts as a communications broker between the webserver and external processes
- `sheepdog/worker.py`: Actually runs the external processes that do the computations

These two systems should be running in the background for the partial correlations feature to work correctly.
