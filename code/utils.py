import shutil
import os
from main import dicomClient


# This function looks for nifti files in the data directory
def look_for_nifti_instances():
    nifti_instances = []
    nifti_paths = {}
    for root, dirs, files in os.walk('data'):
        for direc in dirs:
            file_path = os.path.join(root, direc)
            if os.path.isdir(file_path) and contains_nifti_files(file_path):
                for f in os.listdir(file_path):
                    if f.endswith('.nii.gz'):
                        nifti_instances.append(f)
                        nifti_paths[f] = (os.path.join(file_path, f))
    return nifti_instances, nifti_paths


# This function checks if a directory contains nifti files
def contains_nifti_files(filepath):
    for file in os.listdir(filepath):
        if file.endswith('.nii.gz'):
            return True


# Inspired from Practical Session 5 of course LINFO2381
def lookup_studies(patient_id, patient_name, study_description):
    answer = []

    studies = dicomClient.lookupStudies({
        '00100020': patient_id,
        '00100010': patient_name,
        '00081030': study_description,
    })

    for item in studies:
        answer.append({
            'patient-id': get_qido_rs_tag(item, 0x0010, 0x0020),
            'patient-name': get_qido_rs_tag(item, 0x0010, 0x0010),
            'study-description': get_qido_rs_tag(item, 0x0008, 0x1030),
            'study-instance-uid': get_qido_rs_tag(item, 0x0020, 0x000D),
        })

    return answer


# Inspired from Practical Session 5 of course LINFO2381

# This function extracts one tag of interest from a QIDO-RS response
# formatted in JSON. The DICOM tag must be specified by providing the
# value of its group and of its element. For instance, to extract the
# modality of a QIDO-RS result, one would write:
# "get_quido_rs_tag(json, 0x0008, 0x0060)"
def get_qido_rs_tag(json, group, element):
    tag = '%04X%04X' % (group, element)
    if tag in json:
        if json[tag]['vr'] == 'PN':
            return json[tag]['Value'][0]['Alphabetic']
        else:
            return json[tag]['Value'][0]
    else:
        return ''


# Inspired from Practical Session 5 of course LINFO2381
def lookup_series(study_instance_uid):
    answer = []

    series = dicomClient.lookupSeries({
        '0020000D': study_instance_uid,
    })

    for item in series:
        answer.append({
            'modality': get_qido_rs_tag(item, 0x0008, 0x0060),
            'series-description': get_qido_rs_tag(item, 0x0008, 0x103E),
            'series-instance-uid': get_qido_rs_tag(item, 0x0020, 0x000E),
        })

    return answer


def ensure_uploads_directory():
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)


#  Clears all files and subdirectories in the specified 'uploads' directory.
def clear_uploads_directory(directory='uploads'):
    # Check if the directory exists
    if not os.path.exists(directory):
        print(f"The directory {directory} does not exist.")
        return

    # Iterate over each item in the directory
    for item_name in os.listdir(directory):
        item_path = os.path.join(directory, item_name)

        # If it's a file, delete it
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.remove(item_path)
            print(f"Deleted file: {item_path}")
        # If it's a directory, delete the entire directory tree
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)
            print(f"Deleted directory: {item_path}")


def save_dicom_files(parts, directory):
    for index, part in enumerate(parts):
        # filepath directory/dicom_instance.dcm
        file_path = directory + '/dicom_instance' + str(index) + '.dcm'
        # if does not exist, creates the file
        with open(file_path, 'wb') as file:
            file.write(part)
            file.close()
