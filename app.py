from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import csv, os
from werkzeug.utils import secure_filename
from bot import smart_contact_form_submitter

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'supersecretkey'

ENABLE_LOGIN = True
USERNAME = "admin"
PASSWORD = "test123"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    if ENABLE_LOGIN and not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if not ENABLE_LOGIN:
        return redirect(url_for("index"))
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login" if ENABLE_LOGIN else "index"))

@app.route("/run", methods=["POST"])
def run_bot():
    if ENABLE_LOGIN and not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        if 'url' not in reader.fieldnames:
            return jsonify({"error": "CSV must contain a 'url' column"}), 400
        urls = [row['url'] for row in reader if row.get('url')]

    results = []
    for url in urls:
        try:
            result = smart_contact_form_submitter(url)
            status = result.get("status", "Unknown")
            message = ", ".join(result.get("fields_filled", [])) if isinstance(result, dict) else ""
        except Exception as e:
            status = f"Error: {str(e)}"
            message = ""

        results.append({
            "url": url,
            "status": status,
            "message": message
        })

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5090)
