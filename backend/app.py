import os
from datetime import date, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor

from flask import (
    Flask,
    request,
    jsonify,
    session,
    send_from_directory,
)

from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend")
)

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY is missing from .env")

CORS(app, supports_credentials=True)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        database=os.environ.get("POSTGRES_DB"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        sslmode=os.environ.get("POSTGRES_SSLMODE", "require"),
    )


def fetch_one(query, params=()):
    connection = get_db()

    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    finally:
        connection.close()


def fetch_all(query, params=()):
    connection = get_db()

    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    finally:
        connection.close()


def execute_query(query, params=(), fetch=False):
    connection = get_db()

    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)

            result = None

            if fetch:
                result = cursor.fetchone()

            connection.commit()

            return result

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def create_database():

    connection = get_db()

    try:
        with connection.cursor() as cursor:

            # -------------------------------------------------
            # USERS
            # -------------------------------------------------

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    level INTEGER DEFAULT 1,
                    xp INTEGER DEFAULT 0,
                    coins INTEGER DEFAULT 100,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    longest_streak INTEGER DEFAULT 0,
                    current_streak INTEGER DEFAULT 0,
                    last_streak_date DATE
                );
            """)

            # -------------------------------------------------
            # TASKS
            # -------------------------------------------------

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER
                        REFERENCES users(id)
                        ON DELETE CASCADE,
                    title VARCHAR(100) NOT NULL,
                    description TEXT,
                    category VARCHAR(50),
                    xp_reward INTEGER DEFAULT 10,
                    coin_reward INTEGER DEFAULT 5,
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                );
            """)

            # -------------------------------------------------
            # ATTRIBUTES
            # -------------------------------------------------

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attributes (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER
                        REFERENCES users(id)
                        ON DELETE CASCADE,
                    strength INTEGER DEFAULT 1,
                    intelligence INTEGER DEFAULT 1,
                    discipline INTEGER DEFAULT 1,
                    creativity INTEGER DEFAULT 1,
                    social INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # -------------------------------------------------
            # INVENTORY
            # -------------------------------------------------

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER
                        REFERENCES users(id)
                        ON DELETE CASCADE,
                    item_name VARCHAR(100) NOT NULL,
                    item_type VARCHAR(50),
                    quantity INTEGER DEFAULT 1,
                    cost INTEGER DEFAULT 0,
                    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # -------------------------------------------------
            # OLD DATABASE COMPATIBILITY
            # -------------------------------------------------

            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1;
            """)

            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0;
            """)

            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS coins INTEGER DEFAULT 100;
            """)

            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS longest_streak INTEGER DEFAULT 0;
            """)

            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS current_streak INTEGER DEFAULT 0;
            """)

            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS last_streak_date DATE;
            """)

            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS created_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
            """)

            # -------------------------------------------------
            # IMPORTANT FIX
            #
            # ON CONFLICT (user_id) requires user_id to be
            # UNIQUE.
            #
            # This creates the unique index even when the
            # database already existed before this version.
            # -------------------------------------------------

            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                attributes_user_id_unique_idx
                ON attributes(user_id);
            """)

        connection.commit()

        print("Database initialization successful.")

    except Exception as error:

        connection.rollback()

        print("Database initialization failed:")
        print(error)

        raise

    finally:
        connection.close()


# =========================================================
# FRONTEND ROUTES
# =========================================================

@app.route("/")
def home():
    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(
        FRONTEND_DIR,
        filename
    )


# =========================================================
# DATABASE TEST
# =========================================================

@app.route("/api/test-db")
def test_database():

    connection = None

    try:

        connection = get_db()

        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT current_database(), version();
            """)

            row = cursor.fetchone()

        return jsonify({
            "success": True,
            "message": "PostgreSQL connection successful!",
            "database": row[0],
            "version": row[1]
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Database connection failed",
            "error": str(error)
        }), 500

    finally:

        if connection:
            connection.close()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_current_user():

    user_id = session.get("user_id")

    if not user_id:
        return None

    return fetch_one("""
        SELECT
            id,
            username,
            email,
            level,
            xp,
            coins,
            longest_streak,
            current_streak,
            last_streak_date,
            created_at
        FROM users
        WHERE id = %s
    """, (user_id,))


def login_required():

    user_id = session.get("user_id")

    if not user_id:
        return None

    return user_id


# =========================================================
# XP / LEVEL SYSTEM
# =========================================================

def xp_needed_for_level(level):

    return int(100 * (level ** 1.5))


def calculate_level(xp):

    level = 1
    remaining_xp = max(0, int(xp))

    while remaining_xp >= xp_needed_for_level(level):

        remaining_xp -= xp_needed_for_level(level)
        level += 1

    return (
        level,
        remaining_xp,
        xp_needed_for_level(level)
    )


# =========================================================
# STREAK SYSTEM
# =========================================================

def update_streak(user_id):

    user = fetch_one("""
        SELECT
            current_streak,
            longest_streak,
            last_streak_date
        FROM users
        WHERE id = %s
    """, (user_id,))

    if not user:
        return

    today = date.today()
    last_date = user["last_streak_date"]

    current = user["current_streak"] or 0
    longest = user["longest_streak"] or 0

    if last_date == today:
        return

    if last_date == today - timedelta(days=1):
        current += 1

    else:
        current = 1

    longest = max(longest, current)

    execute_query("""
        UPDATE users
        SET
            current_streak = %s,
            longest_streak = %s,
            last_streak_date = %s
        WHERE id = %s
    """, (
        current,
        longest,
        today,
        user_id
    ))


# =========================================================
# ATTRIBUTE SYSTEM
# =========================================================

def update_attribute_for_category(user_id, category):

    if not category:
        return

    category = category.lower().strip()

    attribute_map = {

        "gym": "strength",
        "fitness": "strength",
        "workout": "strength",

        "coding": "intelligence",
        "study": "intelligence",
        "learning": "intelligence",

        "work": "discipline",
        "productivity": "discipline",
        "habit": "discipline",

        "creative": "creativity",
        "creativity": "creativity",
        "art": "creativity",

        "social": "social",
        "communication": "social",
    }

    attribute = attribute_map.get(category)

    if not attribute:
        return

    allowed = {
        "strength",
        "intelligence",
        "discipline",
        "creativity",
        "social"
    }

    if attribute not in allowed:
        return

    # Make sure attribute row exists.
    execute_query("""
        INSERT INTO attributes (user_id)
        VALUES (%s)
        ON CONFLICT (user_id) DO NOTHING
    """, (user_id,))

    execute_query(f"""
        UPDATE attributes
        SET
            {attribute} = {attribute} + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = %s
    """, (user_id,))


# =========================================================
# AUTHENTICATION - REGISTER
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    username = str(
        data.get("username", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not username or not email or not password:

        return jsonify({
            "success": False,
            "message":
                "Username, email and password are required."
        }), 400

    if len(username) < 3:

        return jsonify({
            "success": False,
            "message":
                "Username must be at least 3 characters."
        }), 400

    if len(password) < 6:

        return jsonify({
            "success": False,
            "message":
                "Password must be at least 6 characters."
        }), 400

    # -----------------------------------------------------
    # CHECK EXISTING USER
    # -----------------------------------------------------

    existing = fetch_one("""
        SELECT id
        FROM users
        WHERE username = %s
        OR email = %s
    """, (
        username,
        email
    ))

    if existing:

        return jsonify({
            "success": False,
            "message":
                "Username or email already exists."
        }), 409

    password_hash = generate_password_hash(password)

    connection = get_db()

    try:

        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            # -------------------------------------------------
            # CREATE USER
            # -------------------------------------------------

            cursor.execute("""
                INSERT INTO users (
                    username,
                    email,
                    password_hash,
                    level,
                    xp,
                    coins
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    1,
                    0,
                    100
                )
                RETURNING
                    id,
                    username,
                    email,
                    level,
                    xp,
                    coins
            """, (
                username,
                email,
                password_hash
            ))

            user = cursor.fetchone()

            # -------------------------------------------------
            # CREATE CHARACTER ATTRIBUTES
            # -------------------------------------------------

            cursor.execute("""
                INSERT INTO attributes (
                    user_id
                )
                VALUES (%s)
                ON CONFLICT (user_id) DO NOTHING
            """, (user["id"],))

        connection.commit()

        # Automatically log in after registration.
        session.clear()
        session["user_id"] = user["id"]

        return jsonify({
            "success": True,
            "message": "Registration successful!",
            "user": user
        }), 201

    except psycopg2.IntegrityError as error:

        connection.rollback()

        return jsonify({
            "success": False,
            "message":
                "Username or email already exists.",
            "error": str(error)
        }), 409

    except Exception as error:

        connection.rollback()

        return jsonify({
            "success": False,
            "message": "Registration failed.",
            "error": str(error)
        }), 500

    finally:

        connection.close()


# =========================================================
# AUTHENTICATION - LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    try:

        data = request.get_json(silent=True) or {}

        username = str(
            data.get("username", "")
        ).strip()

        password = str(
            data.get("password", "")
        )

        if not username or not password:

            return jsonify({
                "success": False,
                "message":
                    "Username and password are required."
            }), 400

        user = fetch_one("""
            SELECT
                id,
                username,
                email,
                password_hash,
                level,
                xp,
                coins
            FROM users
            WHERE username = %s
            OR email = %s
        """, (
            username,
            username.lower()
        ))

        if not user:

            return jsonify({
                "success": False,
                "message":
                    "Invalid username or password."
            }), 401

        if not check_password_hash(
            user["password_hash"],
            password
        ):

            return jsonify({
                "success": False,
                "message":
                    "Invalid username or password."
            }), 401

        session.clear()

        session["user_id"] = user["id"]

        return jsonify({
            "success": True,
            "message": "Login successful!",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "level": user["level"] or 1,
                "xp": user["xp"] or 0,
                "coins": user["coins"] or 0
            }
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Login failed.",
            "error": str(error)
        }), 500


# =========================================================
# LOGOUT
# =========================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    })


# =========================================================
# CURRENT USER
# =========================================================

@app.route("/api/me")
def me():

    try:

        user = get_current_user()

        if not user:

            return jsonify({
                "success": False,
                "message": "Not logged in."
            }), 401

        return jsonify({
            "success": True,
            "user": user
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not load user.",
            "error": str(error)
        }), 500


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/api/dashboard")
def dashboard():

    try:

        user_id = login_required()

        if not user_id:

            return jsonify({
                "success": False,
                "message": "Please login first."
            }), 401

        user = get_current_user()

        if not user:

            session.clear()

            return jsonify({
                "success": False,
                "message": "User not found."
            }), 401

        # -------------------------------------------------
        # ATTRIBUTES
        # -------------------------------------------------

        attributes = fetch_one("""
            SELECT
                strength,
                intelligence,
                discipline,
                creativity,
                social
            FROM attributes
            WHERE user_id = %s
        """, (user_id,))

        if not attributes:

            execute_query("""
                INSERT INTO attributes (user_id)
                VALUES (%s)
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id,))

            attributes = fetch_one("""
                SELECT
                    strength,
                    intelligence,
                    discipline,
                    creativity,
                    social
                FROM attributes
                WHERE user_id = %s
            """, (user_id,))

        # -------------------------------------------------
        # TASK STATISTICS
        # -------------------------------------------------

        total_tasks = fetch_one("""
            SELECT COUNT(*) AS count
            FROM tasks
            WHERE user_id = %s
        """, (user_id,))

        completed_tasks = fetch_one("""
            SELECT COUNT(*) AS count
            FROM tasks
            WHERE user_id = %s
            AND completed = TRUE
        """, (user_id,))

        # -------------------------------------------------
        # LEVEL CALCULATION
        # -------------------------------------------------

        level, current_level_xp, level_xp_required = (
            calculate_level(user["xp"])
        )

        # Synchronize stored level.
        if level != user["level"]:

            execute_query("""
                UPDATE users
                SET level = %s
                WHERE id = %s
            """, (
                level,
                user_id
            ))

            user["level"] = level

        return jsonify({
            "success": True,

            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "level": level,
                "xp": user["xp"] or 0,
                "coins": user["coins"] or 0,
                "current_streak":
                    user["current_streak"] or 0,
                "longest_streak":
                    user["longest_streak"] or 0
            },

            "xp": {
                "total": user["xp"] or 0,
                "current": current_level_xp,
                "required": level_xp_required,
                "percentage": round(
                    (
                        current_level_xp /
                        level_xp_required
                    ) * 100,
                    2
                ) if level_xp_required else 0
            },

            "attributes": attributes,

            "stats": {
                "total_tasks":
                    total_tasks["count"],
                "completed_tasks":
                    completed_tasks["count"]
            }
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Dashboard loading failed.",
            "error": str(error)
        }), 500


# =========================================================
# GET TASKS
# =========================================================

@app.route("/api/tasks", methods=["GET"])
def get_tasks():

    try:

        user_id = login_required()

        if not user_id:

            return jsonify({
                "success": False,
                "message": "Please login first."
            }), 401

        tasks = fetch_all("""
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
            ORDER BY
                completed ASC,
                created_at DESC
        """, (user_id,))

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


# =========================================================
# CREATE TASK
# =========================================================

@app.route("/api/tasks", methods=["POST"])
def create_task():

    try:

        user_id = login_required()

        if not user_id:

            return jsonify({
                "success": False,
                "message": "Please login first."
            }), 401

        data = request.get_json(silent=True) or {}

        title = str(
            data.get("title", "")
        ).strip()

        description = str(
            data.get("description", "")
        ).strip()

        category = str(
            data.get("category", "")
        ).strip()

        try:
            xp_reward = int(
                data.get("xp_reward", 10)
            )
        except (TypeError, ValueError):
            xp_reward = 10

        try:
            coin_reward = int(
                data.get("coin_reward", 5)
            )
        except (TypeError, ValueError):
            coin_reward = 5

        if not title:

            return jsonify({
                "success": False,
                "message": "Task title is required."
            }), 400

        xp_reward = max(
            1,
            min(xp_reward, 10000)
        )

        coin_reward = max(
            0,
            min(coin_reward, 10000)
        )

        task = execute_query("""
            INSERT INTO tasks (
                user_id,
                title,
                description,
                category,
                xp_reward,
                coin_reward
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING
                id,
                title,
                description,
                category,
                xp_reward,
                coin_reward,
                completed,
                created_at
        """, (
            user_id,
            title,
            description,
            category,
            xp_reward,
            coin_reward
        ), fetch=True)

        return jsonify({
            "success": True,
            "message": "Quest created successfully!",
            "task": task
        }), 201

    except Exception as error:

        return jsonify({
            "success": False,
            "message": "Could not create quest.",
            "error": str(error)
        }), 500


# =========================================================
# COMPLETE TASK
# =========================================================

@app.route(
    "/api/tasks/<int:task_id>/complete",
    methods=["POST"]
)
def complete_task(task_id):

    user_id = login_required()

    if not user_id:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    connection = get_db()

    try:

        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            # -------------------------------------------------
            # LOCK TASK
            # -------------------------------------------------

            cursor.execute("""
                SELECT *
                FROM tasks
                WHERE id = %s
                AND user_id = %s
                FOR UPDATE
            """, (
                task_id,
                user_id
            ))

            task = cursor.fetchone()

            if not task:

                connection.rollback()

                return jsonify({
                    "success": False,
                    "message": "Quest not found."
                }), 404

            if task["completed"]:

                connection.rollback()

                return jsonify({
                    "success": False,
                    "message":
                        "Quest is already completed."
                }), 400

            # -------------------------------------------------
            # COMPLETE TASK
            # -------------------------------------------------

            cursor.execute("""
                UPDATE tasks
                SET
                    completed = TRUE,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                AND user_id = %s
            """, (
                task_id,
                user_id
            ))

            # -------------------------------------------------
            # ADD XP + COINS
            # -------------------------------------------------

            cursor.execute("""
                UPDATE users
                SET
                    xp = COALESCE(xp, 0) + %s,
                    coins = COALESCE(coins, 0) + %s
                WHERE id = %s
            """, (
                task["xp_reward"],
                task["coin_reward"],
                user_id
            ))

        connection.commit()

        # -----------------------------------------------------
        # STREAK
        # -----------------------------------------------------

        update_streak(user_id)

        # -----------------------------------------------------
        # ATTRIBUTE
        # -----------------------------------------------------

        update_attribute_for_category(
            user_id,
            task["category"]
        )

        # -----------------------------------------------------
        # USER AFTER REWARD
        # -----------------------------------------------------

        user = get_current_user()

        old_level = user["level"] or 1

        new_level, current_xp, required_xp = (
            calculate_level(
                user["xp"] or 0
            )
        )

        if new_level != old_level:

            execute_query("""
                UPDATE users
                SET level = %s
                WHERE id = %s
            """, (
                new_level,
                user_id
            ))

        return jsonify({
            "success": True,
            "message": "Quest completed!",

            "reward": {
                "xp": task["xp_reward"],
                "coins": task["coin_reward"]
            },

            "level_up":
                new_level > old_level,

            "user": {
                "level": new_level,
                "xp": user["xp"],
                "coins": user["coins"],
                "current_streak":
                    user["current_streak"] or 0
            }
        })

    except Exception as error:

        connection.rollback()

        return jsonify({
            "success": False,
            "message": "Could not complete quest.",
            "error": str(error)
        }), 500

    finally:

        connection.close()


# =========================================================
# SHOP
# =========================================================

SHOP_ITEMS = [

    {
        "id": 1,
        "name": "Health Potion",
        "type": "Potion",
        "cost": 25,
        "description":
            "A small reward for your adventure."
    },

    {
        "id": 2,
        "name": "Iron Sword",
        "type": "Weapon",
        "cost": 100,
        "description":
            "A symbol of your growing strength."
    },

    {
        "id": 3,
        "name": "Magic Book",
        "type": "Knowledge",
        "cost": 75,
        "description":
            "Boost your learning journey."
    },

    {
        "id": 4,
        "name": "Golden Shield",
        "type": "Armor",
        "cost": 150,
        "description":
            "A reward for dedicated adventurers."
    },

    {
        "id": 5,
        "name": "Legendary Crown",
        "type": "Legendary",
        "cost": 300,
        "description":
            "For those who reach legendary status."
    }
]


# =========================================================
# GET SHOP
# =========================================================

@app.route("/api/shop", methods=["GET"])
def get_shop():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    return jsonify({
        "success": True,
        "items": SHOP_ITEMS
    })


# =========================================================
# BUY SHOP ITEM
# =========================================================

@app.route("/api/shop/buy", methods=["POST"])
def buy_item():

    user_id = login_required()

    if not user_id:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    data = request.get_json(silent=True) or {}

    item_id = data.get("item_id")

    try:
        item_id = int(item_id)

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "Invalid item."
        }), 400

    item = next(
        (
            x for x in SHOP_ITEMS
            if x["id"] == item_id
        ),
        None
    )

    if not item:

        return jsonify({
            "success": False,
            "message": "Item not found."
        }), 404

    connection = get_db()

    try:

        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            # -------------------------------------------------
            # LOCK USER
            # -------------------------------------------------

            cursor.execute("""
                SELECT coins
                FROM users
                WHERE id = %s
                FOR UPDATE
            """, (user_id,))

            user = cursor.fetchone()

            if not user:

                connection.rollback()

                return jsonify({
                    "success": False,
                    "message": "User not found."
                }), 404

            current_coins = user["coins"] or 0

            if current_coins < item["cost"]:

                connection.rollback()

                return jsonify({
                    "success": False,
                    "message": "Not enough coins."
                }), 400

            # -------------------------------------------------
            # DEDUCT COINS
            # -------------------------------------------------

            cursor.execute("""
                UPDATE users
                SET coins = coins - %s
                WHERE id = %s
            """, (
                item["cost"],
                user_id
            ))

            # -------------------------------------------------
            # CHECK INVENTORY
            # -------------------------------------------------

            cursor.execute("""
                SELECT
                    id,
                    quantity
                FROM inventory
                WHERE user_id = %s
                AND item_name = %s
                FOR UPDATE
            """, (
                user_id,
                item["name"]
            ))

            existing = cursor.fetchone()

            if existing:

                cursor.execute("""
                    UPDATE inventory
                    SET quantity = quantity + 1
                    WHERE id = %s
                """, (
                    existing["id"],
                ))

            else:

                cursor.execute("""
                    INSERT INTO inventory (
                        user_id,
                        item_name,
                        item_type,
                        quantity,
                        cost
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        1,
                        %s
                    )
                """, (
                    user_id,
                    item["name"],
                    item["type"],
                    item["cost"]
                ))

        connection.commit()

        updated_user = get_current_user()

        return jsonify({
            "success": True,
            "message":
                f"{item['name']} purchased!",
            "item": item,
            "coins":
                updated_user["coins"]
        })

    except Exception as error:

        connection.rollback()

        return jsonify({
            "success": False,
            "message": "Purchase failed.",
            "error": str(error)
        }), 500

    finally:

        connection.close()


# =========================================================
# INVENTORY
# =========================================================

@app.route("/api/inventory", methods=["GET"])
def get_inventory():

    try:

        user_id = login_required()

        if not user_id:

            return jsonify({
                "success": False,
                "message": "Please login first."
            }), 401

        items = fetch_all("""
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
        """, (user_id,))

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


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def not_found(error):

    if request.path.startswith("/api/"):

        return jsonify({
            "success": False,
            "message": "API endpoint not found."
        }), 404

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


@app.errorhandler(500)
def server_error(error):

    if request.path.startswith("/api/"):

        return jsonify({
            "success": False,
            "message": "Internal server error."
        }), 500

    return "Internal Server Error", 500


# =========================================================
# INITIALIZE DATABASE
# =========================================================
#
# IMPORTANT:
# This runs for BOTH:
#
#     python app.py
#
# and Render/Gunicorn:
#
#     gunicorn app:app
#
# Therefore the existing cloud database gets the required
# unique index automatically.
# =========================================================

try:

    create_database()

except Exception as error:

    print("Database initialization warning:")
    print(error)


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    debug_mode = (
        os.environ.get(
            "FLASK_DEBUG",
            "0"
        ) == "1"
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_mode
    )