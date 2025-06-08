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
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    subprocess.run(['python3', 'bot.py', filepath], capture_output=True, text=True)

    results = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append({
                    "url": row.get("url", "N/A"),
                    "status": row.get("status", "Unknown")
                })
    return jsonify(results)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
