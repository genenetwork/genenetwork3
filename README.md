# genenetwork3
GeneNetwork3 REST API for data science and machine  learning

## Installation

#### Using guix

Simply load up the environment (for development purposes):

```bash
guix environment --load=guix.scm
```

Also, make sure you have the *guix-bioinformatics* channel set up.

```bash
env GUIX_PACKAGE_PATH=~/guix-bioinformatics/ ~/.config/guix/current/bin/guix environment --load=guix.scm
python3
  import redis
```

Better run a proper container

```
env GUIX_PACKAGE_PATH=~/guix-bioinformatics/ ~/.config/guix/current/bin/guix environment -C --network --load=guix.scm 
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

To spin up the server:

```bash
env FLASK_DEBUG=1 FLASK_APP="main.py" flask run --port=8080
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
