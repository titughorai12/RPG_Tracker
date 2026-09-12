from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import psycopg2
import os
from datetime import datetime, timedelta


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

CORS(app, supports_credentials=True)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        database=os.environ.get("POSTGRES_DB", "liferpg"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        sslmode="disable"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "RPG Tracker API is running!"
    })


# ============================================================
# TEST DATABASE
# ============================================================

@app.route("/api/test-db")
def test_db():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]

        return jsonify({
            "success": True,
            "message": "PostgreSQL connection successful!",
            "database": "liferpg",
            "version": version
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Database connection failed.",
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# REGISTER
# ============================================================

@app.route("/api/register", methods=["POST"])
def register():

    connection = None
    cursor = None

    try:

        data = request.get_json() or {}

        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not username or not email or not password:

            return jsonify({
                "success": False,
                "message": "Username, email and password are required."
            }), 400

        if len(username) > 50:

            return jsonify({
                "success": False,
                "message": "Username must be 50 characters or less."
            }), 400

        if len(email) > 100:

            return jsonify({
                "success": False,
                "message": "Email must be 100 characters or less."
            }), 400

        if len(password) < 6:

            return jsonify({
                "success": False,
                "message": "Password must contain at least 6 characters."
            }), 400

        connection = get_db_connection()
        cursor = connection.cursor()

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

            return jsonify({
                "success": False,
                "message": "Username or email already exists."
            }), 409

        password_hash = generate_password_hash(password)

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
                current_streak,
                longest_streak
            )
            VALUES (%s, %s, %s, 1, 0, 0, 0, 0)
            RETURNING id
            """,
            (username, email, password_hash)
        )

        user_id = cursor.fetchone()[0]

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
            VALUES (%s, 1, 1, 1, 1, 1)
            """,
            (user_id,)
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Character created successfully!",
            "user_id": user_id
        }), 201

    except Exception as error:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Registration failed.",
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# LOGIN
# ============================================================

@app.route("/api/login", methods=["POST"])
def login():

    connection = None
    cursor = None

    try:

        data = request.get_json() or {}

        login_value = data.get("login", "").strip()
        password = data.get("password", "")

        if not login_value or not password:

            return jsonify({
                "success": False,
                "message": "Login and password are required."
            }), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                username,
                email,
                password_hash
            FROM users
            WHERE username = %s OR email = %s
            """,
            (login_value, login_value.lower())
        )

        user = cursor.fetchone()

        if not user:

            return jsonify({
                "success": False,
                "message": "Invalid username/email or password."
            }), 401

        user_id = user[0]
        username = user[1]
        email = user[2]
        password_hash = user[3]

        if not check_password_hash(password_hash, password):

            return jsonify({
                "success": False,
                "message": "Invalid username/email or password."
            }), 401

        session.clear()

        session["user_id"] = user_id
        session["username"] = username

        return jsonify({
            "success": True,
            "message": "Login successful!",
            "user": {
                "id": user_id,
                "username": username,
                "email": email
            }
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Login failed.",
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# CURRENT USER
# ============================================================

@app.route("/api/me")
def me():

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "success": False,
            "message": "Not logged in."
        }), 401

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

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
                longest_streak
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:

            session.clear()

            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        return jsonify({
            "success": True,
            "user": {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "level": user[3],
                "xp": user[4],
                "coins": user[5],
                "current_streak": user[6],
                "longest_streak": user[7]
            }
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not load user.",
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# LOGOUT
# ============================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    })


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/api/dashboard")
def dashboard():

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

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
                longest_streak
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:

            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

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

        return jsonify({
            "success": True,

            "user": {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "level": user[3],
                "xp": user[4],
                "coins": user[5],
                "current_streak": user[6],
                "longest_streak": user[7]
            },

            "attributes": {
                "strength": attributes[0] if attributes else 1,
                "intelligence": attributes[1] if attributes else 1,
                "discipline": attributes[2] if attributes else 1,
                "creativity": attributes[3] if attributes else 1,
                "social": attributes[4] if attributes else 1
            }
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Dashboard error.",
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# CREATE TASK
# ============================================================

@app.route("/api/tasks", methods=["POST"])
def create_task():

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    connection = None
    cursor = None

    try:

        data = request.get_json() or {}

        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        category = data.get("category", "Personal").strip()

        if not title:

            return jsonify({
                "success": False,
                "message": "Quest title is required."
            }), 400

        if len(title) > 100:

            return jsonify({
                "success": False,
                "message": "Quest title must be 100 characters or less."
            }), 400

        if len(description) > 1000:

            return jsonify({
                "success": False,
                "message": "Quest description must be 1000 characters or less."
            }), 400

        allowed_categories = [
            "Coding",
            "Fitness",
            "Study",
            "Work",
            "Personal",
            "Social"
        ]

        if category not in allowed_categories:

            category = "Personal"

        xp_reward = 50
        coin_reward = 25

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO tasks
            (
                user_id,
                title,
                description,
                category,
                xp_reward,
                coin_reward,
                completed
            )
            VALUES (%s, %s, %s, %s, %s, %s, FALSE)
            RETURNING id
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

        task_id = cursor.fetchone()[0]

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Quest created successfully!",
            "task_id": task_id
        }), 201

    except Exception as error:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Could not create quest.",
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# GET TASKS
# ============================================================

@app.route("/api/tasks")
def get_tasks():

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

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
            ORDER BY completed ASC, created_at DESC
            """,
            (user_id,)
        )

        rows = cursor.fetchall()

        tasks = []

        for row in rows:

            tasks.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "category": row[3],
                "xp_reward": row[4],
                "coin_reward": row[5],
                "completed": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "completed_at": row[8].isoformat() if row[8] else None
            })

        return jsonify({
            "success": True,
            "tasks": tasks
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not load quests.",
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# COMPLETE TASK
# ============================================================

@app.route("/api/tasks/<int:task_id>/complete", methods=["PUT"])
def complete_task(task_id):

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # ----------------------------------------------------
        # Get task
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                title,
                category,
                xp_reward,
                coin_reward,
                completed
            FROM tasks
            WHERE id = %s
            AND user_id = %s
            """,
            (task_id, user_id)
        )

        task = cursor.fetchone()

        if not task:

            return jsonify({
                "success": False,
                "message": "Quest not found."
            }), 404

        if task[5]:

            return jsonify({
                "success": False,
                "message": "Quest is already completed."
            }), 400

        task_title = task[1]
        category = task[2]
        xp_reward = task[3]
        coin_reward = task[4]

        # ----------------------------------------------------
        # Mark task completed
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Get player
        # ----------------------------------------------------

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

        player = cursor.fetchone()

        if not player:

            connection.rollback()

            return jsonify({
                "success": False,
                "message": "Player not found."
            }), 404

        current_level = player[0]
        current_xp = player[1]
        current_coins = player[2]
        current_streak = player[3] or 0
        longest_streak = player[4] or 0
        last_streak_date = player[5]

        # ----------------------------------------------------
        # STREAK LOGIC
        # ----------------------------------------------------

        today = datetime.now().date()

        streak_updated = False

        if last_streak_date is None:

            current_streak = 1
            streak_updated = True

        elif last_streak_date == today:

            # Already completed something today.
            current_streak = current_streak

        elif last_streak_date == today - timedelta(days=1):

            current_streak += 1
            streak_updated = True

        else:

            current_streak = 1
            streak_updated = True

        if current_streak > longest_streak:

            longest_streak = current_streak

        # ----------------------------------------------------
        # XP AND COINS
        # ----------------------------------------------------

        new_xp = current_xp + xp_reward
        new_coins = current_coins + coin_reward

        new_level = current_level
        level_ups = 0

        # Nonlinear level progression
        while new_xp >= new_level * 100:

            new_xp -= new_level * 100

            new_level += 1

            level_ups += 1

        # ----------------------------------------------------
        # UPDATE PLAYER
        # ----------------------------------------------------

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
                new_level,
                new_xp,
                new_coins,
                current_streak,
                longest_streak,
                today,
                user_id
            )
        )

        # ----------------------------------------------------
        # ATTRIBUTE MAPPING
        # ----------------------------------------------------

        attribute_map = {
            "Fitness": "strength",
            "Coding": "intelligence",
            "Study": "intelligence",
            "Work": "discipline",
            "Personal": "discipline",
            "Social": "social"
        }

        attribute = attribute_map.get(
            category,
            "discipline"
        )

        allowed_attributes = {
            "strength",
            "intelligence",
            "discipline",
            "creativity",
            "social"
        }

        if attribute in allowed_attributes:

            cursor.execute(
                f"""
                UPDATE attributes
                SET
                    {attribute} = {attribute} + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                """,
                (user_id,)
            )

        connection.commit()

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "message": f"Quest '{task_title}' completed!",

            "reward": {
                "xp": xp_reward,
                "coins": coin_reward
            },

            "player": {
                "level": new_level,
                "xp": new_xp,
                "coins": new_coins,
                "level_ups": level_ups,
                "current_streak": current_streak,
                "longest_streak": longest_streak
            },

            "streak": {
                "current": current_streak,
                "longest": longest_streak,
                "updated": streak_updated
            },

            "attribute": attribute
        })

    except Exception as error:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Could not complete quest.",
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# SHOP ITEMS
# ============================================================

SHOP_ITEMS = [

    {
        "id": 1,
        "name": "Iron Sword",
        "type": "Equipment",
        "description": "A basic warrior sword.",
        "cost": 100,
        "icon": "⚔️"
    },

    {
        "id": 2,
        "name": "Guardian Shield",
        "type": "Equipment",
        "description": "Protect yourself from life's challenges.",
        "cost": 150,
        "icon": "🛡️"
    },

    {
        "id": 3,
        "name": "Health Potion",
        "type": "Consumable",
        "description": "A potion for your adventure.",
        "cost": 75,
        "icon": "🧪"
    },

    {
        "id": 4,
        "name": "Magic Book",
        "type": "Special",
        "description": "A mysterious book of knowledge.",
        "cost": 250,
        "icon": "📕"
    },

    {
        "id": 5,
        "name": "Golden Crown",
        "type": "Legendary",
        "description": "A reward for legendary players.",
        "cost": 500,
        "icon": "👑"
    }

]


# ============================================================
# GET SHOP
# ============================================================

@app.route("/api/shop")
def get_shop():

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    return jsonify({
        "success": True,
        "items": SHOP_ITEMS
    })


# ============================================================
# BUY SHOP ITEM
# ============================================================

@app.route("/api/shop/buy", methods=["POST"])
def buy_shop_item():

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    connection = None
    cursor = None

    try:

        data = request.get_json() or {}

        item_id = data.get("item_id")

        try:
            item_id = int(item_id)
        except (TypeError, ValueError):

            return jsonify({
                "success": False,
                "message": "Invalid item ID."
            }), 400

        item = next(
            (
                shop_item
                for shop_item in SHOP_ITEMS
                if shop_item["id"] == item_id
            ),
            None
        )

        if not item:

            return jsonify({
                "success": False,
                "message": "Item not found."
            }), 404

        connection = get_db_connection()
        cursor = connection.cursor()

        # Lock player row during purchase
        cursor.execute(
            """
            SELECT coins
            FROM users
            WHERE id = %s
            FOR UPDATE
            """,
            (user_id,)
        )

        player = cursor.fetchone()

        if not player:

            return jsonify({
                "success": False,
                "message": "Player not found."
            }), 404

        current_coins = player[0]

        if current_coins < item["cost"]:

            return jsonify({
                "success": False,
                "message": "Not enough coins."
            }), 400

        new_coins = current_coins - item["cost"]

        # Deduct coins
        cursor.execute(
            """
            UPDATE users
            SET coins = %s
            WHERE id = %s
            """,
            (new_coins, user_id)
        )

        # Check inventory
        cursor.execute(
            """
            SELECT id, quantity
            FROM inventory
            WHERE user_id = %s
            AND item_name = %s
            """,
            (user_id, item["name"])
        )

        existing_item = cursor.fetchone()

        if existing_item:

            cursor.execute(
                """
                UPDATE inventory
                SET quantity = quantity + 1
                WHERE id = %s
                """,
                (existing_item[0],)
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
                VALUES (%s, %s, %s, 1, %s)
                """,
                (
                    user_id,
                    item["name"],
                    item["type"],
                    item["cost"]
                )
            )

        connection.commit()

        return jsonify({
            "success": True,
            "message": f"{item['name']} purchased successfully!",
            "item": item,
            "coins": new_coins
        })

    except Exception as error:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": "Purchase failed.",
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# INVENTORY
# ============================================================

@app.route("/api/inventory")
def get_inventory():

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

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

        rows = cursor.fetchall()

        items = []

        for row in rows:

            items.append({
                "id": row[0],
                "item_name": row[1],
                "item_type": row[2],
                "quantity": row[3],
                "cost": row[4],
                "acquired_at": row[5].isoformat()
                if row[5]
                else None
            })

        return jsonify({
            "success": True,
            "items": items
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not load inventory.",
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )