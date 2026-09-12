import os
from datetime import date, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# FLASK APP
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

# Session security
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# For HTTPS production
if os.environ.get("FLASK_ENV") == "production":
    app.config["SESSION_COOKIE_SECURE"] = True


# During local development this is okay.
# Because frontend and backend will eventually use the same Flask server,
# CORS is not required for production.
CORS(app, supports_credentials=True)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_HOST = os.environ.get("POSTGRES_HOST")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_NAME = os.environ.get("POSTGRES_DB")
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD")


def get_db():
    """
    Create a PostgreSQL database connection.
    """

    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode=os.environ.get("POSTGRES_SSLMODE", "require")
    )

    return connection


# ============================================================
# FRONTEND ROUTES
# ============================================================

@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/index.html")
def index_page():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/login.html")
def login_page():
    return send_from_directory(FRONTEND_DIR, "login.html")


@app.route("/register.html")
def register_page():
    return send_from_directory(FRONTEND_DIR, "register.html")


@app.route("/dashboard.html")
def dashboard_page():
    return send_from_directory(FRONTEND_DIR, "dashboard.html")


# ============================================================
# DATABASE TEST
# ============================================================

@app.route("/api/test-db", methods=["GET"])
def test_database():

    try:
        connection = get_db()

        cursor = connection.cursor()

        cursor.execute("SELECT version();")

        result = cursor.fetchone()

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "message": "PostgreSQL connection successful!",
            "version": result[0],
            "database": DB_NAME
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Database connection failed",
            "error": str(error)
        }), 500


# ============================================================
# REGISTER
# ============================================================

@app.route("/api/register", methods=["POST"])
def register():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data received"
            }), 400

        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        # Validation
        if not username or not email or not password:
            return jsonify({
                "success": False,
                "message": "Username, email and password are required"
            }), 400

        if len(username) < 3:
            return jsonify({
                "success": False,
                "message": "Username must contain at least 3 characters"
            }), 400

        if len(password) < 6:
            return jsonify({
                "success": False,
                "message": "Password must contain at least 6 characters"
            }), 400

        connection = get_db()
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Check existing user
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE username = %s OR email = %s
            """,
            (username, email)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            connection.close()

            return jsonify({
                "success": False,
                "message": "Username or email already exists"
            }), 409

        # Secure password hash
        password_hash = generate_password_hash(password)

        # Create user
        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                email,
                password_hash,
                level,
                xp,
                coins,
                longest_streak,
                current_streak
            )
            VALUES
            (
                %s,
                %s,
                %s,
                1,
                0,
                100,
                0,
                0
            )
            RETURNING id, username, email, level, xp, coins
            """,
            (
                username,
                email,
                password_hash
            )
        )

        user = cursor.fetchone()

        # Create starting attributes
        cursor.execute(
            """
            INSERT INTO attributes
            (
                user_id,
                strength,
                intelligence,
                discipline,
                creativity,
                social
            )
            VALUES
            (
                %s,
                1,
                1,
                1,
                1,
                1
            )
            """,
            (user["id"],)
        )

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "message": "Registration successful!",
            "user": user
        }), 201

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Registration failed",
            "error": str(error)
        }), 500


# ============================================================
# LOGIN
# ============================================================

@app.route("/api/login", methods=["POST"])
def login():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data received"
            }), 400

        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username and password are required"
            }), 400

        connection = get_db()

        cursor = connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username = %s OR email = %s
            """,
            (username, username.lower())
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid username or password"
            }), 401

        if not check_password_hash(user["password_hash"], password):
            return jsonify({
                "success": False,
                "message": "Invalid username or password"
            }), 401

        # Store only user ID in session
        session["user_id"] = user["id"]

        return jsonify({
            "success": True,
            "message": "Login successful!",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "level": user["level"],
                "xp": user["xp"],
                "coins": user["coins"]
            }
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Login failed",
            "error": str(error)
        }), 500


# ============================================================
# LOGOUT
# ============================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    })


# ============================================================
# CURRENT USER
# ============================================================

@app.route("/api/me", methods=["GET"])
def current_user():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Not logged in"
        }), 401

    try:

        connection = get_db()

        cursor = connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT
                id,
                username,
                email,
                level,
                xp,
                coins,
                current_streak,
                longest_streak,
                last_streak_date
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if not user:
            session.clear()

            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        return jsonify({
            "success": True,
            "user": user
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not get user",
            "error": str(error)
        }), 500


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/api/dashboard", methods=["GET"])
def dashboard():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    try:

        connection = get_db()

        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # User information
        cursor.execute(
            """
            SELECT
                id,
                username,
                email,
                level,
                xp,
                coins,
                current_streak,
                longest_streak,
                last_streak_date
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            cursor.close()
            connection.close()

            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        # Attributes
        cursor.execute(
            """
            SELECT
                strength,
                intelligence,
                discipline,
                creativity,
                social
            FROM attributes
            WHERE user_id = %s
            """,
            (user_id,)
        )

        attributes = cursor.fetchone()

        # Total tasks
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM tasks
            WHERE user_id = %s
            """,
            (user_id,)
        )

        total_tasks = cursor.fetchone()["total"]

        # Completed tasks
        cursor.execute(
            """
            SELECT COUNT(*) AS completed
            FROM tasks
            WHERE user_id = %s
            AND completed = TRUE
            """,
            (user_id,)
        )

        completed_tasks = cursor.fetchone()["completed"]

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "user": user,
            "attributes": attributes,
            "stats": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks
            }
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not load dashboard",
            "error": str(error)
        }), 500


# ============================================================
# GET TASKS
# ============================================================

@app.route("/api/tasks", methods=["GET"])
def get_tasks():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    try:

        connection = get_db()

        cursor = connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT
                id,
                title,
                description,
                category,
                xp_reward,
                coin_reward,
                completed,
                created_at,
                completed_at
            FROM tasks
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )

        tasks = cursor.fetchall()

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "tasks": tasks
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not load tasks",
            "error": str(error)
        }), 500


# ============================================================
# CREATE TASK
# ============================================================

@app.route("/api/tasks", methods=["POST"])
def create_task():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No task data received"
            }), 400

        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        category = data.get("category", "General")

        xp_reward = int(data.get("xp_reward", 10))
        coin_reward = int(data.get("coin_reward", 5))

        if not title:
            return jsonify({
                "success": False,
                "message": "Task title is required"
            }), 400

        if len(title) > 100:
            return jsonify({
                "success": False,
                "message": "Task title is too long"
            }), 400

        if xp_reward < 1:
            xp_reward = 1

        if coin_reward < 0:
            coin_reward = 0

        connection = get_db()

        cursor = connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            INSERT INTO tasks
            (
                user_id,
                title,
                description,
                category,
                xp_reward,
                coin_reward
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING *
            """,
            (
                user_id,
                title,
                description,
                category,
                xp_reward,
                coin_reward
            )
        )

        task = cursor.fetchone()

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "message": "Task created!",
            "task": task
        }), 201

    except ValueError:

        return jsonify({
            "success": False,
            "message": "XP and coin rewards must be numbers"
        }), 400

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not create task",
            "error": str(error)
        }), 500


# ============================================================
# COMPLETE TASK
# ============================================================

@app.route("/api/tasks/<int:task_id>/complete", methods=["POST"])
def complete_task(task_id):

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    connection = None

    try:

        connection = get_db()

        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Get task
        cursor.execute(
            """
            SELECT *
            FROM tasks
            WHERE id = %s
            AND user_id = %s
            """,
            (task_id, user_id)
        )

        task = cursor.fetchone()

        if not task:

            cursor.close()
            connection.close()

            return jsonify({
                "success": False,
                "message": "Task not found"
            }), 404

        if task["completed"]:

            cursor.close()
            connection.close()

            return jsonify({
                "success": False,
                "message": "Task already completed"
            }), 400

        # Mark task completed
        cursor.execute(
            """
            UPDATE tasks
            SET
                completed = TRUE,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = %s
            AND user_id = %s
            """,
            (task_id, user_id)
        )

        # Get user
        cursor.execute(
            """
            SELECT
                level,
                xp,
                coins,
                current_streak,
                longest_streak,
                last_streak_date
            FROM users
            WHERE id = %s
            FOR UPDATE
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        old_level = user["level"]
        old_xp = user["xp"]

        new_xp = old_xp + task["xp_reward"]
        new_coins = user["coins"] + task["coin_reward"]

        # ====================================================
        # NON-LINEAR LEVEL SYSTEM
        # ====================================================

        level = 1
        remaining_xp = new_xp

        while remaining_xp >= level * level * 100:
            remaining_xp -= level * level * 100
            level += 1

        # ====================================================
        # STREAK SYSTEM
        # ====================================================

        today = date.today()

        current_streak = user["current_streak"] or 0
        longest_streak = user["longest_streak"] or 0
        last_streak_date = user["last_streak_date"]

        if last_streak_date is None:

            current_streak = 1

        elif last_streak_date == today:

            # Already completed a task today.
            # Keep the current streak.
            current_streak = max(current_streak, 1)

        elif last_streak_date == today - timedelta(days=1):

            current_streak += 1

        else:

            current_streak = 1

        if current_streak > longest_streak:
            longest_streak = current_streak

        # Update user
        cursor.execute(
            """
            UPDATE users
            SET
                level = %s,
                xp = %s,
                coins = %s,
                current_streak = %s,
                longest_streak = %s,
                last_streak_date = %s
            WHERE id = %s
            """,
            (
                level,
                new_xp,
                new_coins,
                current_streak,
                longest_streak,
                today,
                user_id
            )
        )

        # ====================================================
        # ATTRIBUTE REWARD
        # ====================================================

        category = (task["category"] or "").lower()

        attribute_column = None

        if category in ["gym", "fitness", "health", "exercise", "strength"]:
            attribute_column = "strength"

        elif category in ["coding", "study", "learning", "education", "intelligence"]:
            attribute_column = "intelligence"

        elif category in ["work", "discipline", "habit", "productivity"]:
            attribute_column = "discipline"

        elif category in ["art", "creative", "creativity", "design"]:
            attribute_column = "creativity"

        elif category in ["social", "friends", "communication"]:
            attribute_column = "social"

        if attribute_column:

            cursor.execute(
                f"""
                UPDATE attributes
                SET
                    {attribute_column} = {attribute_column} + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                """,
                (user_id,)
            )

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "message": "Quest completed!",
            "reward": {
                "xp": task["xp_reward"],
                "coins": task["coin_reward"]
            },
            "player": {
                "level": level,
                "xp": new_xp,
                "coins": new_coins,
                "current_streak": current_streak,
                "longest_streak": longest_streak
            },
            "level_up": level > old_level
        })

    except Exception as error:

        if connection:
            connection.rollback()
            connection.close()

        return jsonify({
            "success": False,
            "message": "Could not complete task",
            "error": str(error)
        }), 500


# ============================================================
# SHOP
# ============================================================

@app.route("/api/shop", methods=["GET"])
def shop():

    # Static shop items for prototype.
    # These can later be moved into a database table.

    items = [
        {
            "id": 1,
            "name": "XP Potion",
            "description": "A small boost for your journey.",
            "item_type": "potion",
            "cost": 50
        },
        {
            "id": 2,
            "name": "Health Potion",
            "description": "Recover your warrior energy.",
            "item_type": "health",
            "cost": 75
        },
        {
            "id": 3,
            "name": "Golden Sword",
            "description": "A legendary cosmetic weapon.",
            "item_type": "weapon",
            "cost": 250
        },
        {
            "id": 4,
            "name": "Magic Shield",
            "description": "Protect your character.",
            "item_type": "armor",
            "cost": 200
        }
    ]

    return jsonify({
        "success": True,
        "items": items
    })


# ============================================================
# BUY SHOP ITEM
# ============================================================

@app.route("/api/shop/buy", methods=["POST"])
def buy_item():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    try:

        data = request.get_json()

        item_id = int(data.get("item_id"))

        items = {
            1: {
                "name": "XP Potion",
                "type": "potion",
                "cost": 50
            },
            2: {
                "name": "Health Potion",
                "type": "health",
                "cost": 75
            },
            3: {
                "name": "Golden Sword",
                "type": "weapon",
                "cost": 250
            },
            4: {
                "name": "Magic Shield",
                "type": "armor",
                "cost": 200
            }
        }

        if item_id not in items:

            return jsonify({
                "success": False,
                "message": "Invalid shop item"
            }), 400

        item = items[item_id]

        connection = get_db()

        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Lock user row
        cursor.execute(
            """
            SELECT coins
            FROM users
            WHERE id = %s
            FOR UPDATE
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:

            cursor.close()
            connection.close()

            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        if user["coins"] < item["cost"]:

            cursor.close()
            connection.close()

            return jsonify({
                "success": False,
                "message": "Not enough coins"
            }), 400

        # Deduct coins
        cursor.execute(
            """
            UPDATE users
            SET coins = coins - %s
            WHERE id = %s
            RETURNING coins
            """,
            (
                item["cost"],
                user_id
            )
        )

        updated_user = cursor.fetchone()

        # Add item to inventory
        cursor.execute(
            """
            SELECT id
            FROM inventory
            WHERE user_id = %s
            AND item_name = %s
            """,
            (
                user_id,
                item["name"]
            )
        )

        existing_item = cursor.fetchone()

        if existing_item:

            cursor.execute(
                """
                UPDATE inventory
                SET quantity = quantity + 1
                WHERE id = %s
                """,
                (existing_item["id"],)
            )

        else:

            cursor.execute(
                """
                INSERT INTO inventory
                (
                    user_id,
                    item_name,
                    item_type,
                    quantity,
                    cost
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    1,
                    %s
                )
                """,
                (
                    user_id,
                    item["name"],
                    item["type"],
                    item["cost"]
                )
            )

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "message": f'{item["name"]} purchased!',
            "coins": updated_user["coins"]
        })

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Invalid item ID"
        }), 400

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Purchase failed",
            "error": str(error)
        }), 500


# ============================================================
# INVENTORY
# ============================================================

@app.route("/api/inventory", methods=["GET"])
def inventory():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    try:

        connection = get_db()

        cursor = connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT
                id,
                item_name,
                item_type,
                quantity,
                cost,
                acquired_at
            FROM inventory
            WHERE user_id = %s
            ORDER BY acquired_at DESC
            """,
            (user_id,)
        )

        items = cursor.fetchall()

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "inventory": items
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not load inventory",
            "error": str(error)
        }), 500


# ============================================================
# ATTRIBUTES
# ============================================================

@app.route("/api/attributes", methods=["GET"])
def get_attributes():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    try:

        connection = get_db()

        cursor = connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT
                strength,
                intelligence,
                discipline,
                creativity,
                social
            FROM attributes
            WHERE user_id = %s
            """,
            (user_id,)
        )

        attributes = cursor.fetchone()

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "attributes": attributes
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not load attributes",
            "error": str(error)
        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "ok",
        "application": "RPG Tracker"
    })


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    # API 404 should return JSON
    if request.path.startswith("/api/"):
        return jsonify({
            "success": False,
            "message": "API endpoint not found"
        }), 404

    return send_from_directory(FRONTEND_DIR, "index.html")


@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({
        "success": False,
        "message": "Internal server error"
    }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.environ.get("FLASK_DEBUG", "0") == "1"
    )