import requests

import bcrypt
from flask import flash, jsonify, request, session, Blueprint

from gn3.auth import db
from gn3.settings import AUTH_DB

from .users import User, user_by_email

auth_routes = Blueprint("auth", __name__)

def valid_login(conn: db.DbConnection, user: User, password: str) -> bool:
    """Check the validity of the provided credentials for login."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            ("SELECT * FROM users LEFT JOIN user_credentials "
             "ON users.user_id=user_credentials.user_id "
             "WHERE users.user_id=?"),
            (str(user.user_id),))
        row = cursor.fetchone()

    if row == None:
        return False

    return bcrypt.checkpw(password.encode("utf-8"), row["password"])

@auth_routes.route("/login", methods=["POST"])
def login():
    """Log in the user."""
    print(request.cookies)
    if session.get("user"):
        flash("Already logged in!", "alert-warning")
        print(f"ALREADY LOGGED IN: {session['user']}")
        return redirect("/", code=302)

    form = request.form
    email = form.get("email").strip()
    password = form.get("password").strip()
    if email == "" or password == "":
        flash("You must provide the email and password!", "alert-error")
        return redirect("/", code=302)

    with db.connection(AUTH_DB) as conn:
        user = user_by_email(conn, email).maybe(False, lambda usr: usr)
        if user and valid_login(conn, user, password):
            session["user"] = user
            return jsonify({
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name
            }), 200

    return jsonify({
        "message": "Could not login. Invalid 'email' or 'password'.",
        "type": "authentication-error"
    }), 401
