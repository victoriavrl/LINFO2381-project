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


Name= 'Alex'# TODOOOOO studyname recovered from flask
with open ('unravel_mean.json', 'r') as f:
    unravel_mean = f.read()
# TODO
# BEGIN STRIP

#create function to add pateient and results
def addStudyResult(StudyName ,results):
    #with open (results, 'r') as f:
    #    results = f.read()
    StudyDate = datetime.datetime.now().isoformat()
    ResultID = client.addDocument('results', {
    'name' : StudyName,
    'date': StudyDate,
    'results': results
    

})
addStudyResult(Name, unravel_mean)




# TODO
# BEGIN STRIP

# Fast version (install a view that "groups" results
# according to their patient ID)
client.installView('results', 'resultsView', 'by_study_name', '''
function(doc) {
    if (doc.name && doc.results) {
    emit(doc.name, doc);
    }
}
''')
# Fast version (install a view that "groups" results
# according to their patient name)
client.installView('results', 'resultsView', 'by_time', '''
function(doc) {
    if (doc.date && doc.results) {
    emit(doc.date, doc);
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