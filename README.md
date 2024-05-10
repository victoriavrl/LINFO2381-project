# LINFO2381-project

## Launch Database in CouchDB
  For Windows, launch Docker Desktop
  
  docker run --rm -t -i -p 5984:5984 -e COUCHDB_USER=admin -e COUCHDB_PASSWORD=password couchdb:3.3.3

## Lauch Orthanc localhost
  For Windows, launch Docker Desktop

  docker run --rm -t -i -p 8042:8042 -p 4242:4242 jodogne/orthanc-plugins:1.12.3
