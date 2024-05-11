import os
import zipfile
import shutil
import platform
import pydicom


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


def conversion(filename, out):  # TODO check le os.system
    os_name = platform.system()
    librairy = ''
    if os_name == "Windows":
        librairy = 'dcm2niix.exe '
    elif os_name == "Linux":
        librairy = 'dcm2niix '
    os.system(librairy +
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


def list_subdirectories(directory):
    subdirectories = []
    # List all files and directories in the specified directory
    for item in os.listdir(directory):
        item = item.replace(".zip", "")
        subdirectories.append(item)
    return subdirectories


def convert_DICOM_to_NIfTI(root, doing_study):
    # doing_study = False
    # root = "C:/Users/quent/OneDrive/Documents/LINFO2381-project/front-end/"
    dicom_root = "uploads/"
    unzip_root = "data/UNZIP/"
    niftii_root = "data/NIFTII/"
    patient_list = "IRM_10.01.01_T2"#list_subdirectories(dicom_root)
    # study_path = create_directory(root + "/study_10")
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

    patient_list = list_subdirectories(dicom_root)
    empty_directory(unzip_root)
    empty_directory(niftii_root)

    print("empty")

    for patient in patient_list:  # patients directory
        if doing_study and not os.path.exists(study_path + "/subjects/" + patient):
            os.makedirs(study_path + "/subjects/" + patient)
        if not os.path.exists(niftii_root + "/" + patient):
            os.makedirs(niftii_root + "/" + patient)
        if not os.path.exists(unzip_root + "/" + patient):
            os.makedirs(unzip_root + "/" + patient)

    print("patient directories")

    for patient in patient_list:  # unzip
        unzip_file(dicom_root + "/" + patient + ".zip", unzip_root + "/" + patient + "/")

    print("unziping")

    for patient in patient_list:  # conversion
        for root, dirs, files in os.walk(unzip_root + patient):
            for direc in dirs:
                file_path = os.path.join(root, direc)
                if os.path.isdir(file_path) and contains_dicom_files(file_path):
                    conversion(file_path, niftii_root + "/" + patient)

    print("conversion")

    if doing_study:
        for patient in patient_list:
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
