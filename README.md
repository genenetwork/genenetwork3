# genenetwork3

[![GeneNetwork3 CI
badge](https://ci.genenetwork.org/badge/genenetwork3.svg)](https://ci.genenetwork.org/jobs/genenetwork3)
[![GeneNetwork3 pylint CI
badge](https://ci.genenetwork.org/badge/genenetwork3-pylint.svg)](https://ci.genenetwork.org/jobs/genenetwork3-pylint)
[![GeneNetwork3 mypy CI badge](https://ci.genenetwork.org/badge/genenetwork3-mypy.svg)](https://ci.genenetwork.org/jobs/genenetwork3-mypy)

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



## Installation

#### GNU Guix packages

Install GNU Guix - this can be done on every running Linux system.

There are at least three ways to start GeneNetwork3 with GNU Guix:

1. Create an environment with `guix shell`
2. Create a container with `guix shell -C`
3. Use a profile and shell settings with `source ~/opt/genenetwork3/etc/profile`

#### Create an environment:

Simply load up the environment (for development purposes):

```bash
guix shell -Df guix.scm
```

Also, make sure you have the [guix-bioinformatics](https://git.genenetwork.org/guix-bioinformatics/guix-bioinformatics) channel set up.

```bash
guix shell --expose=$HOME/genotype_files/ -Df guix.scm
python3
  import redis
```

#### Run a Guix container

```
guix shell -C --network --expose=$HOME/genotype_files/ -Df guix.scm
```

#### Using a Guix profile (or rolling back)

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
- RQTL_WRAPPER (ex: "~/genenetwork3/scripts/rqtl_wrapper.R")
- XAPIAN_DB_PATH (ex: "/export/data/genenetwork/xapian")

TMPDIR also needs to be set correctly for the R script(s) (previously there was an issue with it being set to /tmp instead of ~/genenetwork3/tmp)

## Migrations

**NOTE**: Do not create migration scripts manually. Use the processes indicated below.

### Authentication/Authorisation Migrations

The migration scripts for the authentication and authorisation system are in the *migrations/auth* folder in the root of the repository.

To create an new migration script for the, do:

```bash
$ yoyo new -m "<description of the migration>" ./migrations/auth/
```

The command will ask whether you want to save the migration configuration, e.g.

```bash
$ yoyo new --config=yoyo.auth.ini -m "testing a new migration"
Error: could not open editor!
Created file ./migrations/auth/20221103_02_HBzwk-testing-a-new-migration.py
Save migration configuration to yoyo.ini?
This is saved in plain text and contains your database password.

Answering 'y' means you do not have to specify the migration source or database connection for future runs [yn]:
```

If you specify `y` then a file named yoyo.ini will be created in your current working directory, and you can refer to it to avoid providing the `./migrations/auth` explicitly.

Now you can open and edit the scripts to provide the appropriate SQL statements to update or rollback your schema.

### Running the Migrations

To apply the migrations, you can do something like:

```bash
$ yoyo apply --database="sqlite:////tmp/test-auth.db" ./migrations/auth/

[20221103_01_js9ub-initialise-the-auth-entic-oris-ation-database]
Shall I apply this migration? [Ynvdaqjk?]: Y

[20221103_02_sGrIs-create-user-credentials-table]
Shall I apply this migration? [Ynvdaqjk?]: Y

[20221108_01_CoxYh-create-the-groups-table]
Shall I apply this migration? [Ynvdaqjk?]: Y

[20221108_02_wxTr9-create-privileges-table]
Shall I apply this migration? [Ynvdaqjk?]: Y

...
```

If you have previously initialised the yoyo config file, you can put the database uri in the configuration file and just provide it to avoid the prompt to save the configuration.

As a convenience, and to enable the CI/CD to apply the migrations automatically, I have provided a flask cli command that can be run with:

```bash
$ export FLASK_APP=main.py
$ flask apply-migrations
```

This expects that the following two configuration variables are set in the application:

* `AUTH_MIGRATIONS`: path to the migration scripts
* `AUTH_DB`: path to the sqlite database file (will be created if absent)

## Running Tests

(assuming you are in a guix container; otherwise use venv!)

To run tests:

```bash
$ export AUTHLIB_INSECURE_TRANSPORT=true
$ export OAUTH2_ACCESS_TOKEN_GENERATOR="tests.unit.auth.test_token.gen_token"
$ pytest
```

To specify unit-tests:

```bash
$ export AUTHLIB_INSECURE_TRANSPORT=true
$ export OAUTH2_ACCESS_TOKEN_GENERATOR="tests.unit.auth.test_token.gen_token"
$ pytest -k unit_test
```

Running pylint:

```bash
pylint *py tests gn3 scripts sheepdog
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
