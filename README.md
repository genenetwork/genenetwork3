# genenetwork3
GeneNetwork3 REST API for data science and machine  learning

## Installation

#### GNU Guix packages

Install GNU Guix - this can be done on every running Linux system.

There are at least three ways to start GeneNetwork3 with GNU Guix:

1. Create an environment with `guix environment`
2. Create a container with `guix environment -C`
3. Use a profile and shell settings with `source ~/opt/genenetwork3/etc/profile`

#### Create an environment:

Simply load up the environment (for development purposes):

```bash
guix environment --load=guix.scm
```

Also, make sure you have the [guix-bioinformatics](https://git.genenetwork.org/guix-bioinformatics/guix-bioinformatics) channel set up.

```bash
~/.config/guix/current/bin/guix environment --expose=$HOME/genotype_files/ --load=guix.scm
python3
  import redis
```

#### Run a Guix container

```
~/.config/guix/current/bin/guix environment -C --network --expose=$HOME/genotype_files/ --load=guix.scm
```


#### Using a Guix profile (or rolling back)

Create a new profile with

```
~/.config/guix/current/bin/guix package -i genenetwork3 -p ~/opt/genenetwork3
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

## Running Tests

(assuming you are in a guix container; otherwise use venv!)

To run tests:

```bash
python -m unittest discover -v
```

Running pylint:

```bash
pylint *py tests gn3
```

Running mypy(type-checker):

```bash
mypy .
```

## Running the GN3 web service

To spin up the server on its own (for development):

```bash
env FLASK_DEBUG=1 FLASK_APP="main.py" flask run --port=8080
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
