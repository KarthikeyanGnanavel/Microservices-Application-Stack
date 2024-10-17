from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
import os
from dotenv import load_dotenv
from flask_cors import CORS
import logging
from google.cloud import storage

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Enable CORS for the entire app
CORS(app)

# Access environment variables for DB app IP and port
DB_APP_IP = os.getenv('DB_APP_IP', '127.0.0.1')
DB_APP_PORT = os.getenv('DB_APP_PORT', '5001')

# Log the IP and Port to the console
print(f"Connecting to Database App at {DB_APP_IP}:{DB_APP_PORT}")

# Google Cloud Storage Configuration
BUCKET_NAME = os.getenv('GCP_BUCKET_NAME', 'docker2gcp_bucket')
GCP_SERVICE_ACCOUNT_FILE = os.getenv('GCP_SERVICE_ACCOUNT_FILE', 'docker2gcp-b80ec434f87f.json')
storage_client = storage.Client.from_service_account_json(GCP_SERVICE_ACCOUNT_FILE)


@app.route('/')
def index():
    error = session.pop('error', None)
    return render_template('login.html', error=error)


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    app.logger.debug(f"Login attempt with username: {username}, password: {password}")
    db_app_url = f'http://{DB_APP_IP}:{DB_APP_PORT}/validate'
    response = requests.post(db_app_url, json={'username': username, 'password': password})

    app.logger.debug(f"Response Status Code: {response.status_code}")
    app.logger.debug(f"Response Body: {response.text}")

    if response.status_code == 200 and response.json().get('valid'):
        session['username'] = username
        return redirect(url_for('welcome'))
    else:
        session['error'] = 'Invalid credentials, please try again.'
        return redirect(url_for('index'))


@app.route('/welcome')
def welcome():
    if 'username' not in session:
        return redirect(url_for('index'))
    username = session['username']
    return render_template('welcome.html', username=username)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('logout.html')


@app.route('/logins', methods=['GET'])
def display_logins():
    try:
        db_app_url = f'http://{DB_APP_IP}:{DB_APP_PORT}/logins'
        response = requests.get(db_app_url)
        if response.status_code == 200:
            logins = response.json()
            return render_template('logins.html', logins=logins)
        else:
            flash('Failed to fetch login entries.', 'danger')
            return redirect(url_for('welcome'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('welcome'))


# Route for File Upload
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # Upload to GCP bucket
        try:
            blob = storage_client.bucket(BUCKET_NAME).blob(file.filename)
            blob.upload_from_file(file)

            flash(f'File {file.filename} uploaded to {BUCKET_NAME}.', 'success')
            return redirect(url_for('upload_file'))
        except Exception as e:
            flash(f'Error uploading file: {str(e)}', 'danger')
            return redirect(request.url)

    return render_template('upload.html')  # Use a separate template for the upload form


# New Route to List Files from GCP Bucket
@app.route('/list-files', methods=['GET'])
def list_files():
    try:
        # Get the list of blobs in the GCP bucket
        blobs = storage_client.list_blobs(BUCKET_NAME)
        files = [blob.name for blob in blobs]

        return render_template('files.html', files=files)  # Render the files page
    except Exception as e:
        app.logger.error(f"Error listing files: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('welcome'))


# New Route for Downloading Files
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        blob = storage_client.bucket(BUCKET_NAME).blob(filename)
        url = blob.generate_signed_url(version="v4", expiration=3600)  # URL valid for 1 hour
        return redirect(url)
    except Exception as e:
        app.logger.error(f"Error downloading file: {str(e)}")
        flash(f'An error occurred while downloading: {str(e)}', 'danger')
        return redirect(url_for('list_files'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
