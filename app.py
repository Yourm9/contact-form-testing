from flask import Flask, request, jsonify, render_template
import csv, os
from werkzeug.utils import secure_filename
from bot import smart_contact_form_submitter

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run_bot():
    print("📥 Received POST request to /run")
    urls = []

    if 'file' not in request.files:
        print("❌ No file part in request")
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == '':
        print("❌ No file selected")
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    print(f"💾 File saved to: {filepath}")

    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        if 'url' not in reader.fieldnames:
            print("❌ CSV missing 'url' column")
            return jsonify({"error": "CSV must contain a 'url' column"}), 400
        urls = [row['url'] for row in reader if row.get('url')]

    print(f"🔗 URLs extracted: {urls}")

    results = []
    for url in urls:
        try:
            print(f"🚀 Submitting form on: {url}")
            status = smart_contact_form_submitter(url)
        except Exception as e:
            status = f"Error: {str(e)}"
            print(f"❌ Failed on {url}: {status}")
        results.append({"url": url, "status": status})
        print(f"✅ Result: {url} -> {status}")

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
