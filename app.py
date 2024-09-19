import os
import psycopg2
from flask import Flask, request, render_template_string

app = Flask(__name__)

DATABASE_URL = os.environ['DATABASE_URL']

def get_db_connection():
    if 'localhost' in DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
    else:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Warriors News Subscription</title>
</head>
<body>
    <h1>Subscribe to Daily Warriors News Summary</h1>
    <form method="POST">
        <input type="email" name="email" required>
        <input type="submit" value="Subscribe">
    </form>
    {% if message %}
    <p>{{ message }}</p>
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def subscribe():
    message = ''
    if request.method == 'POST':
        email = request.form['email']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS subscribers (email TEXT UNIQUE)')
        try:
            cur.execute('INSERT INTO subscribers (email) VALUES (%s)', (email,))
            conn.commit()
            message = 'Subscribed successfully!'
        except psycopg2.IntegrityError:
            conn.rollback()
            message = 'You are already subscribed.'
        cur.close()
        conn.close()
    return render_template_string(HTML, message=message)

if __name__ == '__main__':
    app.run(debug=True)