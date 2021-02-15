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
pip install -r requirements.txt
```

#### Using guix

Simply load up the environment (for development purposes):

```bash
guix environment --load=guix.scm
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
