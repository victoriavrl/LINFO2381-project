from flask import Flask, render_template, request
from DICOMtoNIIconversion import conversion
import time

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    message = None

    if request.method == "POST":
        if 'file' not in request.files:
            return "No file part", 400

        file = request.files['file']

        if file.filename == '':
            return "No selected file", 400

        # Set message to be displayed
        message = "Archive soumise"

        # Perform conversion and yield progress
        progress_generator = conversion(file)

        # Update progress in real-time
        for progress in progress_generator:
            time.sleep(0.1)  # Adjust this to control the update rate of the progress bar

    return render_template("index.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)
