import os
from dotenv import load_dotenv
from get_warriors_news import main as news_main
from app import app, get_db_connection

# Load environment variables
load_dotenv()

def setup_test_database():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS subscribers (email TEXT UNIQUE)')
    cur.execute('INSERT INTO subscribers (email) VALUES (%s) ON CONFLICT DO NOTHING', ('test@example.com',))
    conn.commit()
    cur.close()
    conn.close()

def test_news_script():
    print("Testing news script...")
    news_main()

def test_web_app():
    print("Testing web app...")
    client = app.test_client()
    response = client.get('/')
    print(f"GET /: {response.status_code}")
    response = client.post('/', data={'email': 'new_user@example.com'})
    print(f"POST /: {response.status_code}")
    print(response.get_data(as_text=True))

if __name__ == "__main__":
    setup_test_database()
    test_news_script()
    test_web_app()