from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, os, uuid
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "outpass_secret_key_2024"

DATA_FILE = "outpass_data.json"
USERS_FILE = "users.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# default built-in users
BASE_USERS = {
    "student1": {"password": "pass123", "role": "student"},
    "student2": {"password": "pass456", "role": "student"},
    "admin":    {"password": "admin123", "role": "admin"},
}

# signed-up users loaded from file
EXTRA_USERS = load_users()

def get_all_users():
    return {**BASE_USERS, **EXTRA_USERS}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Admin access only.", "error")
            return redirect(url_for("outpass"))
        return f(*args, **kwargs)
    return decorated

@app.route("/")
def index():
    if "username" in session:
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("outpass"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        all_users = get_all_users()
        if username in all_users and all_users[username]["password"] == password:
            session["username"] = username
            session["role"] = all_users[username]["role"]
            flash(f"Welcome back, {username}! 🎉", "success")
            if all_users[username]["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("outpass"))
        else:
            flash("Invalid username or password. Try again.", "error")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm  = request.form.get("confirm", "").strip()

        all_users = get_all_users()

        if not username or not password:
            flash("Username மற்றும் Password தேவை.", "error")
            return redirect(url_for("signup"))
        if username in all_users:
            flash("இந்த username already இருக்கு. வேற username try பண்ணு.", "error")
            return redirect(url_for("signup"))
        if password != confirm:
            flash("Password match ஆகலை.", "error")
            return redirect(url_for("signup"))

        EXTRA_USERS[username] = {"password": password, "role": "student"}
        save_users(EXTRA_USERS)
        flash("Account create ஆச்சு! இப்போ login பண்ணு 🎉", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/outpass")
@login_required
def outpass():
    all_records = load_data()
    user_records = [r for r in all_records if r["username"] == session["username"]]
    return render_template("outpass.html", records=user_records)

@app.route("/apply", methods=["POST"])
@login_required
def apply():
    data = load_data()
    new_record = {
        "id":            str(uuid.uuid4())[:8],
        "username":      session["username"],
        "name":          request.form.get("name", "").strip(),
        "roll_number":   request.form.get("roll_number", "").strip(),
        "department":    request.form.get("department", "").strip(),
        "year":          request.form.get("year", "").strip(),
        "phone":         request.form.get("phone", "").strip(),
        "parent_phone":  request.form.get("parent_phone", "").strip(),
        "date_out":      request.form.get("date_out", "").strip(),
        "time_out":      request.form.get("time_out", "").strip(),
        "date_return":   request.form.get("date_return", "").strip(),
        "time_return":   request.form.get("time_return", "").strip(),
        "destination":   request.form.get("destination", "").strip(),
        "place_type":    request.form.get("place_type", "").strip(),
        "reason":        request.form.get("reason", "").strip(),
        "guardian_name": request.form.get("guardian_name", "").strip(),
        "status":        "pending",
        "applied_at":    datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    required = ["name", "roll_number", "department", "year", "phone",
                "date_out", "time_out", "date_return", "time_return",
                "destination", "reason"]
    for field in required:
        if not new_record[field]:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("outpass"))
    data.append(new_record)
    save_data(data)
    flash("✅ OutPass request submitted! Awaiting admin approval.", "success")
    return redirect(url_for("outpass"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    records = load_data()
    return render_template("admin.html", records=records)

@app.route("/admin/approve/<record_id>")
@admin_required
def approve(record_id):
    data = load_data()
    for r in data:
        if r["id"] == record_id:
            r["status"] = "approved"
            r["reviewed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            break
    save_data(data)
    flash(f"OutPass {record_id} approved ✅", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/reject/<record_id>")
@admin_required
def reject(record_id):
    data = load_data()
    for r in data:
        if r["id"] == record_id:
            r["status"] = "rejected"
            r["reviewed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            break
    save_data(data)
    flash(f"OutPass {record_id} rejected ❌", "error")
    return redirect(url_for("admin_dashboard"))

@app.route("/logout")
def logout():
    username = session.get("username", "")
    session.clear()
    flash(f"Goodbye {username}! Logged out 👋", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    print("\n🎓 OutPass System Starting...")
    print("=" * 40)
    print("🌐 http://127.0.0.1:5000")
    print("👤 student1 / pass123")
    print("🛡️  admin   / admin123")
    print("=" * 40 + "\n")
    app.run(debug=True)