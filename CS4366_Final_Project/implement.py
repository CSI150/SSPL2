from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import os
import shutil
import threading
import final

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'papers')
UPLOAD_SESSION_FOLDER = os.path.join(os.getcwd(), 'uploaded_files')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(UPLOAD_SESSION_FOLDER):
    os.makedirs(UPLOAD_SESSION_FOLDER)

summary_status = {'done': False}

@app.route('/')
def index():
    return render_template('file_upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file:
        filename = file.filename
        file.save(os.path.join(UPLOAD_SESSION_FOLDER, filename))
        return 'File uploaded successfully', 200
    return 'Invalid file type', 400

@app.route('/process')
def processing():
    return render_template('processing.html')

@app.route('/start_summary', methods=['POST'])
def start_summary():
    summary_status['done'] = False

    def run_summary():
        # Clear old files
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Copy files from session folder to papers
        if os.path.exists(UPLOAD_SESSION_FOLDER):
            for filename in os.listdir(UPLOAD_SESSION_FOLDER):
                src = os.path.join(UPLOAD_SESSION_FOLDER, filename)
                dest = os.path.join(UPLOAD_FOLDER, filename)
                shutil.copy2(src, dest)

        # Run summary
        final.main()
        summary_status['done'] = True

    threading.Thread(target=run_summary).start()
    return redirect(url_for('processing'))

@app.route('/check_status')
def check_status():
    return jsonify({'done': summary_status['done']})

@app.route('/completed')
def completed():
    summary_text = ""
    try:
        with open("summaries.txt", "r", encoding="utf-8") as f:
            summary_text = f.read()
    except FileNotFoundError:
        summary_text = "No summaries found."
    return render_template('completed.html', summary=summary_text)

@app.route('/my_summaries')
def my_summaries():
    summaries = []
    try:
        with open("summaries.txt", "r", encoding="utf-8") as f:
            current_topic = ""
            current_paper = ""
            for line in f:
                line = line.strip()
                if line.startswith("--- Topic"):
                    current_topic = line
                elif line.startswith("Paper:"):
                    current_paper = line
                elif line.startswith("Summary:"):
                    summary = next(f).strip()
                    summaries.append((current_topic, current_paper, summary))
    except FileNotFoundError:
        pass
    return render_template('my_summaries.html', summaries=summaries)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
