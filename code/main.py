from flask import Flask, redirect, url_for, render_template, request, send_file, jsonify, flash
from DICOMtoNIIconversion import convert_DICOM_to_NIfTI
import os
import nibabel as nib
import Client as client
import json
from DICOMwebClient import DICOMwebClient

app = Flask(__name__)

# Initialize the client and Couch DB
client.client_init()

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

conversion_successful = False
study_name = ""
name = "No current file uploaded"
dicomClient = DICOMwebClient()  # TODO : mettre un url specifique?

# ca sert a rien on pense cest vrai ? --> réponse de Vic : OUI, en effet
"""@app.route("/download_json", methods=["GET"])
def download_json():
    # TODO: change unravel_mean.json with the name of the json file with the result (and it's path if necessary)
    #   if it's not in a file but juste a variable with the value go see the code in the function download
    return send_file('unravel_mean.json', as_attachment=True, download_name='Result.json')


# TODO: PUT THE RIGHT FILE NAME
@app.route("/download_study_zip", methods=["GET"])
def download_study_zip():
    # TODO: change 'session-03-a-client (1).zip' with the name of the zip (and it's path if necesary)
    return send_file('session-03-a-client (1).zip', as_attachment=True, download_name='study.zip')
"""


def ensure_uploads_directory():
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)


@app.route("/", methods=["POST", "GET"])
def home():
    global conversion_successful, name
    global study_name
    ensure_uploads_directory()
    if request.method == "POST":
        study_name = request.form.get('studyName')  # Get study name
        file = request.files['file']  # Get uploaded file

        # If file is present and valid, save it temporarily and set the message
        if file and study_name:
            name = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

    return render_template('index.html', file=name)


@app.route("/history", methods=["POST", "GET"])
def history():
    dates = []
    names = []
    results = []
    times = []
    actions = []
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
            actions.append(composition[i]['action'])
        size = len(dates)

    return render_template('history.html', dates=dates, names=names, results=results, size=size, times=times,
                           actions=actions)


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


# TODO : lier au mémoire de quentin ?
@app.route('/DTI_analysis', methods=['POST'])
def perform_download_action():
    convert_DICOM_to_NIfTI("uploads", False)

    # Check if conversion was successful
    out_files = os.listdir('data/NIFTII')
    print(out_files)

    # TODO: when we have the json result from the back-end add it to couchdb with:
    # addStudyResult(name, the_json_data)
    return render_template('content.html', data=str("DTI analysis completed successfully!"))


@app.route('/nifti_conversion', methods=['POST'])
def perform_nifti_conversion():
    convert_DICOM_to_NIfTI("uploads", False)
    flash('Successful conversion', 'success')
    return render_template('index.html', file=name)


@app.route('/nifti_conversionDTI', methods=['POST'])
def perform_nifti_conversion():
    convert_DICOM_to_NIfTI("uploads", True)
    flash('Successful conversion', 'success')
    return render_template('index.html', file=name)


@app.route('/display_info')
def display_nifti_infos():
    global study_name
    out_files = os.listdir('data/NIFTII')
    if len(out_files) == 0:
        convert_DICOM_to_NIfTI("uploads", False)

    nifti_files = []
    for study in os.listdir("data/NIFTII"):
        for file in os.listdir("data/NIFTII/" + study):
            if file.endswith('.nii.gz'):
                nifti_file = os.path.join("data/NIFTII/" + study, file)
                img = nib.load(nifti_file)
                data = img.get_fdata()
                header = img.header
                affine = img.affine
                shape = data.shape
                dtype = data.dtype
                filename = os.path.basename(nifti_file)
                nifti_info = {
                    'filename': str(filename),
                    'shape': str(shape),
                    'dtype': str(dtype),
                    'zooms': str(header.get_zooms()),
                    'affine': affine.tolist()
                }
                nifti_files.append(nifti_info)
                file_name = filename.split('.')[0] + ".json"
                with open(file_name, 'w') as json_file:
                    json.dump(nifti_info, json_file, indent=4)
                client.addStudyResult(study_name, file_name,
                                      'Display NIFTII information')
                if os.path.exists(file_name):
                    os.remove(file_name)

    return render_template('display.html', nifti_files=nifti_files)


@app.route('/DICOMweb', methods=['GET', 'POST'])
def getDICOMfromWeb():
    if request.method == 'POST':
        # Get the study name and patient name from the form
        study_name = request.form.get('studyName')
        patient_name = request.form.get('patientName')

        # Perform search with study name and patient name using DICOMwebClient
        search_results = dicomClient.lookupStudies({'StudyDescription': study_name, 'PatientName': patient_name})

        return render_template('search_results.html', results=search_results)
    else:
        return render_template('dicomweb_form.html')


if __name__ == "__main__":
    app.run(debug=True)
