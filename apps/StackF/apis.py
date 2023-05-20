import sqlite3

import sqlite3
import pandas as pd


def print_db(file_path="../StackF/perf.db"):
    # Connect to the database file
    conn = sqlite3.connect(file_path)

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Execute an SQL query to fetch data
    cursor.execute("SELECT * FROM mnist")

    # Fetch all rows from the query result
    rows = cursor.fetchall()

    # Process the fetched rows
    for row in rows:
        print(row[0], row[1])

    # Close the cursor and connection
    cursor.close()
    conn.close()


def dumb_db(tab_id, file_path="../StackF/perf.db"):
    # Connect to the database file
    conn = sqlite3.connect(file_path)

    # Execute a query to fetch data from specific columns
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {tab_id}")
    rows = cursor.fetchall()

    # Create a pandas DataFrame from the fetched rows
    df = pd.DataFrame(rows)

    # Save the DataFrame to an Excel file
    df.to_excel(f'{tab_id}.xlsx', index=False)

    # Close the cursor and connection
    cursor.close()
    conn.close()
