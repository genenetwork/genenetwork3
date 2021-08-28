# genenetwork3
GeneNetwork3 REST API for data science and machine  learning

## Installation

#### Using guix

Simply load up the environment (for development purposes):

```bash
guix environment --load=guix.scm
```

Also, make sure you have the [guix-bioinformatics](https://git.genenetwork.org/guix-bioinformatics/guix-bioinformatics) channel set up.

```bash
env GUIX_PACKAGE_PATH=~/guix-bioinformatics/ ~/.config/guix/current/bin/guix environment --load=guix.scm
python3
  import redis
```

Better run a proper container

```
env GUIX_PACKAGE_PATH=~/guix-bioinformatics/ ~/.config/guix/current/bin/guix environment -C --network --load=guix.scm
```

If you get a Guix error, such as `ice-9/boot-9.scm:1669:16: In procedure raise-exception:
error: python-sqlalchemy-stubs: unbound variable` it typically means an update to guix latest is required (i.e., guix pull):

```
guix pull
source ~/.config/guix/current/etc/profile
```

and try again.

See also instructions in [.guix.scm](.guix.scm).

#### Using a Guix profile (or rolling back)

Create a new profile with

```
env GUIX_PACKAGE_PATH=~/guix-bioinformatics/ ~/.config/guix/current/bin/guix package -i genenetwork3 -p ~/opt/genenetwork3
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

#### Running Tests

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

#### Running the flask app

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

##### Using python-pip

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
