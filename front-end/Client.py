#!/usr/bin/env python3

import datetime
import random

##
## Initialization of the CouchDB server (creation of 1 collection of
## documents named "ehr", if it is not already existing)
##

import CouchDBClient

client = CouchDBClient.CouchDBClient()

# client.reset()   # If you want to clear the entire content of CouchDB

if not 'results' in client.listDatabases():
    client.createDatabase('results')


##
## Goal: Create a patient, record a few temperatures, retrieve the
## temperatures associated with the patient, and finally retrieve the
## name of all the patients stored in the CouchDB databases.
##

## 1. Create one new patient (which corresponds to an EHR in the
## framework of openEHR CDR) and associate it with a demographic
## information (i.e., patient's name)

patientID =4 # TODOOOOO patientId recovered from dicom
patientID= str(patientID)
patientName= 'Alex'
with open ('unravel_mean.json', 'r') as f:
    unravel_mean = f.read()
# TODO
# BEGIN STRIP

#create function to add pateient and results
def addPatientResult(patientID, patientName, results):
    #with open (results, 'r') as f:
    #    results = f.read()
    ResultID = client.addDocument('results', {
    'name' : patientName,
    'patientID': patientID,
    'results': results
    

})
addPatientResult(patientID, patientName, unravel_mean)



## 3. Retrieve all the temperatures that have just been stored, sorted
## by increasing time

# TODO
# BEGIN STRIP

# Fast version (install a view that "groups" results
# according to their patient ID)
client.installView('results', 'resultsView', 'by_patient_id', '''
function(doc) {
    if (doc.patientID && doc.results) {
    emit(doc.patientID, doc);
    }
}
''')
# Fast version (install a view that "groups" results
# according to their patient name)
client.installView('results', 'resultsView', 'by_patient_name', '''
function(doc) {
    if (doc.name && doc.results) {
    emit(doc.name, doc);
    }
}
''')

compositions = client.executeView('results', 'resultsView', 'by_patient_id', '3')
print(compositions)

# Only keep the content of "value" to be compatible with the slow version
compositions = list(map(lambda x: x['value'], compositions))

print(compositions)
"""
for composition in sorted(compositions, key = lambda x: x['time']):
    print('At %s: %.1f °C' % (composition['time'],
                              composition['temperature']))"""
# END STRIP
"""

## 4. Retrieve the name of all the patients stored in the database

# TODO
# BEGIN STRIP
if False:
    # Slow version (many calls to the REST API)
    compositions = []
    
    for documentId in client.listDocuments('ehr'):
        doc = client.getDocument('ehr', documentId)
        if doc['type'] == 'patient':
            compositions.append(doc)
else:
    # Fast version (install a view)
    client.installView('ehr', 'patients', 'by_patient_name', '''
    function(doc) {
      if (doc.type == 'patient') {
        emit(doc.name, doc);
      }
    }
    ''')

    compositions = client.executeView('ehr', 'patients', 'by_patient_name')

    # Only keep the content of "value" to be compatible with the slow version
    compositions = list(map(lambda x: x['value'], compositions))

for composition in compositions:
    print('Patient with ID %s is %s' % (composition['_id'], composition['name']))
# END STRIP
"""