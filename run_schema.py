import sqlite3

def execute_sql_file(db_path, sql_file_path):
    """
    Executes SQL commands from a file against an SQLite database.

    Args:
        db_path (str): Path to the SQLite database file.
        sql_file_path (str): Path to the SQL file containing commands.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        with open(sql_file_path, 'r') as f:
            sql_commands = f.read()
            cursor.executescript(sql_commands)  # Execute multiple SQL statements
        conn.commit()
        print(f"SQL file '{sql_file_path}' executed successfully on '{db_path}'")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    db_file = 'database.db'  # Name of your database file
    sql_file = 'schema.sql'  # Name of your SQL file
    execute_sql_file(db_file, sql_file)