import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from loguru import logger
import json

load_dotenv()

db_name = os.getenv('POSTGRES_DB')
db_user = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWORD')
db_host = os.getenv('POSTGRES_HOST')
db_port = os.getenv('POSTGRES_PORT')

if not all([db_name, db_user, db_password, db_host, db_port]):
    logger.error("""One or more required
                    environment variables are not set or empty.""")
    exit(1)


# Configure logger
def serialize(record):
    subset = {
        "timestamp": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "message": record["message"],
        "level": record["level"].name,
        "function": record["function"],
        "line": record["line"],
        "file": record["file"].name,
        "module": record["module"]
    }
    return json.dumps(subset)


def patching(record):
    record["extra"]["serialized"] = serialize(record)


conn = psycopg2.connect(
            database=db_name,
            user=db_user, password=db_password,
            host=db_host, port=db_port)

cur = conn.cursor(cursor_factory=RealDictCursor)


def insertstudent(data: dict):
    try:
        insert_query = """INSERT INTO students (name, email, age, phone)
                        VALUES (%s, %s, %s, %s) RETURNING ID;"""
        cur.execute(insert_query, (data.name, data.email,
                                   data.age, data.phone))
        student_id = cur.fetchone()
        conn.commit()
        return {"status": "success", "message":
                "Student inserted successfully", "student_id": student_id}
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f'error:"{str(e)}')
        return {"status": "error", "message":
                "An unexpected error occurred. Please contact support."}


def get_all_students():
    try:
        select_query = """
        SELECT * from  students;
        """
        cur.execute(select_query)
        students = cur.fetchall()
        conn.commit()
        if len(students) > 0 or students is None:
            return {"status": "success", "message":
                    "Student inserted successfully", "students": students}
        else:
            return {"status": "error", "message": "No Data Present"}
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f'error:"{str(e)}')
        return {"status": "error", "message":
                "An unexpected error occurred. Please contact support."}


def get_student_by_Id(id):
    try:
        select_query = """
        SELECT * FROM students WHERE ID = %s;
        """
        cur.execute(select_query, (id,))
        students = cur.fetchone()
        conn.commit()
        if students is not None:
            return {"status": "success", "students": students}
        else:
            return {"status": "error", "message": "No Data found"}
    except Exception as e:
        # Catch Unexpected Errors
        logger.error(f"Unexpected error: {e}")
        return {"status": "error", "message":
                "An unexpected error occurred. Please contact support."}


def Update_student(id, student):
    try:
        update_fields = []
        update_values = []

        if student.name is not None and student.name != "":
            update_fields.append("name = %s")
            update_values.append(student.name)
        if student.email is not None and student.email != "":
            update_fields.append("email = %s")
            update_values.append(student.email)
        if student.age is not None and student.email != "":
            update_fields.append("age = %s")
            update_values.append(student.age)
        if student.phone is not None and student.email != "":
            update_fields.append("phone = %s")
            update_values.append(student.phone)

        if not update_fields:
            logger.warning("No fields provided for update")
            return {"status": "error", "message":
                    "Please provide at least one field to update."}

        update_values.append(id)
        update_query = f'''UPDATE students SET {', '.join(update_fields)}
        WHERE id = %s;'''
        cur.execute(update_query, update_values)
        conn.commit()
        rows_affected = cur.rowcount
        if rows_affected > 0:
            return {"status": "success", "message": "Data is updated"}
        else:
            return {"status": "error", "message": "No Data found"}

    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f'error:"{str(e)}')
        return {"status": "error", "message":
                "An unexpected error occurred. Please contact support."}


def delete_student(id):
    try:
        delete_query = """
        DELETE FROM students WHERE Id = %s;
        """
        cur.execute(delete_query, (id, ))
        if cur.rowcount > 0:
            conn.commit()
            return {"status": "success", "message":
                    "Student deleted successfully"}
        else:
            return {"status": "error", "message": "Student not found"}
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Database error: {str(e)}")
        return {"status": "error", "message":
                "An unexpected error occurred. Please contact support."}
