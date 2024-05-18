# LINFO2381-project: Interactive DICOM processing
Contributors: Alexandra Onciul (54212000), Delphine van Rossum (81352000), Quentin Dujardin (63292000), Victoria Van Rillaer (09362000)
License: MIT License

## Description

This project was developed under the scope of the LINFO2381-Health Informatics course at Université Catholique de Louvain. Its goal is to create a simple and clear web interface where the user can upload DICOM files from his computer or Orthanc. Several actions can then be performed like a conversion from DICOM to Nifti, display of DICOM or Nifti files, or basic information about Nifti files. All those actions are performed via Python. The conversion uses the tool dicom2nifti. An history of actions performes is stored via CouchDB. 


## Launch

First, check that you have a recent version of Python. Make sure to install every package listed in requirements.txt found in this project. You can install them all via this terminal command: 

	pip install -r requirements.txt

To use Orthanc and CouchDB, you need Docker installed. And Docker Studio for Windows. Please find infos on https://www.docker.com/get-started/

Then you need write two command lines in your terminal: 

### Launch Database in CouchDB
  For Windows, launch Docker Desktop
  
    docker run --rm -t -i -p 5984:5984 -e COUCHDB_USER=admin -e COUCHDB_PASSWORD=password couchdb:3.3.3

### Lauch Orthanc localhost

info: https://orthanc.uclouvain.be/book/users/docker.html#docker
  
For Windows, launch Docker Desktop

    docker run --rm -t -i -p 8042:8042 -p 4242:4242 jodogne/orthanc-plugins:1.12.3

When it is done and it runs well, open another terminal window and run the main.py via

	Python main.py

You then get two links. The first one enables you to run the Web Interface only in your computer and the second one can be run on any device under the same Wifi network. 

## Use

The left side of the interface enables the submission of DICOM files. Either via your local computer. In this case, the DICOM directory needs to be zipped and you should enter a study name. Or via Orthanc where you can search for already existing DICOM files. 

The right side is where you find the drop-down menu that list the actions. For every action needing a DICOM file, be sure to have submitted a DICOM file, and for the ones needing nifti files, you should have performed a conversion DICOM to nifti. 

On the top-left, you will find a tab "History" where your files can be retrieved either by date or name. They come with a JSON file that is downloadable. 

## Implement a new feature

To implement a new feature to the Web Interface, 3 steps have to be followed:

### 1. create your script(s)

Your new feature algorithm must be written in Python and applied on either DICOM or Niftii files. You must put your script(s) in the folder code of the project

### 2. add an option in the drop-down menu

This can be done in the index.html file found in the code/templates path. 

### 3. add a route in Flask

You must then add a function in the main.py, that will call your script. You could ignore step 1 and code directly in main.py but we do not recommend this for not small features. For the interface, you need to add a route with a @app.route just above. It should have the name you choose in index.html and do not forget to precise the Flask method. 

## Important note

If your new feature uses data from the app, there are three folders to know: the folder code/uploads will contain raw data of what is uploaded so DICOM data under the form of a zip file or directly the slices (if uploaded from Orthanc). The folder code/data/unzip will contain potential unzip DICOM files and code/data/nifti, the nifti files after conversion. 
