from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
import os
from dotenv import load_dotenv
from flask_cors import CORS  # Import Flask-CORS
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Enable CORS for the entire app
CORS(app)  # This will allow cross-origin requests from any domain

# Access environment variables for DB app IP and port
DB_APP_IP = os.getenv('DB_APP_IP', '127.0.0.1')  # Default to localhost if not set
DB_APP_PORT = os.getenv('DB_APP_PORT', '5001')   # Default to port 5001 if not set

# Log the IP and Port to the console
print(f"Connecting to Database App at {DB_APP_IP}:{DB_APP_PORT}")

@app.route('/')
def index():
    # Check if there's a login error
    error = session.pop('error', None)
    return render_template('login.html', error=error)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    app.logger.debug(f"Login attempt with username: {username}, password: {password}")
    # Use environment variables for the db-app address
    db_app_url = f'http://{DB_APP_IP}:{DB_APP_PORT}/validate'
    response = requests.post(db_app_url, json={'username': username, 'password': password})

    # Log the response status code and body
    app.logger.debug(f"Response Status Code: {response.status_code}")
    app.logger.debug(f"Response Body: {response.text}")  # or response.json() if it's JSON

    if response.status_code == 200 and response.json().get('valid'):
        # Set the username in session and redirect to the welcome page on success
        session['username'] = username
        return redirect(url_for('welcome'))
    else:
        # Flash error message and redirect back to login page if credentials are invalid
        session['error'] = 'Invalid credentials, please try again.'
        return redirect(url_for('index'))

@app.route('/welcome')
def welcome():
    # Get the username from session
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirect to login if not logged in
    username = session['username']
    return render_template('welcome.html', username=username)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('logout.html')

@app.route('/logins', methods=['GET'])
def display_logins():
    """Fetches and displays all login entries."""
    try:
        # Use environment variables for the db-app address
        db_app_url = f'http://{DB_APP_IP}:{DB_APP_PORT}/logins'
        response = requests.get(db_app_url)  # Call the endpoint to get logins
        if response.status_code == 200:
            logins = response.json()  # Assuming the response returns a list of user data
            return render_template('logins.html', logins=logins)
        else:
            flash('Failed to fetch login entries.', 'danger')
            return redirect(url_for('welcome'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('welcome'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
