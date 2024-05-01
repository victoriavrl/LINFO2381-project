from flask import Flask, redirect, url_for, render_template, request, send_file
from DICOMtoNIIconversion import conversion
import os
import Client as client
app = Flask(__name__)

# Define a folder to store the uploaded files temporarily
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global variable to track conversion status
#TODO: PUT THE RIGHT FILE NAME
conversion_successful = False
@app.route("/download_json", methods=[ "GET"])
def download_json():
    return send_file('unravel_mean.json', as_attachment=True,download_name='jsonResult.json')
#TODO: PUT THE RIGHT FILE NAME
@app.route("/download_study_zip", methods=[ "GET"])
def download_study_zip():
    return send_file('session-03-a-client (1).zip', as_attachment=True,download_name='study.zip')


@app.route("/", methods=["POST", "GET"])
def home():
    global conversion_successful
    message = None  # Initialize message variable

    if request.method == "POST":
        # Check if the POST request has a file part
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        # If the user does not select a file, the browser submits an empty file without a filename
        if file.filename == '':
            return redirect(request.url)

        # If file is present and valid, save it temporarily and set the message
        if file:

            # Save the file temporarily
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # Call the conversion function with the file path
            conversion(file_path)

            # Check if conversion was successful
            out_files = os.listdir('out')
            if not out_files:
                conversion_successful = False  # Conversion failed
            else:
                conversion_successful = True  # Conversion successful

            # Delete the temporary file after conversion
            os.remove(file_path)

    return render_template('index.html')


@app.route("/history", methods=["POST", "GET"])
def history():
    return render_template('history.html')


if __name__ == "__main__":
    app.run(debug=True)
