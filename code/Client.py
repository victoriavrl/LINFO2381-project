#!/usr/bin/env python3

#docker run --rm -t -i -p 5984:5984 -e COUCHDB_USER=admin -e COUCHDB_PASSWORD=password couchdb:3.3.3

import datetime
import random

##
## Initialization of the CouchDB server (creation of 1 collection of
## documents named "ehr", if it is not already existing)
##

import CouchDBClient
def addStudyResult(StudyName , results, action):
    #with open (results, 'r') as f:
    #    results = f.read()
    StudyDate = datetime.datetime.now().date().isoformat()
    StudyTime = datetime.datetime.now().time().isoformat()[:5]
    ResultID = client.addDocument('results', {
    'name' : StudyName,
    'date': StudyDate,
    'results': results,
    'time': StudyTime,
    'action': action
    

})
client=None
def client_init():
    global client
    client= CouchDBClient.CouchDBClient()

    #client.reset()   # If you want to clear the entire content of CouchDB
    if not 'results' in client.listDatabases():
        client.createDatabase('results')
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

client_init()


Name= 'Alex'
with open ('unravel_mean.json', 'r') as f:
    unravel_mean = f.read()

# function to add  results
addStudyResult(Name, unravel_mean, 'unravel')

#function to add to database
def addmultipleResults():
    with open ('unravel_mean.json', 'r') as f:
            unravel_mean = f.read()
    for i in range(10):
        Name= 'Alex'+str(i)
        addStudyResult(Name, unravel_mean,'test')

#TODO :To add artificial results to the database
#addmultipleResults()



def searchByName(name):
    compositions = client.executeView('results', 'resultsView', 'by_study_name', name)
    compositions = list(map(lambda x: x['value'], compositions))
    return compositions

def searchByDate(date):
    compositions = client.executeView('results', 'resultsView', 'by_time', date)
    compositions = list(map(lambda x: x['value'], compositions))
    
    return compositions
