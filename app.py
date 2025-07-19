
from flask import Flask, request, redirect, url_for, send_from_directory, jsonify
from flask import render_template
import os
from werkzeug.utils import secure_filename
import json
from flask_cors import CORS
import os

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
