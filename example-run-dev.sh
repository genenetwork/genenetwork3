
## An example script to run the development server.
## Copy to run-dev.sh and update the appropriate environment variables.

export SQL_URI="${SQL_URI:+${SQL_URI}}"
export FLASK_DEBUG=1
export FLASK_APP="main.py"
export AUTHLIB_INSECURE_TRANSPORT=true

CMD_ARGS=$@
if [ ${#CMD_ARGS} -eq 0 ]
then
    CMD_ARGS=("run" "--port=8080")
fi

if [ -z "${SQL_URI}" ]
then
    echo "ERROR: You need to specify the 'SQL_URI' environment variable";
    exit 1;
fi

# flask run --port=8080
flask ${CMD_ARGS[@]}
