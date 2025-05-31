import mysql.connector
import phpserialize
import sys
import json

class WordpressDatabaseManager:
    def __init__(self, host, user, password, database, port=3306):
        try:
            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port
            )
            self.cursor = self.conn.cursor()
        except mysql.connector.Error as e:
            print(f"Error connecting to MySQL: {e}")
            sys.exit(1)

    def set_value(self, table, column, value, condition):
        """
        Update a specific element's value in the database.

        :param table: The table name.
        :param column: The column name to update.
        :param value: The new value to set.
        :param condition: The condition to identify the specific element (e.g., "id=1").
        """
        try:
            query = f"UPDATE {table} SET {column} = %s WHERE {condition}"
            self.cursor.execute(query, (value,))
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"Error: {e}")

    def get_value(self, table, column, condition):
        """
        Retrieve values from a specific column in the table based on a condition.

        :param table: The table name.
        :param column: The column name to retrieve.
        :param condition: The condition to identify the specific elements (e.g., "id=1").
        :return: List of values that match the condition.
        """
        try:
            query = f"SELECT {column} FROM {table} WHERE {condition}"
            self.cursor.execute(query)
            res = [row[0] for row in self.cursor.fetchall()]
            if len(res) == 1:
                return self._php_serialize(res[0])
            else:
                raise Exception(f"error")

        except mysql.connector.Error as e:
            print(f"Error: {e}")
            return None

    def _php_serialize(self, data):
        # PHPのシリアライズデータをPythonの辞書に変換
        if isinstance(data, str):
            data = data.encode("utf-8")

        parsed_data = phpserialize.loads(data, decode_strings=True)
  
        return parsed_data

    def _php_decode(self, data):
        res = phpserialize.dumps(data).decode("utf-8")
        return res

    def close(self):
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    # Example usage
    db_manager = WordpressDatabaseManager(
        host="127.0.0.1",
        user="root",
        password="root",
        database="local",
        port=10004
    )
    try:
        res = db_manager.get_value(
            table="wp_options",
            column="option_value",
            # value="option_value",
            condition="option_name='lightning_theme_options'"
        )
        print(res)
    finally:
        db_manager.close()
