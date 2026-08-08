from flask import Flask, render_template, request, session, redirect 
import sqlite3

app = Flask(__name__)
app.secret_key = "trekking_secret_key"

def login_required():
    if "user_id" not in session:
        return False
    return True

conn = sqlite3.connect("trekking.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS bookings")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    trek_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT,
    email TEXT,
    password TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS treks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trek_name TEXT,
    location TEXT,
    duration TEXT,
    difficulty TEXT,
    price INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    trek_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")

cursor.execute("""
INSERT OR IGNORE INTO admins (id, username, password)
VALUES (1, 'admin', 'admin123')
""")

cursor.execute("SELECT * FROM admins")
print("Admins:", cursor.fetchall())


conn.commit()
conn.close()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        print("Full Name:", fullname)
        print("Email:", email)
        print("Password:", password)
        print("Confirm Password:", confirm_password)
        conn = sqlite3.connect("trekking.db")

        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (fullname, email, password) VALUES (?, ?, ?)",
            (fullname, email, password)
        )

        conn.commit()
        conn.close()

        print("Data Saved Successfully!")


    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("trekking.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session["user_id"] = user[0]
            session["user_name"] = user[1]

            return render_template("dashboard.html", name=user[1])
        
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        print("Admin Username:", username)
        print("Admin Password:", password)

        conn = sqlite3.connect("trekking.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM admins WHERE username=? AND password=?",
            (username, password)
        )

        admin = cursor.fetchone()
        print("Admin Found:", admin)

        conn.close()

        if admin:
            session["admin_id"] = admin[0]
            session["admin_username"] = admin[1]

            return redirect("/admin/dashboard")

        else:
            return "Invalid Admin Username or Password"

    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect("/admin/login")

    return render_template("admin_dashboard.html")

@app.route("/admin/treks")
def admin_treks():

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM treks")
    trek_data = cursor.fetchall()

    conn.close()

    return render_template("admin_treks.html", treks=trek_data)

@app.route("/admin/add_trek", methods=["GET", "POST"])
def admin_add_trek():

    if "admin_id" not in session:
        return redirect("/admin/login")

    if request.method == "POST":

        trek_name = request.form["trek_name"]
        location = request.form["location"]
        duration = request.form["duration"]
        difficulty = request.form["difficulty"]
        price = request.form["price"]

        conn = sqlite3.connect("trekking.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO treks
            (trek_name, location, duration, difficulty, price)
            VALUES (?, ?, ?, ?, ?)
        """, (trek_name, location, duration, difficulty, price))

        conn.commit()
        conn.close()

        return redirect("/admin/treks")

    return render_template("admin_add_trek.html")

@app.route("/admin/edit_trek/<int:trek_id>", methods=["GET", "POST"])
def admin_edit_trek(trek_id):

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    if request.method == "POST":

        trek_name = request.form["trek_name"]
        location = request.form["location"]
        duration = request.form["duration"]
        difficulty = request.form["difficulty"]
        price = request.form["price"]

        cursor.execute("""
            UPDATE treks
            SET trek_name=?, location=?, duration=?, difficulty=?, price=?
            WHERE id=?
        """, (trek_name, location, duration, difficulty, price, trek_id))

        conn.commit()
        conn.close()

        return redirect("/admin/treks")

    cursor.execute("SELECT * FROM treks WHERE id=?", (trek_id,))
    trek = cursor.fetchone()

    conn.close()

    return render_template("admin_edit_trek.html", trek=trek)

@app.route("/admin/delete_trek/<int:trek_id>")
def admin_delete_trek(trek_id):

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM treks WHERE id=?", (trek_id,))

    conn.commit()
    conn.close()

    return redirect("/admin/treks")

@app.route("/treks")
def treks():

    if not login_required():
        return redirect("/login")
    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM treks")

    trek_data = cursor.fetchall()

    conn.close()

    return render_template("treks.html", treks=trek_data)

@app.route("/my_bookings")
def my_bookings():

    if not login_required():
        return redirect("/login")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    user_id = session.get("user_id")

    cursor.execute("""
    SELECT treks.trek_name,
       treks.location,
       treks.duration,
       treks.difficulty,
       treks.price
    FROM bookings
    JOIN treks
    ON bookings.trek_id = treks.id
    WHERE bookings.user_id = ?
    """, (user_id,))

    booking_data = cursor.fetchall()

    conn.close()

    return render_template("my_bookings.html", bookings=booking_data)

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

@app.route("/add_trek", methods=["GET", "POST"])
def add_trek():

    if request.method == "POST":

        trek_name = request.form["trek_name"]
        location = request.form["location"]
        duration = request.form["duration"]
        difficulty = request.form["difficulty"]
        price = request.form["price"]

        conn = sqlite3.connect("trekking.db")
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO treks 
            (trek_name, location, duration, difficulty, price)
            VALUES (?, ?, ?, ?, ?)""",
            (trek_name, location, duration, difficulty, price)
        )

        conn.commit()
        conn.close()

        return "Trek Added Successfully!"

    return render_template("add_trek.html")

@app.route("/book/<int:trek_id>")
def book(trek_id):

    user_id = session.get("user_id")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trek_id INTEGER
    )
    """)

    cursor.execute(
    "INSERT INTO bookings (user_id, trek_id) VALUES (?, ?)",
    (user_id, trek_id)
)

    conn.commit()
    conn.close()

    return "Trek Booked Successfully!"

if __name__ == "__main__":
    app.run(debug=True)