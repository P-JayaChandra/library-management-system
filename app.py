from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "library_secret"

# ---------------- DATABASE ----------------

def init_db():

    conn = sqlite3.connect("library.db")
    c = conn.cursor()

    # Students

    c.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        roll TEXT UNIQUE,
        branch TEXT,
        year TEXT,
        password TEXT
    )
    """)

    # Books

    c.execute("""
    CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_name TEXT,
        author TEXT,
        quantity INTEGER
    )
    """)

    # Issued Books

    c.execute("""
    CREATE TABLE IF NOT EXISTS issued_books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll TEXT,
        book_id INTEGER,
        book_name TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")

# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        conn = sqlite3.connect("library.db")
        c = conn.cursor()

        try:

            c.execute(
                """
                INSERT INTO students
                (name, roll, branch, year, password)
                VALUES (?,?,?,?,?)
                """,
                (
                    request.form["name"],
                    request.form["roll"],
                    request.form["branch"],
                    request.form["year"],
                    request.form["password"]
                )
            )

            conn.commit()

        except:
            return "Roll Number Already Exists"

        conn.close()

        return redirect("/")

    return render_template("register.html")

# ---------------- STUDENT LOGIN ----------------

@app.route("/login", methods=["POST"])
def login():

    roll = request.form["roll"]
    password = request.form["password"]

    conn = sqlite3.connect("library.db")
    c = conn.cursor()

    c.execute(
        """
        SELECT * FROM students
        WHERE roll=? AND password=?
        """,
        (roll, password)
    )

    user = c.fetchone()

    conn.close()

    if user:

        session["student"] = roll

        return redirect("/student")

    return "Invalid Login"

# ---------------- STUDENT DASHBOARD ----------------

@app.route("/student")
def student():

    if "student" not in session:
        return redirect("/")

    conn = sqlite3.connect("library.db")
    c = conn.cursor()

    search = request.args.get("search")

    if search:

        c.execute(
            """
            SELECT * FROM books
            WHERE book_name LIKE ?
            """,
            ('%' + search + '%',)
        )

    else:

        c.execute("SELECT * FROM books")

    books = c.fetchall()

    c.execute(
        """
        SELECT * FROM issued_books
        WHERE roll=?
        """,
        (session["student"],)
    )

    my_books = c.fetchall()

    conn.close()

    return render_template(
        "student_dashboard.html",
        books=books,
        my_books=my_books
    )
# ---------------- ISSUE BOOK ----------------

@app.route("/issue-book/<int:id>")
def issue_book(id):

    if "student" not in session:
        return redirect("/")

    conn = sqlite3.connect("library.db")
    c = conn.cursor()

    c.execute(
        "SELECT book_name, quantity FROM books WHERE id=?",
        (id,)
    )

    book = c.fetchone()

    if book and book[1] > 0:

        c.execute(
            """
            INSERT INTO issued_books
            (roll, book_id, book_name)
            VALUES (?,?,?)
            """,
            (
                session["student"],
                id,
                book[0]
            )
        )

        c.execute(
            """
            UPDATE books
            SET quantity = quantity - 1
            WHERE id=?
            """,
            (id,)
        )

        conn.commit()

    conn.close()

    return redirect("/student")

# ---------------- ADMIN LOGIN ----------------

ADMIN_USER = "admin"
ADMIN_PASS = "12345"

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if (
            username == ADMIN_USER
            and
            password == ADMIN_PASS
        ):

            session["admin"] = True

            return redirect("/admin")

        return "Invalid Admin Login"

    return render_template("admin_login.html")

# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/admin-login")

    conn = sqlite3.connect("library.db")
    c = conn.cursor()

    c.execute("SELECT * FROM books")
    books = c.fetchall()

    c.execute("SELECT * FROM issued_books")
    issued = c.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        books=books,
        issued=issued
    )

# ---------------- ADD BOOK ----------------

@app.route("/add-book", methods=["POST"])
def add_book():

    if not session.get("admin"):
        return redirect("/admin-login")

    conn = sqlite3.connect("library.db")
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO books
        (book_name, author, quantity)
        VALUES (?,?,?)
        """,
        (
            request.form["book_name"],
            request.form["author"],
            request.form["quantity"]
        )
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

# ---------------- DELETE BOOK ----------------

@app.route("/delete-book/<int:id>")
def delete_book(id):

    if not session.get("admin"):
        return redirect("/admin-login")

    conn = sqlite3.connect("library.db")
    c = conn.cursor()

    c.execute(
        "DELETE FROM books WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

# ---------------- RETURN BOOK ----------------

@app.route("/return-book/<int:id>")
def return_book(id):

    if not session.get("admin"):
        return redirect("/admin-login")

    conn = sqlite3.connect("library.db")
    c = conn.cursor()

    c.execute(
        """
        SELECT book_id
        FROM issued_books
        WHERE id=?
        """,
        (id,)
    )

    record = c.fetchone()

    if record:

        book_id = record[0]

        c.execute(
            """
            UPDATE books
            SET quantity = quantity + 1
            WHERE id=?
            """,
            (book_id,)
        )

        c.execute(
            """
            DELETE FROM issued_books
            WHERE id=?
            """,
            (id,)
        )

        conn.commit()

    conn.close()

    return redirect("/admin")

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# ---------------- RUN APP ----------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )