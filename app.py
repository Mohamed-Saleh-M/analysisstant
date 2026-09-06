import os
import re
from datetime import datetime, timedelta

import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

DB_NAME = os.environ.get("DB_NAME", "stockapp")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "123456")
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DB_PORT", "5432")

conn = psycopg2.connect(
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
)

loggedin = 0
name_p = "User"
email_p = "email"

TOP_COMPANIES_SQL = """
    SELECT "companyIntId", "totalTradeQty", "totalTradeValue", "totalTrades"
    FROM nse_script_closing_prs_data
    WHERE "tradeDate" = %s
    ORDER BY ("totalTrades" * ("totalTradeValue" / "totalTradeQty")) DESC
    LIMIT 3
"""

MARKET_SUMMARY_SQL = """
    SELECT count("internalId"), sum("totalTradeQty"), sum("totalTradeValue"), sum("totalTrades")
    FROM nse_script_closing_prs_data
    WHERE "tradeDate" = %s
"""


def get_recent_market_summary():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    days_ago = 0
    while True:
        days_ago += 1
        trade_day = datetime.now() - timedelta(days=days_ago)
        qdate = trade_day.strftime("%Y-%m-%d")
        date1 = trade_day.strftime("%d/%m/%Y")
        date2 = trade_day.strftime("%d %B %Y")
        cursor.execute(TOP_COMPANIES_SQL, (qdate,))
        if cursor.fetchone():
            break
    cursor.execute(TOP_COMPANIES_SQL, (qdate,))
    top_companies = cursor.fetchall()
    cursor.execute(MARKET_SUMMARY_SQL, (qdate,))
    market_summary = cursor.fetchone()
    return top_companies, market_summary, date1, date2


@app.route("/")
def home():
    global loggedin
    loggedin = 0
    return render_template("home.html")


@app.route("/home")
def home2():
    global loggedin
    loggedin = 0
    return render_template("home.html")


@app.route("/about")
def about():
    global loggedin
    loggedin = 0
    return render_template("about.html")


@app.route("/login")
def login():
    global loggedin
    loggedin = 0
    return render_template("login.html")


@app.route("/login_validation", methods=["POST"])
def login_validation():
    global email_p, name_p, loggedin
    email_p = request.form.get("emailid")
    password = request.form.get("password")
    try:
        if not email_p or not password:
            return render_template("login.html", error="Please fill the form completely !")
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM users WHERE emailid LIKE %s", (email_p.lower(),))
        user_object = cursor.fetchone()
        if user_object:
            name_p = user_object["name"]
            if check_password_hash(user_object["password"], password):
                loggedin = 1
                top_companies, market_summary, date1, date2 = get_recent_market_summary()
                return render_template(
                    "userpage.html",
                    v1=market_summary,
                    uname=name_p,
                    data=top_companies,
                    date1=date1,
                    date2=date2,
                )
            loggedin = 0
            return render_template("login.html", error="Incorrect Password, please try again !")
        loggedin = 0
        return render_template("login.html", error="Email ID not registered, please sign up and try again !")
    except Exception:
        loggedin = 0
        return render_template("server_error.html")


@app.route("/register")
def register():
    global loggedin
    loggedin = 0
    return render_template("register.html")


@app.route("/register_validation", methods=["POST"])
def register_validation():
    global name_p, email_p, loggedin
    name_p = request.form.get("name")
    email_p = request.form.get("emailid")
    password = request.form.get("password")
    try:
        if not name_p or not email_p or not password:
            return render_template("register.html", error="Please fill the form completely !")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email_p):
            return render_template("register.html", error="Please enter valid Email ID !")
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM users WHERE emailid LIKE %s", (email_p.lower(),))
        if cursor.fetchone():
            loggedin = 0
            return render_template("register.html", error="Given Email ID is already registered !")
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users(name, emailid, password) VALUES(%s, %s, %s)",
            (name_p, email_p.lower(), hashed_password),
        )
        conn.commit()
        loggedin = 1
        top_companies, market_summary, date1, date2 = get_recent_market_summary()
        return render_template(
            "userpage.html",
            v1=market_summary,
            uname=name_p,
            data=top_companies,
            date1=date1,
            date2=date2,
        )
    except Exception:
        loggedin = 0
        return render_template("server_error.html")


@app.route("/nsedata", methods=["GET"])
def nse_data():
    global loggedin
    if loggedin == 1:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM nse_script_closing_prs_data")
        data = cursor.fetchall()
        return render_template("nse_data.html", data=data)
    loggedin = 0
    return render_template("server_error.html")


@app.route("/userpage", methods=["GET"])
def userpage():
    global loggedin
    if loggedin == 1:
        top_companies, market_summary, date1, date2 = get_recent_market_summary()
        return render_template(
            "userpage.html",
            v1=market_summary,
            uname=name_p,
            data=top_companies,
            date1=date1,
            date2=date2,
        )
    loggedin = 0
    return render_template("server_error.html")


@app.route("/companies", methods=["GET"])
def companies():
    global loggedin
    if loggedin == 1:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM "Company"')
        data = cursor.fetchall()
        return render_template("companies.html", data=data)
    loggedin = 0
    return render_template("server_error.html")


@app.route("/profile", methods=["GET"])
def profile():
    global loggedin
    if loggedin == 1:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM users WHERE emailid LIKE %s", (email_p,))
        data = cursor.fetchone()
        return render_template("profile.html", data=data)
    loggedin = 0
    return render_template("server_error.html")


if __name__ == "__main__":
    app.run(debug=True)