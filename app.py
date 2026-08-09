from flask import Flask, render_template, request, session, redirect, flash

import sqlite3

app = Flask(__name__)
app.secret_key = "trekking_secret_key"

def login_required():
    if "user_id" not in session:
        return False
    return True

conn = sqlite3.connect("trekking.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    trek_id INTEGER
)
""")
try:
    cursor.execute(
        "ALTER TABLE bookings ADD COLUMN status TEXT DEFAULT 'Pending'"
    )
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE bookings ADD COLUMN booking_date TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE bookings ADD COLUMN status TEXT DEFAULT 'Booked'")
except sqlite3.OperationalError:
    pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT,
    email TEXT,
    password TEXT
)
""")
try:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN blacklisted INTEGER DEFAULT 0"
    )
except sqlite3.OperationalError:
    pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT,
    email TEXT,
    password TEXT,
    approved INTEGER DEFAULT 0,
    blacklisted INTEGER DEFAULT 0
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
try:
    cursor.execute("ALTER TABLE treks ADD COLUMN available_slots INTEGER DEFAULT 0")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE treks ADD COLUMN status TEXT DEFAULT 'Open'")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE treks ADD COLUMN start_date TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE treks ADD COLUMN end_date TEXT")
except sqlite3.OperationalError:
    pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS trek_staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id INTEGER,
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

        return redirect("/login")


    return render_template("register.html")

@app.route("/staff/register", methods=["GET", "POST"])
def staff_register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("trekking.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO staff
            (fullname, email, password)
            VALUES (?, ?, ?)
        """, (fullname, email, password))

        conn.commit()
        conn.close()

        flash("Staff registration successful! Wait for admin approval.")

        return redirect("/staff/login")

    return render_template("staff_register.html")

@app.route("/staff/login", methods=["GET", "POST"])
def staff_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("trekking.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, fullname, email, password, approved, blacklisted
            FROM staff
            WHERE email = ? AND password = ?
        """, (email, password))

        staff = cursor.fetchone()

        conn.close()

        if not staff:
            return "Invalid Email or Password"

        if staff[5] == 1:
            return "Your staff account has been blacklisted."

        if staff[4] == 0:
            return "Your account is waiting for admin approval."

        session["staff_id"] = staff[0]
        session["staff_name"] = staff[1]

        return redirect("/staff/dashboard")

    return render_template("staff_login.html")

@app.route("/staff/dashboard")
def staff_dashboard():

    if "staff_id" not in session:
        return redirect("/staff/login")

    return render_template(
        "staff_dashboard.html",
        name=session["staff_name"]
    )

@app.route("/staff/logout")
def staff_logout():

    session.pop("staff_id", None)
    session.pop("staff_name", None)

    return redirect("/staff/login")

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

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        name=session["user_name"]
    )

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute("""
            UPDATE users
            SET fullname = ?, email = ?, password = ?
            WHERE id = ?
        """, (fullname, email, password, user_id))

        conn.commit()

        session["user_name"] = fullname

        conn.close()

        flash("Profile updated successfully!")

        return redirect("/profile")

    cursor.execute("""
        SELECT fullname, email, password
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )

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

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM treks")
    total_treks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM staff")
    total_staff = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings
    )

@app.route("/admin/treks")
def admin_treks():

    if "admin_id" not in session:
        return redirect("/admin/login")

    search = request.args.get("search", "")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM treks
            WHERE trek_name LIKE ?
               OR location LIKE ?
               OR difficulty LIKE ?
        """, (
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        ))
    else:
        cursor.execute("SELECT * FROM treks")

    trek_data = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_treks.html",
        treks=trek_data,
        search=search
    )

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
        available_slots = request.form["available_slots"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        conn = sqlite3.connect("trekking.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO treks
            (trek_name, location, duration, difficulty, price,
             available_slots, start_date, end_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trek_name,
            location,
            duration,
            difficulty,
            price,
            available_slots,
            start_date,
            end_date,
            "Open"
        ))

        conn.commit()
        conn.close()

        flash("Trek added successfully!")
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
        available_slots = request.form["available_slots"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        cursor.execute("""
            UPDATE treks
            SET trek_name=?,
                location=?,
                duration=?,
                difficulty=?,
                price=?,
                available_slots=?,
                start_date=?,
                end_date=?
            WHERE id=?
        """, (
            trek_name,
            location,
            duration,
            difficulty,
            price,
            available_slots,
            start_date,
            end_date,
            trek_id
        ))

        conn.commit()
        conn.close()

        flash("Trek updated successfully!")
        return redirect("/admin/treks")

    cursor.execute(
        "SELECT * FROM treks WHERE id=?",
        (trek_id,)
    )

    trek = cursor.fetchone()

    conn.close()

    return render_template(
        "admin_edit_trek.html",
        trek=trek
    )


@app.route("/admin/delete_trek/<int:trek_id>")
def admin_delete_trek(trek_id):

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM treks WHERE id=?",
        (trek_id,)
    )

    conn.commit()
    conn.close()

    flash("Trek deleted successfully!")
    return redirect("/admin/treks")

@app.route("/treks")
def treks():

    if not login_required():
        return redirect("/login")

    search = request.args.get("search", "")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM treks
            WHERE trek_name LIKE ?
               OR location LIKE ?
               OR difficulty LIKE ?
        """, (
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        ))
    else:
        cursor.execute("SELECT * FROM treks")

    trek_data = cursor.fetchall()

    conn.close()

    return render_template(
        "treks.html",
        treks=trek_data,
        search=search
    )

@app.route("/admin/users")
def admin_users():

    if "admin_id" not in session:
        return redirect("/admin/login")

    search = request.args.get("search", "")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT id, fullname, email, blacklisted
            FROM users
            WHERE fullname LIKE ?
               OR email LIKE ?
        """, (
            "%" + search + "%",
            "%" + search + "%"
        ))
    else:
        cursor.execute("""
            SELECT id, fullname, email, blacklisted
            FROM users
        """)

    users = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_users.html",
        users=users,
        search=search
    )


@app.route("/admin/staff")
def admin_staff():

    if "admin_id" not in session:
        return redirect("/admin/login")

    search = request.args.get("search", "")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT id, fullname, email, approved, blacklisted
            FROM staff
            WHERE fullname LIKE ?
               OR email LIKE ?
        """, (
            "%" + search + "%",
            "%" + search + "%"
        ))
    else:
        cursor.execute("""
            SELECT id, fullname, email, approved, blacklisted
            FROM staff
        """)

    staff = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_staff.html",
        staff=staff,
        search=search
    )

@app.route("/admin/assign_trek/<int:staff_id>", methods=["GET", "POST"])
def assign_trek(staff_id):

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    if request.method == "POST":

        trek_id = request.form["trek_id"]

        # Check if this trek is already assigned to this staff
        cursor.execute("""
            SELECT id
            FROM trek_staff
            WHERE staff_id = ? AND trek_id = ?
        """, (staff_id, trek_id))

        existing_assignment = cursor.fetchone()

        if existing_assignment:
            conn.close()
            flash("This trek is already assigned to this staff member.")
            return redirect("/admin/staff")

        cursor.execute("""
            INSERT INTO trek_staff (staff_id, trek_id)
            VALUES (?, ?)
        """, (staff_id, trek_id))

        conn.commit()
        conn.close()

        flash("Trek assigned to staff successfully!")

        return redirect("/admin/staff")

    cursor.execute("SELECT * FROM treks")
    treks = cursor.fetchall()

    cursor.execute("""
        SELECT id, fullname, email
        FROM staff
        WHERE id = ?
    """, (staff_id,))

    staff_member = cursor.fetchone()

    conn.close()

    return render_template(
        "assign_trek.html",
        treks=treks,
        staff=staff_member
    )

@app.route("/staff/assigned_treks")
def staff_assigned_treks():

    if "staff_id" not in session:
        return redirect("/staff/login")

    staff_id = session["staff_id"]

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            treks.id,
            treks.trek_name,
            treks.location,
            treks.duration,
            treks.difficulty,
            treks.price,
            treks.available_slots,
            treks.status,
            treks.start_date,
            treks.end_date
        FROM trek_staff
        JOIN treks
        ON trek_staff.trek_id = treks.id
        WHERE trek_staff.staff_id = ?
    """, (staff_id,))

    assigned_treks = cursor.fetchall()

    conn.close()

    return render_template(
        "staff_assigned_treks.html",
        treks=assigned_treks
    )

@app.route("/staff/participants/<int:trek_id>")
def staff_participants(trek_id):

    if "staff_id" not in session:
        return redirect("/staff/login")

    staff_id = session["staff_id"]

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    # Check whether this trek is assigned to this staff
    cursor.execute("""
        SELECT id
        FROM trek_staff
        WHERE staff_id = ? AND trek_id = ?
    """, (staff_id, trek_id))

    assigned = cursor.fetchone()

    if not assigned:
        conn.close()
        return "You are not assigned to this trek."

    # Get trek details
    cursor.execute("""
        SELECT id, trek_name
        FROM treks
        WHERE id = ?
    """, (trek_id,))

    trek = cursor.fetchone()

    # Get participants
    cursor.execute("""
        SELECT
            bookings.id,
            users.fullname,
            users.email,
            bookings.booking_date,
            bookings.status
        FROM bookings
        JOIN users
        ON bookings.user_id = users.id
        WHERE bookings.trek_id = ?
        ORDER BY bookings.id DESC
    """, (trek_id,))

    participants = cursor.fetchall()

    conn.close()

    return render_template(
        "staff_participants.html",
        trek=trek,
        participants=participants
    )

@app.route("/staff/update_slots/<int:trek_id>", methods=["GET", "POST"])
def staff_update_slots(trek_id):

    if "staff_id" not in session:
        return redirect("/staff/login")

    staff_id = session["staff_id"]

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    # Check if trek is assigned to this staff
    cursor.execute("""
        SELECT id
        FROM trek_staff
        WHERE staff_id = ? AND trek_id = ?
    """, (staff_id, trek_id))

    assigned = cursor.fetchone()

    if not assigned:
        conn.close()
        return "You are not assigned to this trek."

    if request.method == "POST":

        available_slots = request.form["available_slots"]

        cursor.execute("""
            UPDATE treks
            SET available_slots = ?
            WHERE id = ?
        """, (available_slots, trek_id))

        conn.commit()
        conn.close()

        flash("Available slots updated successfully!")

        return redirect("/staff/assigned_treks")

    cursor.execute("""
        SELECT trek_name, available_slots
        FROM treks
        WHERE id = ?
    """, (trek_id,))

    trek = cursor.fetchone()

    conn.close()

    return render_template(
        "staff_update_slots.html",
        trek=trek,
        trek_id=trek_id
    )

@app.route("/staff/update_status/<int:trek_id>", methods=["GET", "POST"])
def staff_update_status(trek_id):

    if "staff_id" not in session:
        return redirect("/staff/login")

    staff_id = session["staff_id"]

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    # Check if trek is assigned to this staff
    cursor.execute("""
        SELECT id
        FROM trek_staff
        WHERE staff_id = ? AND trek_id = ?
    """, (staff_id, trek_id))

    assigned = cursor.fetchone()

    if not assigned:
        conn.close()
        return "You are not assigned to this trek."

    if request.method == "POST":

        status = request.form["status"]

        cursor.execute("""
            UPDATE treks
            SET status = ?
            WHERE id = ?
        """, (status, trek_id))

        conn.commit()
        conn.close()

        flash("Trek status updated successfully!")

        return redirect("/staff/assigned_treks")

    cursor.execute("""
        SELECT trek_name, status
        FROM treks
        WHERE id = ?
    """, (trek_id,))

    trek = cursor.fetchone()

    conn.close()

    return render_template(
        "staff_update_status.html",
        trek=trek,
        trek_id=trek_id
    )

@app.route("/admin/approve_staff/<int:staff_id>")
def approve_staff(staff_id):

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE staff SET approved = 1 WHERE id = ?",
        (staff_id,)
    )

    conn.commit()
    conn.close()

    flash("Staff approved successfully!")

    return redirect("/admin/staff")


@app.route("/admin/blacklist_staff/<int:staff_id>")
def blacklist_staff(staff_id):

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE staff SET blacklisted = 1 WHERE id = ?",
        (staff_id,)
    )

    conn.commit()
    conn.close()

    flash("Staff blacklisted successfully!")

    return redirect("/admin/staff")

@app.route("/admin/blacklist_user/<int:user_id>")
def blacklist_user(user_id):

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET blacklisted = 1 WHERE id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    flash("User blacklisted successfully!")

    return redirect("/admin/users")

@app.route("/my_bookings")
def my_bookings():

    if not login_required():
        return redirect("/login")

    user_id = session.get("user_id")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            bookings.id,
            treks.trek_name,
            treks.location,
            treks.duration,
            treks.difficulty,
            treks.price,
            bookings.booking_date,
            bookings.status,
            treks.start_date,
            treks.end_date
        FROM bookings
        JOIN treks
        ON bookings.trek_id = treks.id
        WHERE bookings.user_id = ?
        ORDER BY bookings.booking_date DESC
    """, (user_id,))

    booking_data = cursor.fetchall()

    conn.close()

    return render_template(
        "my_bookings.html",
        bookings=booking_data
    )

@app.route("/admin/bookings")
def admin_bookings():

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            bookings.id,
            users.fullname,
            users.email,
            treks.trek_name,
            treks.location,
            treks.start_date,
            treks.end_date,
            bookings.booking_date,
            bookings.status
        FROM bookings
        JOIN users
        ON bookings.user_id = users.id
        JOIN treks
        ON bookings.trek_id = treks.id
        ORDER BY bookings.booking_date DESC
    """)

    bookings = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_bookings.html",
        bookings=bookings
    )

@app.route("/admin/update_booking_status/<int:booking_id>", methods=["POST"])
def admin_update_booking_status(booking_id):

    if "admin_id" not in session:
        return redirect("/admin/login")

    status = request.form["status"]

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE bookings
        SET status = ?
        WHERE id = ?
    """, (status, booking_id))

    conn.commit()
    conn.close()

    flash("Booking status updated successfully!")

    return redirect("/admin/bookings")

@app.route("/logout")
def logout():

    session.pop("user_id", None)
    session.pop("user_name", None)

    return redirect("/login")

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_id", None)
    session.pop("admin_username", None)

    return redirect("/admin/login")

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

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect("trekking.db")
    cursor = conn.cursor()

    # Get trek details
    cursor.execute("""
        SELECT id, trek_name, available_slots, status
        FROM treks
        WHERE id = ?
    """, (trek_id,))

    trek = cursor.fetchone()

    if not trek:
        conn.close()
        return "Trek not found"

    available_slots = trek[2]
    status = trek[3]

    # Trek must be Open
    if status != "Open":
        conn.close()
        return "This trek is currently closed for booking."

    # Check available slots
    if available_slots <= 0:
        conn.close()
        return "Sorry, no slots are available."

    # Check if user already booked this trek
    cursor.execute("""
        SELECT id
        FROM bookings
        WHERE user_id = ? AND trek_id = ? AND status = 'Booked'
    """, (user_id, trek_id))

    existing_booking = cursor.fetchone()

    if existing_booking:
        conn.close()
        return "You have already booked this trek."

    # Current date
    from datetime import date
    booking_date = date.today().isoformat()

    # Create booking
    cursor.execute("""
        INSERT INTO bookings
        (user_id, trek_id, booking_date, status)
        VALUES (?, ?, ?, ?)
    """, (user_id, trek_id, booking_date, "Booked"))

    # Reduce available slots
    cursor.execute("""
        UPDATE treks
        SET available_slots = available_slots - 1
        WHERE id = ?
    """, (trek_id,))

    conn.commit()
    conn.close()

    flash("Trek booked successfully!")
    return redirect("/my_bookings")

if __name__ == "__main__":
    app.run(debug=True)