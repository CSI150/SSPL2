from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import uuid
import json
from datetime import datetime
import threading
from final import generate_summary  # ✅ Import the real summary function

app = Flask(__name__, static_url_path='/static')

# Configurations
UPLOAD_FOLDER = 'uploads'
SUMMARY_FOLDER = 'summaries'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SUMMARY_FOLDER'] = SUMMARY_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)

SUMMARY_DB = os.path.join(SUMMARY_FOLDER, 'summaries.json')
if not os.path.exists(SUMMARY_DB):
    with open(SUMMARY_DB, 'w') as f:
        json.dump({}, f)

def load_summaries():
    with open(SUMMARY_DB, 'r') as f:
        return json.load(f)

def save_summaries(data):
    with open(SUMMARY_DB, 'w') as f:
        json.dump(data, f)

def cleanup_old_summaries():
    data = load_summaries()
    now = datetime.now().timestamp()
    data = {k: v for k, v in data.items() if now - v['timestamp'] <= 86400}  # 24 hours
    save_summaries(data)

def background_summary(file_id, filepath):
    summary = generate_summary(filepath)  # ✅ Real processing from final.py
    data = load_summaries()
    data[file_id] = {
        'summary': summary,
        'timestamp': datetime.now().timestamp()
    }
    save_summaries(data)

@app.route('/')
def main():
    return render_template('main.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            file_id = str(uuid.uuid4())
            filename = file_id + '_' + file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            threading.Thread(target=background_summary, args=(file_id, filepath)).start()
            return redirect(url_for('processing', file_id=file_id))
    return render_template('file_upload.html')

@app.route('/processing/<file_id>')
def processing(file_id):
    return render_template('processing.html', file_id=file_id)

@app.route('/check_summary/<file_id>')
def check_summary(file_id):
    data = load_summaries()
    if file_id in data:
        return jsonify({'done': True})
    return jsonify({'done': False})

@app.route('/completed/<file_id>')
def completed(file_id):
    data = load_summaries()
    summary = data.get(file_id, {}).get('summary', 'Summary not found.')
    return render_template('completed.html', summary=summary)

@app.route('/summaries')
def summaries():
    cleanup_old_summaries()
    data = load_summaries()
    summaries_list = [v['summary'] for v in data.values()]
    return render_template('my_summaries.html', summaries=summaries_list)

if __name__ == '__main__':
    app.run(debug=True)
