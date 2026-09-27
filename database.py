import psycopg
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    return psycopg.connect(
        host="localhost",
        dbname="postgres",
        user="postgres",
        password=os.getenv("POSTGRES_PASSWORD"),
        port=5432
    )
def save_checkin(patient_id, pain_lvl, symptomps, medication_taken, weight, missed_reason):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO checkins (pataint_id, pain_lvl, symptomps, medication_taken, weight, missed_reason)
        VALUES (%s, %s, %s, %s, %s, %s)""",
        (patient_id, pain_lvl, symptomps, medication_taken, weight, missed_reason),
    )
    conn.commit()
    cur.close()
    conn.close()
    
def fetch_history(patient_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT pain_lvl, symptomps, medication_taken, weight, missed_reason FROM checkins WHERE pataint_id = %s ORDER BY checkin_date", (patient_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    history = []
    for row in rows:
        history.append({
            "pain_lvl": row[0],
            "symptomps": row[1],
            "medication_taken": row[2],
            "weight": row[3],
            "missed_reason": row[4]
        }) 
    return history
    
    