from database.users import create_users_table
from database.history import create_history_table
from database.quizzes import create_quiz_table
from database.analytics import create_analytics_table


def initialize_database():

    create_users_table()

    create_history_table()

    create_quiz_table()

    create_analytics_table()