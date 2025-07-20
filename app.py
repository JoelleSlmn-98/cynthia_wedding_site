
from flask import Flask, request, redirect, url_for, send_from_directory, jsonify
from flask import render_template
import os
from flask import send_file
import io
import zipfile

from werkzeug.utils import secure_filename
import json
from flask_cors import CORS
import os
from flask import send_file
import io
import zipfile


app = Flask(__name__)
CORS(app)
COMMENTS_FILE = 'comments.json'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'mkv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        return jsonify({'success': True, 'filename': filename}), 200
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/list')
def list_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return jsonify(files)

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/<path:filename>')
def serve_static_file(filename):
    return send_from_directory('static', filename)

@app.route('/comments/<filename>', methods=['GET'])
def get_comments(filename):
    comments = load_comments()
    return jsonify(comments.get(filename, []))

@app.route('/comments/<filename>', methods=['POST'])
def post_comment(filename):
    comments = load_comments()
    data = request.json
    name = data.get('name')
    text = data.get('comment')
    if not name or not text:
        return jsonify({'error': 'Invalid input'}), 400
    comments.setdefault(filename, []).append({'name': name, 'comment': text})
    save_comments(comments)
    return jsonify({'success': True})

def load_comments():
    if not os.path.exists(COMMENTS_FILE):
        return {}
    with open(COMMENTS_FILE, 'r') as f:
        return json.load(f)

def save_comments(data):
    with open(COMMENTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
        
@app.route('/comments/<filename>', methods=['GET', 'POST'])
def comments(filename):
    if not os.path.exists(COMMENTS_FILE):
        with open(COMMENTS_FILE, 'w') as f:
            json.dump({}, f)

    with open(COMMENTS_FILE, 'r') as f:
        all_comments = json.load(f)

    if request.method == 'POST':
        data = request.get_json()
        all_comments.setdefault(filename, []).append({
            'name': data['name'],
            'comment': data['comment']
        })
        with open(COMMENTS_FILE, 'w') as f:
            json.dump(all_comments, f, indent=2)
        return jsonify(success=True)

    return jsonify(all_comments.get(filename, []))


@app.route('/download-all')
def download_all():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(filepath):
                zf.write(filepath, arcname=filename)
    zip_buffer.seek(0)
    return send_file(zip_buffer, as_attachment=True, download_name='wedding-gallery.zip', mimetype='application/zip')


@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    data = request.get_json()
    password = data.get('password')
    if password != 'your_password_here':
        return jsonify({'error': 'Unauthorized'}), 403
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        os.remove(path)
        comments = load_comments()
        comments.pop(filename, None)
        save_comments(comments)
        return jsonify({'success': True}), 200
    return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
