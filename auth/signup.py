import bcrypt
import sqlite3

from database.db import get_connection


def hash_password(password):

    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()


def create_user(name, email, password):

    conn = get_connection()

    cursor = conn.cursor()

    try:

        hashed_password = hash_password(password)

        cursor.execute(
            """
            INSERT INTO users(
                name,
                email,
                password
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                email,
                hashed_password
            )
        )

        conn.commit()

        return True, "Account created successfully"

    except sqlite3.IntegrityError:

        return False, "Email already registered"

    except Exception as e:

        return False, str(e)

    finally:

        conn.close()