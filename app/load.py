import pandas as pd
import sqlite3


def load_to_database(df):

    connection = sqlite3.connect("database/students.db")

    df.to_sql(
        "final_students",
        connection,
        if_exists="replace",
        index=False
    )

    connection.close()

    print("Data loaded successfully.")
    
def verify_loaded_data():

    connection = sqlite3.connect("database/students.db")

    df = pd.read_sql("SELECT * FROM final_students", connection)

    connection.close()

    return df

if __name__ == "__main__":

    data = verify_loaded_data()

    print(data)
    print("\nNumber of rows:", len(data))