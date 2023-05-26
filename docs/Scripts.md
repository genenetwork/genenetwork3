# CLI Utility Scripts

This documents the various utility scripts that are provided with the project
whose purposes are to support the operation of the application in one way or
another.

To get a list of the available scripts/flask commands that can be run, do:

```sh
FLASK_APP="main.py" flask --help
```

With that, you should get a list of commands, which as of 2023-05-26 are:

```sh
. . . output truncated to save space ...

Commands:
  apply-migrations     Apply the dabasase migrations.
  assign-system-admin  Assign user with ID `user_id` administrator role.
  init-dev-clients     Initialise a development client for OAuth2 sessions.
  init-dev-users       Initialise development users for OAuth2 sessions.
  routes               Show the routes for the app.
  run                  Run a development server.
  shell                Run a shell in the app context.
```

*NB*: You can simply do `export FLASK_APP="main.py"` at the beginning of your
shell session and then just run the commands without prepending with the
`FLASK_APP="main.py"` declaration.

## Setting a User as System Administrator

Once you have registered the user with the new (as of 2023-05-26)
auth(entic|oris)ation system, you can then proceed to specify that the user is
going to be a system administrator of the system.

You will need to retrieve the users identifier (UUID) from the system; say the
UUID you get for the user is `5b15ef01-a9d7-4ee4-9a38-fe9dd1d871b8`, you can
then set that user as a system administrator by running:

```sh
FLASK_APP="main.py" flask assign-system-admin 5b15ef01-a9d7-4ee4-9a38-fe9dd1d871b8
```

## Make Existing Data Publicly Visible

This will only act on any existing data that is not already linked with a user
group in the new auth system.

This can be run using flask with

```sh
FLASK_APP="main.py" flask make-data-public
```

which will use the application's configuration settings for the
auth(entic|oris)ation database and the MariaDB database.

You could also run the script directly with:

```sh
python3 -m scripts.migrate_existing_data AUTHDBPATH MYSQLDBURI
```

where `AUTHDBPATH` and `MYSQLDBURI` are replaced with the appropriate values,
e.g.

```sh
python3 -m scripts.migrate_existing_data \
    /home/frederick/genenetwork/gn3_files/db/auth.db \
    mysql://webqtlout:webqtlout@127.0.0.1:3307/db_webqtl
```

## List Available Routes

```sh
FLASK_APP="main.py" flask routes
```

## Drop Into a Python Shell

```sh
FLASK_APP="main.py" flask shell
```

## Development Scripts

The commands in this section are meant for easing development and are not to be
run in a production environment.

### Setting up a Sample User for Development

```sh
FLASK_APP="main.py" flask init-dev-users
```

That will initialise your development database with a development user with the
following details:

- User ID: 0ad1917c-57da-46dc-b79e-c81c91e5b928
- Email: test@development.user
- Password: testpasswd

### Setting up Sample OAuth2 Client for Development

```sh
FLASK_APP="main.py" flask init-dev-clients
```
