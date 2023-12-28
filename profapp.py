# import html # html_code.escape() is used to thwart XSS attacks
import flask
import auth
from db_utils import InappropriateTextError
import db_utils as db
import os
import dotenv
import datetime

# ----------------------------------------------------------------------

app = flask.Flask(__name__, template_folder=".")

app.secret_key = os.environ["SECRET_KEY"]

dotenv.load_dotenv()
admin_users_str = os.environ["ADMIN_USERS"]
ADMIN_USERS = eval(admin_users_str)

# ----------------------------------------------------------------------


# Routes for authentication.
@app.route("/logoutapp", methods=["GET"])
def logoutapp():
    return auth.logoutapp()


@app.route("/logoutcas", methods=["GET"])
def logoutcas():
    return auth.logoutcas()


# ----------------------------------------------------------------------
@app.route("/", methods=["GET"])
def landing():
    html_code = flask.render_template("landing.html")
    response = flask.make_response(html_code)
    return response


# @app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
def index():
    flask.session["username"] = auth.authenticate()
    # flask.session["username"] = "eb1889"

    professors = db.get_all_professors()
    is_admin = flask.session.get("username") in ADMIN_USERS

    html_code = flask.render_template(
        "index.html",
        professors=professors,
        is_admin=is_admin,
        username=flask.session.get("username"),
    )
    response = flask.make_response(html_code)
    return response


@app.route("/search_results", methods=["GET"])
def search_results():
    name = flask.request.args.get("name")
    if name is None:
        name = ""
    dept = flask.request.args.get("dept")
    if dept is None:
        dept = ""

    professors = db.query_professor_keyword(name, dept)

    html_code = flask.render_template("search_results.html", professors=professors)
    response = flask.make_response(html_code)
    return response


@app.route("/review_form", methods=["GET"])
def review_form():
    profs = db.get_all_professors()

    username = flask.session.get("username")
    if username is None:
        flask.session["username"] = auth.authenticate()
        # flask.session["username"] = "eb1889"

    is_admin = flask.session.get("username") in ADMIN_USERS
    is_banned = db.is_banned(username)

    html_code = flask.render_template(
        "review.html",
        profs=profs,
        is_admin=is_admin,
        is_banned=is_banned,
        username=flask.session.get("username"),
    )
    response = flask.make_response(html_code)
    return response


@app.route("/review", methods=["POST"])
def review():
    professor = flask.request.form.get("professor")
    parse = professor.split(", ")
    name, department = parse[0], parse[1]

    content = float(flask.request.form.get("content"))
    delivery = float(flask.request.form.get("delivery"))
    availability = float(flask.request.form.get("availability"))
    organization = float(flask.request.form.get("organization"))
    comment = flask.request.form.get("comment")
    courses = flask.request.form.get("courses")
    username = flask.session.get("username")

    try:
        db.add_review(
            name,
            department,
            username,
            content,
            delivery,
            availability,
            organization,
            comment,
            courses,
        )
    except InappropriateTextError as ex:
        is_admin = flask.session.get("username") in ADMIN_USERS
        html_code = flask.render_template(
            "error.html", is_admin=is_admin, username=username, error_msg=ex
        )
        response = flask.make_response(html_code)
        return response

    is_admin = flask.session.get("username") in ADMIN_USERS
    html_code = flask.render_template(
        "thanks.html", is_admin=is_admin, username=username
    )
    response = flask.make_response(html_code)
    return response


@app.route("/prof_details", methods=["GET"])
def prof_details():
    name = flask.request.args.get("name")
    dept = flask.request.args.get("dept")

    reviews = db.get_reviews(name, dept)
    prof = db.get_professor(name, dept)

    html_code = flask.render_template("detailtable.html", reviews=reviews, prof=prof)
    response = flask.make_response(html_code)
    return response


@app.route("/adminlandingpage", methods=["GET"])
def admin_page():
    username = flask.session.get("username")
    if username is None:
        flask.session["username"] = auth.authenticate()
        # flask.session["username"] = "eb1889"

    is_admin = flask.session.get("username") in ADMIN_USERS

    html_code = flask.render_template(
        "adminlanding.html", is_admin=is_admin, username=username
    )
    response = flask.make_response(html_code)
    return response


@app.route("/adminprofpage", methods=["GET"])
def admin_landing_page():
    username = flask.session.get("username")
    if username is None:
        flask.session["username"] = auth.authenticate()
        # flask.session["username"] = "eb1889"

    is_admin = flask.session.get("username") in ADMIN_USERS
    profs = db.get_all_professors()
    html_code = flask.render_template(
        "adminprofpage.html", profs=profs, is_admin=is_admin
    )
    response = flask.make_response(html_code)
    return response


@app.route("/adminuserpage", methods=["GET"])
def admin_user_track_page():
    username = flask.session.get("username")
    if username is None:
        flask.session["username"] = auth.authenticate()
        # flask.session["username"] = "eb1889"

    is_admin = flask.session.get("username") in ADMIN_USERS

    usernames = db.get_all_users()
    html_code = flask.render_template(
        "adminuserpage.html", usernames=usernames, is_admin=is_admin
    )
    response = flask.make_response(html_code)
    return response


@app.route("/adminusertable", methods=["GET"])
def admin_user_table():
    username = flask.request.args.get("username")

    try:
        reviews = db.get_user_reviews(username)
        is_banned = db.is_banned(username)
        prof = db.get_prof_from_review
    except Exception as ex:
        html_code = flask.render_template(
            "error_admin.html", error_msg="Invalid Input"
        )  # if success is False:
        response = flask.make_response(html_code)
        return response

    html_code = flask.render_template(
        "adminusertable.html",
        is_banned=is_banned,
        reviews=reviews,
        username=username,
        get_professor=prof,
    )
    response = flask.make_response(html_code)
    return response


@app.route("/adminproftable", methods=["GET"])
def admin_prof_table():
    profname = flask.request.args.get("profname")
    profdept = flask.request.args.get("profdept")

    try:
        reviews = db.get_reviews(profname, profdept)
    except Exception as ex:
        html_code = flask.render_template("error_admin.html", error_msg="Invalid Input")
        response = flask.make_response(html_code)
        return response

    html_code = flask.render_template(
        "adminproftable.html", reviews=reviews, profname=profname, profdept=profdept
    )
    response = flask.make_response(html_code)
    return response


@app.route("/delete_review", methods=["DELETE"])
def delete_review():
    review_id = flask.request.args.get("reviewId")
    db.delete_review(review_id)

    prof_name = flask.request.args.get("profName")
    prof_dept = flask.request.args.get("profDept")
    reviews = db.get_reviews(prof_name, prof_dept)

    html_code = flask.render_template(
        "adminproftable.html", reviews=reviews, profname=prof_name
    )
    response = flask.make_response(html_code)

    return response


@app.route("/delete_all_reviews", methods=["DELETE"])
def delete_all_reviews():
    username = flask.request.args.get("username")

    db.delete_all_reviews(username)
    db.ban_user(username)

    return "All reviews deleted successfully"


@app.route("/adminProfResults", methods=["GET"])
def adminProfResults():
    prof = flask.request.args.get("prof")
    if prof is None:
        prof = ""

    professors = db.query_professor_keyword(prof)

    html_code = flask.render_template("adminProfResults.html", professors=professors)
    response = flask.make_response(html_code)
    return response


@app.route("/adminUserResults", methods=["GET"])
def adminUserResults():
    user = flask.request.args.get("user")
    if user is None:
        user = ""

    usernames = db.query_username_keyword(user)

    html_code = flask.render_template("adminUserResults.html", usernames=usernames)
    response = flask.make_response(html_code)
    return response


@app.route("/bannedusers", methods=["GET"])
def banned_users():
    usernames = db.get_all_banned_users()

    html_code = flask.render_template("bannedusers.html", usernames=usernames)
    response = flask.make_response(html_code)
    return response


@app.route("/unban", methods=["GET"])
def unban():
    username = flask.request.args.get("username")
    db.unban_user(username)

    usernames = db.get_all_banned_users()
    html_code = flask.render_template("bannedusers.html", usernames=usernames)
    response = flask.make_response(html_code)
    return response


@app.route("/help", methods=["GET"])
def help_page():
    username = flask.session.get("username")
    if username is None:
        flask.session["username"] = auth.authenticate()
        # flask.session["username"] = "eb1889"

    is_admin = flask.session.get("username") in ADMIN_USERS
    html_code = flask.render_template("help.html", username=username, is_admin=is_admin)
    response = flask.make_response(html_code)
    return response
