import os
import zipfile
import shutil
import platform
import pydicom


# Checks if the directory contains zip files
def check_for_zip_files(directory):
    # List all files in the directory
    files = os.listdir(directory)

    # Filter files to find those ending with '.zip'
    zip_files = [file for file in files if file.endswith('.zip')]

    # Check if there are any zip files
    if zip_files:
        return True
    else:
        return False


# Checks if the directory contains dicom files
def contains_dicom_files(directory):
    print(directory)
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            print(filepath)
            try:
                with pydicom.dcmread(filepath):
                    return True
            except pydicom.errors.InvalidDicomError:
                pass
    return False


# Delete all files and directories within the specified directory
def empty_directory(directory):
    try:
        # Recursively remove all files and directories within the specified directory
        for root, dirs, files in os.walk(directory, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                shutil.rmtree(os.path.join(root, dir))

        # Check if the directory is empty
        if not os.listdir(directory):
            print(f"Directory '{directory}' emptied successfully.")
        else:
            print(f"Directory '{directory}' is not empty.")

        # Check permission to delete files
        test_file = os.path.join(directory, ".test_file")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print("Permission to delete files: Yes")

    except PermissionError:
        print("Permission denied to delete files.")
    except Exception as e:
        print(f"Error occurred: {e}")


# Rename a file
def rename(old_name, new_name):
    try:
        # Split the file name and extension
        file_name, file_extension = os.path.splitext(old_name)

        # Concatenate the new name with the original extension
        new_file_name = new_name + file_extension

        # Rename the file
        os.rename(old_name, new_file_name)

        print(f"File '{old_name}' renamed to '{new_file_name}' successfully.")
    except Exception as e:
        print(f"Error occurred: {e}")


def unzip_file(zip_file, extract_to):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(extract_to)


def move_file(source, destination):
    try:
        shutil.move(source, destination)
        print(f"File moved successfully from '{source}' to '{destination}'.")
    except Exception as e:
        print(f"Error occurred: {e}")


# Convert DICOM files to NIfTI format with dcm2niix
def conversion(filename, out):
    os_name = platform.system()
    library = ''
    # The library is different according to the operating system
    if os_name == "Windows":
        library = 'dcm2niix.exe '
    elif os_name == "Linux":
        library = 'dcm2niix '
    os.system(library +
              '-f %f_%d_%t ' +
              '-b y ' +
              '-d 9 ' +
              '-p n ' +
              '-z y ' +
              '-ba y ' +
              '-w 2 ' +
              '-o ' + out + " " +
              filename + '/')


def create_directory(directory):
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist. Creating it.")
        os.makedirs(directory)
    else:
        print(f"Directory '{directory}' already exists.")
        # Optionally, create a new directory within the existing directory
        new_directory = os.path.join(directory, "new_directory")
        if not os.path.exists(new_directory):
            print(f"Creating a new directory '{new_directory}'.")
            os.makedirs(new_directory)
        else:
            print(f"New directory '{new_directory}' already exists.")
    return directory + "/"


# List all files and directories in the specified directory
def list_subdirectories(directory):
    subdirectories = []
    for item in os.listdir(directory):
        item = item.replace(".zip", "")
        subdirectories.append(item)
    return subdirectories


def convert_DICOM_to_NIfTI(root, doing_study):
    """
    Converts DICOM files to NIfTI format according to the study type
    :param root: the root directory of the study
    :param doing_study: doing the conversion for DTI analysis or not
    """
    dicom_root = "uploads/"
    unzip_root = "data/UNZIP/"
    niftii_root = "data/NIFTII/"
    if doing_study:
        study_path = root + "/study_10/"
        if not os.path.exists(study_path):
            os.makedirs(study_path)

        print("study directory")
        if not os.path.exists(study_path + "/data_1"):
            os.makedirs(study_path + "/data_1")
        else:
            empty_directory(study_path + "/data_1")

        if not os.path.exists(study_path + "/data_T1"):
            os.makedirs(study_path + "/data_T1")
        else:
            empty_directory(study_path + "/data_T1")

        if not os.path.exists(study_path + "/data_T2"):
            os.makedirs(study_path + "/data_T2")
        else:
            empty_directory(study_path + "/data_T2")

        if not os.path.exists(study_path + "/subjects"):
            os.makedirs(study_path + "/subjects")

    print("all subdirectories")

    empty_directory(unzip_root)
    empty_directory(niftii_root)

    print("empty")

    if doing_study and not os.path.exists(study_path + "/subjects/"):
        os.makedirs(study_path + "/subjects/")
    if not os.path.exists(niftii_root):
        os.makedirs(niftii_root)
    if not os.path.exists(unzip_root):
        os.makedirs(unzip_root)

    print("patient directories")

    dicom_files = os.listdir(dicom_root)
    print("1")
    patient = dicom_files[0]
    print("2")
    if check_for_zip_files(dicom_root):
        print("3")
        unzip_file(dicom_root + "/" + patient, unzip_root)

    print("unziping")

    if contains_dicom_files(dicom_root):
        conversion(dicom_root, niftii_root)
    for root, dirs, files in os.walk(unzip_root):
        for direc in dirs:
            file_path = os.path.join(root, direc)
            if os.path.isdir(file_path) and contains_dicom_files(file_path):
                conversion(file_path, niftii_root)

    print("conversion")

    if doing_study:
        fichiers = os.listdir(niftii_root + "/" + patient)
        for fichier in fichiers:
            print(fichier)
            if 'T1' in fichier:
                print("T1")
                move_file(niftii_root + patient + "/" + fichier, study_path + "/data_T1")
                rename(study_path + "/data_T1/" + fichier, study_path + "/data_T1/" + patient + "_T1")

            elif 'T2' in fichier:
                print("T2")
                move_file(niftii_root + patient + "/" + fichier, study_path + "/data_T2")
                rename(study_path + "/data_T2/" + fichier, study_path + "/data_T2/" + patient + "_T2")

            elif 'DTI' in fichier:
                print("DTI")
                move_file(niftii_root + patient + "/" + fichier, study_path + "/data_1")
                rename(study_path + "/data_1/" + fichier, study_path + "/data_1/" + patient + "_DTI")
