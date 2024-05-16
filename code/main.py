import pydicom
from matplotlib import pyplot as plt
from nilearn import plotting
from flask import Flask, render_template, request, send_file, flash, Response, session
from DICOMtoNIIconversion import convert_DICOM_to_NIfTI, unzip_file
import nibabel as nib
import Client as client
import json
from DICOMwebClient import DICOMwebClient
import matplotlib
from utils import *

matplotlib.use('TkAgg')

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "secret key"

# Initialize the clients for Couch DB and DICOMweb
client.client_init()
dicomClient = DICOMwebClient('https://orthanc.uclouvain.be/demo/dicom-web')

# Global variables
conversion_successful = False
study_name = ""
name = "No current file uploaded"


@app.route("/", methods=["POST", "GET"])
def home():
    global name, study_name
    ensure_uploads_directory()
    if request.method == "POST":
        clear_uploads_directory()
        clear_uploads_directory('data/NIFTII')
        clear_uploads_directory('data/UNZIP')
        session['study_name'] = request.form.get('studyName')  # Get study name
        file = request.files['file']  # Get uploaded file

        # If file is present and valid, save it temporarily and set the message
        if file and session['study_name']:
            name = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            unzip_file(file_path, 'data/UNZIP')
        elif not study_name:
            flash("Please provide a study name and retry.")
        elif not file:
            flash("Please provide a file and retry.")
        flash("File uploaded successfully.")
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
        studyName = request.form.get('searchStudyName')

        # Get the results from the form
        time = request.form.get('searchStudyDate')
        # Add the study name and results to the database
        if time:
            composition = client.searchByDate(time)
        elif studyName:
            composition = client.searchByName(studyName)
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


@app.route("/download/<json>", methods=["POST", "GET"])
def download(json):
    # make json file from text argument
    json_string = json.dumps(json)
    with open('jsonResult.json', 'w') as json_file:
        json_file.write(json_string)

    return send_file('jsonResult.json', as_attachment=True, download_name='jsonResult.json')


@app.route("/content/<data>", methods=["POST", "GET"])
def showjson(data):
    json_string = json.dumps(json.loads(data), indent=4)
    return render_template('content.html', data=str(json_string))


@app.route('/nifti_conversion', methods=['GET'])
def perform_nifti_conversion():
    try:
        convert_DICOM_to_NIfTI("uploads", False)
        i = look_for_nifti_instances()
        if len(i) == 0:
            flash('Error during conversion. Please verify the content of your files.', 'error')
        else:
            flash('Successful conversion', "error")
    except Exception as e:
        flash('Error during conversion. Please verify the content of your files.', 'error')
    return render_template('displayflash.html', file=study_name)


@app.route('/nifti_conversionDTI', methods=['GET'])
def perform_nifti_conversionDTI():
    try:
        if len(os.listdir('data/NIFTII' + name)) == 0:
            convert_DICOM_to_NIfTI("uploads", True)
            flash('Error during conversion. Please verify the content of your files.', 'error')
        else:
            flash('Successful conversion')
    except Exception as e:
        flash('Error during conversion. Please verify the content of your files.', 'error')
    return render_template('displayflash.html', file=name)


@app.route('/display_info')
def display_nifti_infos():
    global study_name
    try:
        nifti_files = []
        inst, paths = look_for_nifti_instances()
        paths = paths.values()
        for path in paths:
            nifti_file = path
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
            nifti_info_json = json.dumps(nifti_info)
            client.addStudyResult(study_name, nifti_info_json, 'Display NIFTII information')
    except Exception as e:
        print(e)
        flash('Error during displaying information. Are you sure your files are the correct format (nii) ?',
              'error')
        return render_template('index.html', study=study_name)
    return render_template('display.html', nifti_files=nifti_files)


@app.route('/DICOMweb', methods=['GET', 'POST'])
def getDICOMfromWeb():
    global study_name, name
    return render_template('dicomweb_form.html', study=study_name)


studies_uids = {}


@app.route('/search_studies', methods=['POST'])
def search_studies():
    if request.method == 'POST':
        patient_id = request.form.get('patientID')
        patient_name = request.form.get('patientName')
        study_description = request.form.get('studyDescription')
        search_results = lookup_studies(patient_id, patient_name, study_description)
        results = []
        for study1 in search_results:
            text = study1['patient-id'] + ' - ' + study1['patient-name'] + ' - ' + study1['study-description']
            results.append(text)
            studies_uids[text] = study1['study-instance-uid']
        return render_template('dicomweb_form.html', studies=results, study=study_name)


instances = {}
study = ''


@app.route('/getSeries', methods=['POST'])
def getSeries():
    global study, study_name
    if request.method == 'POST':
        study_txt = request.form.get('Study')
        study_name = study_txt
        study_instance_uid = studies_uids[study_txt]
        study = study_instance_uid
        search_results = lookup_series(study_instance_uid)
        results = []
        for series in search_results:
            text = series['modality'] + ' - ' + series['series-description']
            results.append(text)
            instances[text] = series['series-instance-uid']
        return render_template('dicomweb_form.html', series=results, study=study_name)


series = ''
orthanc = False


@app.route('/download_dicom', methods=['POST'])
def download_dicom():
    global series
    if request.method == 'POST':
        clear_uploads_directory()
        clear_uploads_directory('data/NIFTII')
        clear_uploads_directory('data/UNZIP')
        series_txt = request.form.get('Serie')
        series_instance_uid = instances[series_txt]
        series = series_instance_uid
        d = dicomClient.downloadInstancesOfSeries(study, series_instance_uid)
        save_dicom_files(d, 'uploads')
        flash('DICOM files downloaded successfully', 'success')
        infos = {"study": study, "series": series}
        info_json = json.dumps(infos)
        client.addStudyResult(study_name, info_json, 'Dowload DICOM files')
        orthanc = True
        return render_template('index.html', file=study_name)


instances_glob = []


@app.route('/show_dicom', methods=['GET', 'POST'])
def show_dicom():
    global study, series, instances_glob
    if request.method == 'POST':
        try:
            instance = request.form.get("dicomSelector")
            if orthanc:
                pngImage = dicomClient.getRenderedInstance(study, series, instance, False)
                infos = {"study": study, "series": series, "instance": instance}
                info_json = json.dumps(infos)
                client.addStudyResult(study_name, info_json, 'Display DICOM image')
                with open('static/image.png', 'wb') as f:
                    f.write(pngImage)
            else:
                d = os.listdir('data/UNZIP')
                if os.path.isdir('data/UNZIP/' + d[0]):
                    pixel_data = pydicom.dcmread('data/UNZIP/' + d[0] + '/' + instance).pixel_array
                else:
                    pixel_data = pydicom.dcmread('data/UNZIP/' + instance).pixel_array
                plt.imshow(pixel_data, cmap=plt.cm.bone)
                plt.axis('off')
                plt.savefig('static/image.png', bbox_inches='tight', pad_inches=0)
                plt.close()
        except Exception as e:
            print(e)
            flash('Error during displaying DICOM file', 'error')
        return render_template('show_dicom.html', lists=instances_glob, i=instance)
    else:
        if study != '' or series != '':
            try:
                instances_glob = dicomClient.listInstances(study, series)
                return render_template('show_dicom.html', lists=instances_glob)
            except Exception as e:
                print("Error:", e)  # Print the error for debugging
                return Response("Internal Server Error", status=500)
        elif len(os.listdir('data/UNZIP')) > 0:
            d = os.listdir('data/UNZIP')
            inst = os.listdir('data/UNZIP/' + d[0])
            instances_glob = [file for file in inst if file.endswith('.dcm')]
            return render_template('show_dicom.html', lists=instances_glob)
        else:
            flash('You didn\'t download any DICOM file. Please select or upload DICOM files and retry.', 'error')
            return render_template('index.html')


@app.route('/show_nifti', methods=['GET', 'POST'])
def show_nifti():
    niftis, paths = look_for_nifti_instances()
    if len(niftis) == 0:
        flash("There isn't any NIFTI file selected. Please upload a NIFTI file and retry.", 'error')
        return render_template('index.html')
    try:
        instance = request.form.get("niftiSelector")
        p = paths[instance]
        pngImage = plotting.plot_img(nib.load(p))
        pngImage.savefig('static/image_nifti.png')
        nifti_info = {"nifti": instance, "path": p}
        nifti_info_json = json.dumps(nifti_info)
        client.addStudyResult(study_name, nifti_info_json, 'Display NIFTII image')
    except Exception as e:
        flash("There was an error during the display of your NIFTII files. Either the files are too heavy or you "
              "didn't upload any files.", 'error')
    return render_template('show_nifti.html', lists=niftis)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
