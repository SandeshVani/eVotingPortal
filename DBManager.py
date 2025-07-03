import pymysql
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseManager:
    def __init__(self, user, password, host, database):
        self.user = user
        self.password = password
        self.host = host
        self.database = database

    def connect(self):
        return pymysql.connect(
            user=self.user,
            password=self.password,
            host=self.host,
            database=self.database,
            cursorclass=pymysql.cursors.DictCursor
        )

    def fetch(self, query, parameters=None):
        connection = None
        try:
            connection = self.connect()

            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchall()
                return result

        except pymysql.Error as e:
            logging.error(f"Error while fetching data: {e}", exc_info=True)
            return None

        finally:
            if connection:
                connection.close()

    def update(self, query, parameters=None):
        connection = None
        try:
            connection = self.connect()

            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                connection.commit()
                return True

        except pymysql.Error as e:
            logging.error(f"Error while updating data: {e}", exc_info=True)
            return False

        finally:
            if connection:
                connection.close()
                
