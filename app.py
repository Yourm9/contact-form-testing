from flask import Flask, request, jsonify, render_template
import csv, os, subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULTS_FILE = 'results.csv'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_bot():
    urls = []

    # 1. If manual input is present
    if request.form.get("manual") == "true":
        raw = request.form.get("urls", "")
        urls = [line.strip() for line in raw.splitlines() if line.strip()]

    # 2. Else, process CSV file
    elif 'file' in request.files:
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            content = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(content)
            urls = [row['url'].strip() for row in reader if 'url' in row]

    # 3. Run bot logic
    results = []
    for url in urls:
        status = "Success"  # 🔁 Replace with real automation logic
        results.append({"url": url, "status": status})

    return jsonify(results)


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)