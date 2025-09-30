from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------- DB Helper ----------
def get_db_connection():
    conn = sqlite3.connect("game.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- Home ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

# ---------- Register ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    import re
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        errors = []
        if len(username) < 5: errors.append("Username must be at least 5 characters.")
        if not re.search(r"[A-Z]", username): errors.append("Username must have uppercase.")
        if not re.search(r"[a-z]", username): errors.append("Username must have lowercase.")
        if re.search(r"[^A-Za-z]", username): errors.append("Username must be letters only.")
        if len(password) < 5: errors.append("Password at least 5 chars.")
        if not re.search(r"[A-Za-z]", password): errors.append("Password must have letter.")
        if not re.search(r"\d", password): errors.append("Password must have number.")
        if not re.search(r"[$%*@]", password): errors.append("Password must have special char $%*@.")

        if errors:
            for err in errors: flash(err)
            return redirect(url_for("register"))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, role, reg_date, win_status) VALUES (?, ?, ?, ?, ?)",
                (username, password, "PLAYER", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "No")
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Username already exists!")
            return redirect(url_for("register"))
        finally:
            conn.close()

        flash("Registered successfully! Please login.")
        return redirect(url_for("player_page"))

    return render_template("register.html")

# ---------- Player ----------
@app.route("/player", methods=["GET"])
def player_page():
    return render_template("player.html")

@app.route("/player/login", methods=["POST"])
def player_login():
    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=? AND role='PLAYER'",
        (username, password)
    )
    player = cursor.fetchone()

    if not player:
        conn.close()
        flash("Invalid credentials!")
        return redirect(url_for("player_page"))

    session['player'] = username
    last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE users SET last_login=? WHERE username=?", (last_login, username))
    conn.commit()

    # ---------- Daily limit check ----------
    today = date.today().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM user_guesses WHERE username=? AND date=?", (username, today))
    words_today = cursor.fetchone()[0]

    if words_today >= 3:
        conn.close()
        return render_template("game.html",
                               username=username,
                               message="⚠️ Daily limit reached. Come back tomorrow!",
                               attempts=0,
                               history=[],
                               game_over=True,
                               daily_limit_reached=True)

    # ---------- Start new game ----------
    cursor.execute("SELECT * FROM words ORDER BY RANDOM() LIMIT 1")
    word_row = cursor.fetchone()
    conn.close()

    session["word"] = word_row["word"].upper()
    session["attempts"] = 0
    session["history"] = []

    return redirect(url_for('game_page'))


# ---------- Player Game ----------
@app.route("/player/game", methods=["GET"])
def game_page():
    if 'player' not in session:
        return redirect(url_for('player_page'))

    username = session['player']
    conn = get_db_connection()
    today = datetime.now().strftime("%Y-%m-%d")

    # Count words tried today
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as count FROM user_guesses 
        WHERE username=? AND date=?
    """, (username, today))
    words_today = cursor.fetchone()["count"]
    conn.close()

    history = session.get("history", [])
    attempts = session.get("attempts", 0)
    message = ""
    game_over = False
    daily_limit_reached = False

    if words_today >= 3:
        message = "⚠️ Daily limit reached. Come back tomorrow!"
        game_over = True
        daily_limit_reached = True
        # Clear any session game data
        session.pop("word", None)
        session.pop("attempts", None)
        session.pop("history", None)
    else:
        # Check if the current game exceeded max attempts
        if attempts >= 5:
            secret_word = session.get("word", "")
            message = f"❌ Better luck next time! The word was {secret_word}"
            game_over = True

    return render_template("game.html",
                           username=username,
                           history=history,
                           attempts=attempts,
                           message=message,
                           game_over=game_over,
                           daily_limit_reached=daily_limit_reached)


@app.route("/player/guess", methods=["POST"])
def guess_word():
    if 'player' not in session or "word" not in session:
        return jsonify({"error": "Session expired"}), 403

    guess = request.form.get("guess", "").upper()
    secret = session["word"]
    attempts = session.get("attempts", 0) + 1
    session["attempts"] = attempts
    history = session.get("history", [])

    feedback = []
    for i in range(len(secret)):
        if i < len(guess):
            if guess[i] == secret[i]:
                feedback.append("Green")
            elif guess[i] in secret:
                feedback.append("Orange")
            else:
                feedback.append("Grey")
        else:
            feedback.append("Grey")

    history.append({"guess": guess, "feedback": feedback})
    session["history"] = history

    game_over = False
    if guess == secret:
        message = "🎉 Congrats! You guessed it!"
        game_over = True

        conn = get_db_connection()
        conn.execute("UPDATE users SET win_status='Yes' WHERE username=?", (session['player'],))
        conn.commit()
        conn.close()
    elif attempts >= 5:
        message = f"❌ Better luck next time! The word was {secret}"
        game_over = True
    else:
        message = f"Attempt {attempts}/5"

    # Save guess to DB if game over
    if game_over:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO user_guesses (username, word, guesses, correct, date) VALUES (?, ?, ?, ?, ?)",
            (session['player'], secret, attempts, int(guess == secret), date.today().strftime("%Y-%m-%d"))
        )
        conn.commit()
        conn.close()

    return jsonify({
        "guess": guess,
        "feedback": feedback,
        "attempts": attempts,
        "message": message,
        "game_over": game_over
    })

    # Inside guess_word() after processing the guess
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO user_guesses (username, word, guessed_word, date) VALUES (?, ?, ?, ?)
    """, (session['player'], session['word'], guess, today))
    conn.commit()
    conn.close()


@app.route("/player/logout")
def player_logout():
    session.pop('player', None)
    session.pop('word', None)
    session.pop('attempts', None)
    session.pop('history', None)
    return redirect(url_for('player_page'))

# ---------- Admin ----------
@app.route("/admin", methods=["GET"])
def admin_page():
    return render_template("admin.html")

@app.route("/admin/login", methods=["POST"])
def admin_login():
    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=? AND role='ADMIN'",
        (username, password)
    )
    admin = cursor.fetchone()
    conn.close()

    if admin:
        session['admin'] = username
        return redirect(url_for('admin_dashboard'))
    else:
        flash("Invalid credentials! Try again.")
        return redirect(url_for("admin_page"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_page'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE role='PLAYER'")
    players = cursor.fetchall()

    cursor.execute("SELECT * FROM users WHERE role='PLAYER' AND last_login IS NOT NULL")
    logged_in_players = cursor.fetchall()

    cursor.execute("SELECT * FROM words")
    words = cursor.fetchall()

    conn.close()

    return render_template("admin_dashboard.html",
                           admin=session['admin'],
                           players=players,
                           logged_in_players=logged_in_players,
                           words=words)

@app.route("/admin/logout")
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_page'))

@app.route("/admin/add_word", methods=["POST"])
def add_word():
    if 'admin' not in session:
        return redirect(url_for('admin_page'))

    word = request.form['word'].upper()
    added_by = session['admin']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO words (word, added_by) VALUES (?, ?)", (word, added_by))
        conn.commit()
    except sqlite3.IntegrityError:
        flash("Word already exists!")
    finally:
        conn.close()

    return redirect(url_for('admin_dashboard'))

@app.route("/admin/delete_word/<int:word_id>")
def delete_word(word_id):
    if 'admin' not in session:
        return redirect(url_for('admin_page'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM words WHERE id=?", (word_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))

# ---------- Ensure default admin exists ----------
def create_default_admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE role='ADMIN'")
    admin = cursor.fetchone()
    if not admin:
        cursor.execute("INSERT INTO users (username, password, role, reg_date, win_status) VALUES (?, ?, ?, ?, ?)",
                       ("admin", "admin123", "ADMIN", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "N/A"))
        conn.commit()
    conn.close()


@app.template_filter('zip')
def zip_lists(a, b):
    return zip(a, b)


if __name__ == "__main__":
    create_default_admin()
    app.run(debug=True)

@app.route("/player/new_game")
def new_game():
    if 'player' not in session:
        return redirect(url_for('player_page'))

    username = session['player']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Daily limit check
    today = date.today().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM user_guesses WHERE username=? AND date=?", (username, today))
    words_today = cursor.fetchone()[0]

    if words_today >= 3:
        conn.close()
        return render_template("game.html",
                               username=username,
                               message="⚠️ Daily limit reached. Come back tomorrow!",
                               attempts=0,
                               history=[],
                               game_over=True,
                               daily_limit_reached=True)

    # Start new game
    cursor.execute("SELECT * FROM words ORDER BY RANDOM() LIMIT 1")
    word_row = cursor.fetchone()
    conn.close()

    session["word"] = word_row["word"].upper()
    session["attempts"] = 0
    session["history"] = []

    return redirect(url_for('game_page'))


@app.route("/player/new_game")
def new_game():
    if 'player' not in session:
        return redirect(url_for('player_page'))

    username = session['player']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Daily limit check
    today = date.today().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM user_guesses WHERE username=? AND date=?", (username, today))
    words_today = cursor.fetchone()[0]

    if words_today >= 3:
        conn.close()
        return render_template("game.html",
                               username=username,
                               message="⚠️ Daily limit reached. Come back tomorrow!",
                               attempts=0,
                               history=[],
                               game_over=True,
                               daily_limit_reached=True)

    # Start new game
    cursor.execute("SELECT * FROM words ORDER BY RANDOM() LIMIT 1")
    word_row = cursor.fetchone()
    conn.close()

    session["word"] = word_row["word"].upper()
    session["attempts"] = 0
    session["history"] = []

    return redirect(url_for('game_page'))


@app.route('/game', methods=['GET', 'POST'])
def game_page():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    today = date.today().isoformat()

    # Count words played today
    cursor.execute("SELECT COUNT(*) FROM user_guesses WHERE username=? AND date=?", (username, today))
    words_today = cursor.fetchone()[0]

    if words_today >= 3:
        return render_template("game.html",
                               username=username,
                               message="⚠️ Daily limit reached. Come back tomorrow!",
                               attempts=0,
                               history=[],
                               game_over=True,
                               daily_limit_reached=True)

    # Get current word and attempts from session
    if 'current_word' not in session or session.get('new_game'):
        session['current_word'] = get_random_word()
        session['attempts'] = 0
        session['new_game'] = False

    current_word = session['current_word']
    attempts = session.get('attempts', 0)
    message = ""

    return render_template("game.html",
                           username=username,
                           message=message,
                           attempts=attempts,
                           history=[],
                           game_over=False,
                           daily_limit_reached=False)


# ===================== GAME RESULT HANDLER =====================
def end_game(username, message, attempts, history):
    conn = sqlite3.connect("game.db")
    cursor = conn.cursor()

    # Count how many games user has played today
    cursor.execute("SELECT COUNT(DISTINCT word) FROM guesses WHERE username=? AND date=date('now')", (username,))
    today_count = cursor.fetchone()[0]
    conn.close()

    # Daily limit flag
    daily_limit_reached = today_count >= 3

    return render_template("game.html",
                           username=username,
                           history=history,
                           message=message,
                           attempts=attempts,
                           game_over=True,
                           daily_limit_reached=daily_limit_reached)
