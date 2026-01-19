from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import io
import csv

app = Flask(__name__)
app.secret_key = "skillsprint_pro_secret_key"
DB = "database.db"


# ---------------- DB ----------------
def get_db():
    return sqlite3.connect(DB)


def init_db():
    conn = get_db()
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

    # Multiple Roadmaps Support
    cur.execute("""
    CREATE TABLE IF NOT EXISTS roadmap_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        roadmap_name TEXT NOT NULL,
        goal TEXT NOT NULL,
        week INTEGER NOT NULL,
        topic TEXT NOT NULL,
        status TEXT DEFAULT 'Pending'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        task_date TEXT NOT NULL,
        task TEXT NOT NULL,
        done INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


init_db()


def login_required():
    return "user_id" in session


# ---------------- ROADMAP PLANS (15+ goals) ----------------
def get_goals_list():
    return [
        "Web Development",
        "Python Full Stack",
        "Java Full Stack",
        "Data Analyst",
        "Machine Learning",
        "AI / Deep Learning",
        "Cyber Security",
        "DevOps",
        "Cloud Computing",
        "Android Development",
        "UI/UX Design",
        "Competitive Programming",
        "Embedded Systems",
        "IoT",
        "Computer Networks"
    ]


def generate_roadmap(goal):
    plans = {
        "Web Development": [
            "HTML + CSS Basics", "JavaScript Basics", "Bootstrap + Responsive Design",
            "DOM + Projects", "Flask Basics", "Database + SQLite",
            "APIs + JSON", "Final Web Project"
        ],
        "Python Full Stack": [
            "Python Basics", "OOP in Python", "Flask Basics",
            "SQLite + CRUD", "Authentication", "APIs",
            "Frontend Integration", "Final Full Stack Project"
        ],
        "Java Full Stack": [
            "Core Java", "OOP + Collections", "JDBC + MySQL",
            "Spring Boot Basics", "REST APIs", "Frontend Basics",
            "Mini Project", "Final Full Stack Project"
        ],
        "Data Analyst": [
            "Python Basics", "NumPy + Pandas", "Data Cleaning",
            "Visualization (Matplotlib)", "SQL Basics", "EDA Techniques",
            "Mini Project", "Portfolio + Resume"
        ],
        "Machine Learning": [
            "Python Refresher", "Math for ML", "Data Preprocessing",
            "Supervised Learning", "Unsupervised Learning", "Evaluation & Tuning",
            "Mini ML Project", "Final ML Project"
        ],
        "AI / Deep Learning": [
            "Neural Networks Intro", "TensorFlow/PyTorch Basics", "CNN Basics",
            "RNN + LSTM", "Transfer Learning", "Optimization",
            "Mini AI Project", "Final Deep Learning Project"
        ],
        "Cyber Security": [
            "Networking Basics", "Linux Basics", "Security Fundamentals",
            "Web Security Basics", "Tools: Nmap/Wireshark", "Cryptography Intro",
            "CTF Practice", "Final Security Project"
        ],
        "DevOps": [
            "Linux + Git Basics", "Docker Basics", "Docker Compose",
            "CI/CD Intro", "GitHub Actions", "Kubernetes Basics",
            "Mini DevOps Project", "Final DevOps Project"
        ],
        "Cloud Computing": [
            "Cloud Basics", "AWS Services Intro", "EC2 + S3 Hands-on",
            "IAM + Security", "Deployment Basics", "Monitoring + Logs",
            "Mini Cloud Project", "Final Deployment Project"
        ],
        "Android Development": [
            "Java/Kotlin Basics", "Android UI", "Layouts + Activities",
            "Firebase Basics", "API Integration", "Storage + RecyclerView",
            "Mini App", "Final Android App"
        ],
        "UI/UX Design": [
            "Design Basics", "Figma Tools", "Wireframes",
            "UI Components", "User Research", "Prototyping",
            "Mini Design Project", "Portfolio Case Study"
        ],
        "Competitive Programming": [
            "Basics + STL", "Arrays + Strings", "Stack/Queue",
            "Recursion + Backtracking", "Trees + Graphs", "DP Basics",
            "Contest Practice", "Final CP Plan"
        ],
        "Embedded Systems": [
            "C Basics", "Microcontroller Intro", "GPIO + Sensors",
            "Communication Protocols", "Embedded Debugging", "RTOS Intro",
            "Mini Embedded Project", "Final Embedded Project"
        ],
        "IoT": [
            "IoT Basics", "Sensors + Actuators", "Arduino/ESP32 Basics",
            "MQTT + Networking", "Cloud Integration", "IoT Security",
            "Mini IoT Project", "Final IoT Project"
        ],
        "Computer Networks": [
            "OSI + TCP/IP", "IP Addressing", "Subnetting",
            "Routing Basics", "Switching + VLAN", "DNS + HTTP",
            "Wireshark Practice", "Mini Network Project"
        ]
    }

    return plans.get(goal, [
        "Basics", "Intermediate", "Practice",
        "Mini Project", "Advanced Concepts", "Testing",
        "Documentation", "Final Project"
    ])


# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")


# -------- AUTH --------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
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
        email = request.form["email"].strip()
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


# -------- DASHBOARD --------
@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    uid = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    # Tasks
    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id=?", (uid,))
    total_tasks = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND done=1", (uid,))
    done_tasks = cur.fetchone()[0]

    # Roadmap items
    cur.execute("SELECT COUNT(*) FROM roadmap_items WHERE user_id=?", (uid,))
    total_items = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM roadmap_items WHERE user_id=? AND status='Done'", (uid,))
    done_items = cur.fetchone()[0]

    # Recent tasks
    cur.execute("SELECT task_date, task, done FROM tasks WHERE user_id=? ORDER BY id DESC LIMIT 6", (uid,))
    recent_tasks = cur.fetchall()

    # Roadmap names count
    cur.execute("SELECT COUNT(DISTINCT roadmap_name) FROM roadmap_items WHERE user_id=?", (uid,))
    roadmap_count = cur.fetchone()[0]

    # Overall %
    total_all = total_tasks + total_items
    done_all = done_tasks + done_items
    overall_percent = int((done_all / total_all) * 100) if total_all > 0 else 0

    conn.close()

    return render_template("dashboard.html",
                           total_tasks=total_tasks,
                           done_tasks=done_tasks,
                           total_items=total_items,
                           done_items=done_items,
                           roadmap_count=roadmap_count,
                           recent_tasks=recent_tasks,
                           overall_percent=overall_percent)


# -------- TASKS --------
@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    if not login_required():
        return redirect(url_for("login"))

    uid = session["user_id"]

    if request.method == "POST":
        tdate = request.form["date"]
        task_text = request.form["task"].strip()

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO tasks(user_id, task_date, task, done) VALUES(?,?,?,0)",
                    (uid, tdate, task_text))
        conn.commit()
        conn.close()

        flash("✅ Task added!", "success")
        return redirect(url_for("tasks"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, task_date, task, done FROM tasks WHERE user_id=? ORDER BY task_date DESC, id DESC",
                (uid,))
    task_rows = cur.fetchall()

    # Today's tasks
    today = str(date.today())
    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND task_date=?", (uid, today))
    today_total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND task_date=? AND done=1", (uid, today))
    today_done = cur.fetchone()[0]

    conn.close()

    return render_template("tasks.html", tasks=task_rows, today_total=today_total, today_done=today_done)


@app.route("/task-toggle/<int:tid>")
def task_toggle(tid):
    if not login_required():
        return redirect(url_for("login"))

    uid = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT done FROM tasks WHERE id=? AND user_id=?", (tid, uid))
    row = cur.fetchone()

    if row:
        new_val = 0 if row[0] == 1 else 1
        cur.execute("UPDATE tasks SET done=? WHERE id=? AND user_id=?", (new_val, tid, uid))
        conn.commit()

    conn.close()
    return redirect(url_for("tasks"))


@app.route("/task-delete/<int:tid>")
def task_delete(tid):
    if not login_required():
        return redirect(url_for("login"))

    uid = session["user_id"]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (tid, uid))
    conn.commit()
    conn.close()

    flash("🗑 Task deleted", "success")
    return redirect(url_for("tasks"))


# -------- ROADMAPS --------
@app.route("/roadmaps")
def roadmaps():
    if not login_required():
        return redirect(url_for("login"))

    uid = session["user_id"]
    active_name = request.args.get("name")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT roadmap_name FROM roadmap_items WHERE user_id=? ORDER BY roadmap_name",
                (uid,))
    names = [r[0] for r in cur.fetchall()]

    if not active_name and names:
        active_name = names[0]

    items = []
    if active_name:
        cur.execute("""
            SELECT id, roadmap_name, goal, week, topic, status
            FROM roadmap_items
            WHERE user_id=? AND roadmap_name=?
            ORDER BY goal, week
        """, (uid, active_name))
        items = cur.fetchall()

    # progress for active roadmap
    cur.execute("SELECT COUNT(*) FROM roadmap_items WHERE user_id=? AND roadmap_name=?", (uid, active_name))
    total_active = cur.fetchone()[0] if active_name else 0
    cur.execute("SELECT COUNT(*) FROM roadmap_items WHERE user_id=? AND roadmap_name=? AND status='Done'", (uid, active_name))
    done_active = cur.fetchone()[0] if active_name else 0
    percent_active = int((done_active / total_active) * 100) if total_active > 0 else 0

    conn.close()

    return render_template("roadmap_view.html",
                           roadmap_names=names,
                           active_name=active_name,
                           items=items,
                           total_active=total_active,
                           done_active=done_active,
                           percent_active=percent_active)


@app.route("/roadmap/create", methods=["GET", "POST"])
def roadmap_create():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        uid = session["user_id"]
        roadmap_name = request.form["roadmap_name"].strip()
        goals = request.form.getlist("goals")

        if not roadmap_name:
            flash("⚠ Please enter roadmap name!", "danger")
            return redirect(url_for("roadmap_create"))

        if len(goals) == 0:
            flash("⚠ Please select at least one goal!", "danger")
            return redirect(url_for("roadmap_create"))

        conn = get_db()
        cur = conn.cursor()

        for goal in goals:
            topics = generate_roadmap(goal)
            for w, topic in enumerate(topics, start=1):
                cur.execute("""
                    INSERT INTO roadmap_items(user_id, roadmap_name, goal, week, topic, status)
                    VALUES(?,?,?,?,?,?)
                """, (uid, roadmap_name, goal, w, topic, "Pending"))

        conn.commit()
        conn.close()

        flash("✅ Roadmap created successfully!", "success")
        return redirect(url_for("roadmaps"))

    return render_template("roadmap_create.html", goals=get_goals_list())


@app.route("/roadmap/done/<int:item_id>")
def roadmap_done(item_id):
    if not login_required():
        return redirect(url_for("login"))

    uid = session["user_id"]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE roadmap_items SET status='Done' WHERE id=? AND user_id=?", (item_id, uid))
    conn.commit()
    conn.close()

    return redirect(url_for("roadmaps"))


@app.route("/roadmap/delete/<roadmap_name>")
def roadmap_delete(roadmap_name):
    if not login_required():
        return redirect(url_for("login"))

    uid = session["user_id"]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM roadmap_items WHERE user_id=? AND roadmap_name=?", (uid, roadmap_name))
    conn.commit()
    conn.close()

    flash("🗑 Roadmap deleted successfully!", "success")
    return redirect(url_for("roadmaps"))


@app.route("/roadmap/export/<roadmap_name>")
def roadmap_export_csv(roadmap_name):
    if not login_required():
        return redirect(url_for("login"))

    uid = session["user_id"]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT roadmap_name, goal, week, topic, status
        FROM roadmap_items
        WHERE user_id=? AND roadmap_name=?
        ORDER BY goal, week
    """, (uid, roadmap_name))
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Roadmap Name", "Goal", "Week", "Topic", "Status"])
    for r in rows:
        writer.writerow(r)

    mem = io.BytesIO()
    mem.write(output.getvalue().encode("utf-8"))
    mem.seek(0)
    output.close()

    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=f"{roadmap_name}_roadmap.csv")


# -------- PROGRESS --------
@app.route("/progress")
def progress():
    if not login_required():
        return redirect(url_for("login"))

    uid = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    # Task progress
    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id=?", (uid,))
    total_tasks = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND done=1", (uid,))
    done_tasks = cur.fetchone()[0]
    task_percent = int((done_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    # Roadmap progress
    cur.execute("SELECT COUNT(*) FROM roadmap_items WHERE user_id=?", (uid,))
    total_items = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM roadmap_items WHERE user_id=? AND status='Done'", (uid,))
    done_items = cur.fetchone()[0]
    roadmap_percent = int((done_items / total_items) * 100) if total_items > 0 else 0

    # Overall
    total_all = total_tasks + total_items
    done_all = done_tasks + done_items
    overall_percent = int((done_all / total_all) * 100) if total_all > 0 else 0

    conn.close()

    return render_template("progress.html",
                           total_tasks=total_tasks, done_tasks=done_tasks, task_percent=task_percent,
                           total_items=total_items, done_items=done_items, roadmap_percent=roadmap_percent,
                           overall_percent=overall_percent)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

