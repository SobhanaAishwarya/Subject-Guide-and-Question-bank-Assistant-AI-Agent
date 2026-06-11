import bcrypt

from database.db import get_connection


def verify_password(
        plain_password,
        hashed_password
):

    return bcrypt.checkpw(
        plain_password.encode(),
        hashed_password.encode()
    )


def login_user(
        email,
        password
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id,name,password
        FROM users
        WHERE email = ?
        """,
        (email,)
    )

    user = cursor.fetchone()

    conn.close()

    if not user:
        return None

    user_id = user[0]
    name = user[1]
    stored_password = user[2]

    if verify_password(
            password,
            stored_password
    ):
        return {
            "id": user_id,
            "name": name
        }

    return None