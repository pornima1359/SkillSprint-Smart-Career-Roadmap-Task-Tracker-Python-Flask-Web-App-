from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "skillsprint_secret_key"

DB = "database.db"


# ----------------- DB Setup -----------------
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS roadmap(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        goal TEXT,
        week INTEGER,
        topic TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task_date TEXT,
        task TEXT,
        done INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


init_db()


def get_db():
    return sqlite3.connect(DB)


# ----------------- Roadmap Generator -----------------
def generate_roadmap(goal):
    plans = {
        "Web Development": [
            "HTML + CSS Basics", "JavaScript Basics", "Bootstrap + Responsive Design",
            "Python Flask Basics", "Database + SQLite", "Authentication System",
            "APIs + JSON", "Final Project + Deployment"
        ],
        "Data Analyst": [
            "Python Basics", "NumPy + Pandas", "Data Cleaning",
            "Matplotlib + Visualization", "SQL Basics", "Exploratory Data Analysis",
            "Mini Project", "Portfolio + Resume"
        ],
        "Cyber Security": [
            "Networking Basics", "Linux Basics", "Security Fundamentals",
            "Web Security Basics", "Cryptography Intro", "Tools: Nmap/Wireshark",
            "CTF Practice", "Final Security Project"
        ],
        "Android Development": [
            "Java/Kotlin Basics", "Android UI", "Layouts + Activities",
            "Firebase Basics", "API Integration", "RecyclerView + Storage",
            "Mini App", "Final App + Publish"
        ]
    }

    return plans.get(goal, [
        "Basics", "Intermediate Concepts", "Project Planning",
        "Development", "Testing", "Improvement",
        "Documentation", "Final Submission"
    ])


def login_required():
    return "user_id" in session


# ----------------- Routes -----------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users(name,email,password,created_at) VALUES(?,?,?,?)",
                        (name, email, password, str(datetime.now())))
            conn.commit()
            flash("✅ Registration successful. Please login!", "success")
            return redirect(url_for("login"))
        except:
            flash("⚠ Email already registered!", "danger")
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, password, name FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["user_name"] = user[2]
            flash("✅ Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("❌ Invalid login credentials!", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("✅ Logged out successfully!", "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id=?", (session["user_id"],))
    total_tasks = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND done=1", (session["user_id"],))
    completed_tasks = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM roadmap WHERE user_id=?", (session["user_id"],))
    total_roadmap = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM roadmap WHERE user_id=? AND status='Done'", (session["user_id"],))
    done_roadmap = cur.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        total_roadmap=total_roadmap,
        done_roadmap=done_roadmap
    )


@app.route("/create-roadmap", methods=["GET", "POST"])
def create_roadmap():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        goal = request.form["goal"]
        topics = generate_roadmap(goal)

        conn = get_db()
        cur = conn.cursor()

        cur.execute("DELETE FROM roadmap WHERE user_id=?", (session["user_id"],))

        for i, topic in enumerate(topics, start=1):
            cur.execute("INSERT INTO roadmap(user_id,goal,week,topic,status) VALUES(?,?,?,?,?)",
                        (session["user_id"], goal, i, topic, "Pending"))

        conn.commit()
        conn.close()

        flash("✅ Roadmap created successfully!", "success")
        return redirect(url_for("roadmap"))

    return render_template("roadmap.html", mode="create")


@app.route("/roadmap")
def roadmap():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, week, topic, status FROM roadmap WHERE user_id=? ORDER BY week",
                (session["user_id"],))
    rows = cur.fetchall()
    conn.close()

    return render_template("roadmap.html", mode="view", roadmap=rows)


@app.route("/roadmap-done/<int:rid>")
def roadmap_done(rid):
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE roadmap SET status='Done' WHERE id=? AND user_id=?", (rid, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect(url_for("roadmap"))


@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        task_text = request.form["task"]
        tdate = request.form["date"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO tasks(user_id, task_date, task, done) VALUES(?,?,?,0)",
                    (session["user_id"], tdate, task_text))
        conn.commit()
        conn.close()

        flash("✅ Task added!", "success")
        return redirect(url_for("tasks"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, task_date, task, done FROM tasks WHERE user_id=? ORDER BY task_date DESC",
                (session["user_id"],))
    task_rows = cur.fetchall()
    conn.close()

    return render_template("tasks.html", tasks=task_rows)


@app.route("/task-toggle/<int:tid>")
def task_toggle(tid):
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT done FROM tasks WHERE id=? AND user_id=?", (tid, session["user_id"]))
    row = cur.fetchone()

    if row:
        new_val = 0 if row[0] == 1 else 1
        cur.execute("UPDATE tasks SET done=? WHERE id=? AND user_id=?", (new_val, tid, session["user_id"]))
        conn.commit()

    conn.close()
    return redirect(url_for("tasks"))


@app.route("/progress")
def progress():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id=?", (session["user_id"],))
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND done=1", (session["user_id"],))
    done = cur.fetchone()[0]

    percent = 0
    if total > 0:
        percent = int((done / total) * 100)

    conn.close()

    return render_template("progress.html", total=total, done=done, percent=percent)


if __name__ == "__main__":
    app.run(debug=True)
