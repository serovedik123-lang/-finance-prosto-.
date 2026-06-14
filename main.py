from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DB_NAME = "users.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not username or not password:
            flash("Заполни логин и пароль")
            return redirect(url_for("register"))

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), 0)
            )
            conn.commit()
            flash("Регистрация успешна. Теперь войди в аккаунт.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Такой логин уже занят")
            return redirect(url_for("register"))
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        else:
            flash("Неверный логин или пароль")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    conn.close()
    return render_template("dashboard.html", user=user)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/deposit-demo", methods=["POST"])
@login_required
def deposit_demo():
    amount = float(request.form.get("amount", 0))
    if amount > 0:
        conn = get_db()
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE id = ?",
            (amount, session["user_id"])
        )
        conn.commit()
        conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
