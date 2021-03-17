# genenetwork3
GeneNetwork3 REST API for data science and machine  learning

## Installation

##### Using python-pip

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

#### Using guix

Simply load up the environment (for development purposes):

```bash
guix environment --load=guix.scm
```

Also, make sure you have the *guix-bioinformatics* channel set up.

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
