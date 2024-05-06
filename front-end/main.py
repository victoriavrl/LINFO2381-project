from flask import Flask, redirect, url_for, render_template, request, send_file, jsonify
from DICOMtoNIIconversion import conversion
import os
from io import BytesIO
import nibabel as nib
import numpy as np
import Client as client
import json
import requests
from PIL import Image


app = Flask(__name__)

# Initialize the client and Couch DB
client.client_init()

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

conversion_successful = False


@app.route("/download_json", methods=["GET"])
def download_json():
    # TODO: change unravel_mean.json with the name of the json file with the result (and it's path if necesary)
    #   if it's not in a file but juste a variable with the value go see the code in the function download
    return send_file('unravel_mean.json', as_attachment=True, download_name='jsonResult.json')


# TODO: PUT THE RIGHT FILE NAME
@app.route("/download_study_zip", methods=["GET"])
def download_study_zip():
    # TODO: change 'session-03-a-client (1).zip' with the name of the zip (and it's path if necesary)
    return send_file('session-03-a-client (1).zip', as_attachment=True, download_name='study.zip')


def ensure_uploads_directory():
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)


@app.route("/", methods=["POST", "GET"])
def home():
    global conversion_successful
    ensure_uploads_directory()

    if request.method == "POST":
        study_name = request.form.get('studyName')  # Get study name
        file = request.files['file']  # Get uploaded file

        # If file is present and valid, save it temporarily and set the message
        if file and study_name:
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

            # TODO: when we have the json result from the back-end add it to couchdb with:
            # addStudyResult(name, the_json_data)

    return render_template('index.html')


@app.route("/history", methods=["POST", "GET"])
def history():
    dates = []
    names = []
    results = []
    times = []
    size = 0

    if request.method == "POST":
        # Get the study name from the form
        study_name = request.form.get('searchStudyName')

        # Get the results from the form
        time = request.form.get('searchStudyDate')

        # Add the study name and results to the database
        if time:
            composition = client.searchByDate(time)
        if study_name:
            composition = client.searchByName(study_name)
        # process the composition to get date time and result
        else:
            composition = []
        for i in range(len(composition)):
            dates.append(composition[i]['date'])
            names.append(composition[i]['name'])
            results.append(composition[i]['results'])
            times.append(composition[i]['time'])
        size = len(dates)

    return render_template('history.html', dates=dates, names=names, results=results, size=size, times=times)


@app.route("/download/<jsone>", methods=["POST", "GET"])
def download(jsone):
    # make json file from text argument
    json_string = json.dumps(jsone)
    with open('jsonResult.json', 'w') as json_file:
        json_file.write(json_string)

    return send_file('jsonResult.json', as_attachment=True, download_name='jsonResult.json')


@app.route("/content/<data>", methods=["POST", "GET"])
def showjson(data):
    json_string = json.dumps(json.loads(data), indent=4)
    return render_template('content.html', data=str(json_string))


@app.route('/DTI_analysis', methods=['POST'])
def perform_download_action():
    data = request.json
    # TODO
    # return jsonify({'message': 'Download action performed successfully'})
    return jsonify({'error': 'Invalid action'})


@app.route('/display_info')
def display_nifti_images():
    nifti_files = []
    for file in os.listdir("out"):
        if file.endswith('.nii.gz'):
            nifti_file = os.path.join("out", file)
            img = nib.load(nifti_file)
            data = img.get_fdata()
            header = img.header
            affine = img.affine
            shape = data.shape
            dtype = data.dtype
            filename = os.path.basename(nifti_file)
            nifti_files.append({
                'filename': filename,
                'shape': shape,
                'dtype': dtype,
                'zooms': header.get_zooms(),
                'affine': affine
            })

    return render_template('display.html', nifti_files=nifti_files)

if __name__ == "__main__":
    app.run(debug=True)
