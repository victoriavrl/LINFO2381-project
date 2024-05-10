#!/usr/bin/env python3

# Copyright (c) 2024, Sebastien Jodogne, ICTEAM UCLouvain, Belgium
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import PIL.Image
import email
import io
import requests
import requests.auth
import uuid

_STUDY_INSTANCE_UID = '0020000D'
_SERIES_INSTANCE_UID = '0020000E'
_SOP_INSTANCE_UID = '00080018'

# Class that represents a connection to some DICOMweb server
class DICOMwebClient:

    # Constructor for the connection: An URL, an username, and a
    # password are expected. The default credentials correspond to an
    # Orthanc server started using the following command:
    #
    #   $ docker run --rm -t -i -p 8042:8042 -p 4242:4242 jodogne/orthanc-plugins:1.12.3
    #
    def __init__(self,
                 url = 'http://localhost:8042/dicom-web',
                 username = 'orthanc',
                 password = 'orthanc'):
        # Make sure that the URL does not end with a slash
        if url.endswith('/'):
            self.url = url[0 : len(url) - 1]
        else:
            self.url = url

        self.username = username
        self.password = password

    def _getAuthentication(self):
        return requests.auth.HTTPBasicAuth(self.username, self.password)

    def _parseMultipart(self, r):
        with io.BytesIO() as f:
            for (key, value) in r.headers.items():
                f.write(('%s: %s\n' % (key, value)).encode('utf-8'))
            f.write(b'\n')
            f.write(r.content)
            f.seek(0)
            msg = email.message_from_bytes(f.read())

        parts = []

        for i, part in enumerate(msg.walk(), 1):
            content = part.get_payload(decode = True)
            if content != None:
                parts.append(content)

        return parts

    def _sendMultipart(self, url, parts, mime, accept = None):
        # Create a multipart message whose body contains all the input "parts"
        boundary = str(uuid.uuid4())  # The boundary is a random UUID

        with io.BytesIO() as f:
            for i in range(len(parts)):
                header = ('--%s\r\n' % boundary +
                          'Content-Length: %d\r\n' % len(parts[i]) +
                          'Content-Type: %s\r\n\r\n' % mime)
                f.write(header.encode('ascii'))
                f.write(parts[i])
                f.write(b'\r\n')

            f.seek(0)
            body = f.read()

        headers = {
            'Content-Type' : 'multipart/related; type="%s"; boundary=%s' % (mime, boundary),
        }

        if accept != None:
            headers['Accept'] = accept
        
        r = requests.post(url,
                          auth = self._getAuthentication(),
                          headers = headers,
                          data = body)
        r.raise_for_status()

        return r.content

    def _extractTagValues(self, answers, tag):
        result = []
        for item in answers:
            result.append(item[tag]['Value'][0])

        return result


    # Return all the DICOM instances (as arrays of bytes) inside the
    # study whose "Study Instance UID" is provided (WADO-RS request).
    def downloadInstancesOfStudy(self, studyInstanceUid):
        r = requests.get('%s/studies/%s' % (self.url, studyInstanceUid),
                         auth = self._getAuthentication())
        r.raise_for_status()

        parts = self._parseMultipart(r)

        if len(parts) < 1:
            raise Exception('WADO-RS returning zero instance from a study')
        else:
            return parts


    # Return all the DICOM instances (as arrays of bytes) inside the
    # series whose "Series Instance UID" is provided (WADO-RS
    # request). The "Study Instance UID" of the parent study must also
    # be provided.
    def downloadInstancesOfSeries(self, studyInstanceUid, seriesInstanceUid):
        r = requests.get('%s/studies/%s/series/%s' % (self.url, studyInstanceUid, seriesInstanceUid),
                         auth = self._getAuthentication())
        r.raise_for_status()

        parts = self._parseMultipart(r)

        if len(parts) < 1:
            raise Exception('WADO-RS returning zero instance from a series')
        else:
            return parts


    # Return the DICOM instance (as one array of bytes) that
    # corresponds to the instance whose "SOP Instance UID" is provided
    # (WADO-RS request). The "Study Instance UID" and the "Series
    # Instance UID" of the parent study/series must also be provided.
    def downloadInstance(self, studyInstanceUid, seriesInstanceUid, sopInstanceUid):
        r = requests.get('%s/studies/%s/series/%s/instances/%s' %
                         (self.url, studyInstanceUid, seriesInstanceUid, sopInstanceUid),
                         auth = self._getAuthentication())
        r.raise_for_status()

        parts = self._parseMultipart(r)

        if len(parts) != 1:
            raise Exception('WADO-RS returning more than one DICOM instance')
        else:
            return parts[0]


    # Upload a DICOM instance provided as an array of bytes to the
    # DICOMweb server (STOW-RS request).
    def uploadFromBytes(self, content):
        r = self._sendMultipart('%s/studies' % self.url, [ content ], 'application/dicom', 'application/dicom+json')


    # Upload a DICOM instance provided as a path on the filesystem to
    # the DICOMweb server (STOW-RS request).
    def uploadFromPath(self, path):
        with open(path, 'rb') as f:
            self.uploadFromBytes(f.read())


    # List the "Study Instance UID" tag of all the studies that are
    # stored on the DICOMweb server (QIDO-RS request).
    def listStudies(self):
        r = requests.get('%s/studies' % self.url,
                         auth = self._getAuthentication())
        r.raise_for_status()

        return self._extractTagValues(r.json(), _STUDY_INSTANCE_UID)


    # List the "Series Instance UID" tag of all the series that are
    # stored on the DICOMweb server inside the study whose "Study
    # Instance UID" is provided (QIDO-RS request).
    def listSeries(self, studyInstanceUid):
        r = requests.get('%s/studies/%s/series' % (self.url, studyInstanceUid),
                         auth = self._getAuthentication())
        r.raise_for_status()

        return self._extractTagValues(r.json(), _SERIES_INSTANCE_UID)


    # List the "SOP Instance UID" tag of all the instances that are
    # stored on the DICOMweb server inside the study/series whose
    # "Study Instance UID" and "Series Instance UID" is provided
    # (QIDO-RS request).
    def listInstances(self, studyInstanceUid, seriesInstanceUid):
        r = requests.get('%s/studies/%s/series/%s/instances' %
                         (self.url, studyInstanceUid, seriesInstanceUid),
                         auth = self._getAuthentication())
        r.raise_for_status()

        return self._extractTagValues(r.json(), _SOP_INSTANCE_UID)


    # Look for DICOM studies whose tags match the "criteria"
    # dictionary (QIDO-RS request). If the "onlyIdentifiers" argument
    # is true, the method returns the "Study Instance UID" tags of all
    # the matching studies. Otherwise, the DICOM tags of the study
    # module are returned, formatted using the DICOMweb JSON format.
    def lookupStudies(self, criteria, onlyIdentifiers = False):
        r = requests.get('%s/studies' % self.url,
                         auth = self._getAuthentication(),
                         params = criteria)
        r.raise_for_status()

        if onlyIdentifiers:
            return self._extractTagValues(r.json(), _STUDY_INSTANCE_UID)
        else:
            return r.json()


    # Look for DICOM series whose tags match the "criteria" dictionary
    # (QIDO-RS request). If the "onlyIdentifiers" argument is true,
    # the method returns both the "Study Instance UID" and "Series
    # Instance UID" tags of all the matching series. Otherwise, the
    # DICOM tags of the study and series modules are returned,
    # formatted using the DICOMweb JSON format.
    def lookupSeries(self, criteria, onlyIdentifiers = False):
        r = requests.get('%s/series' % self.url,
                         auth = self._getAuthentication(),
                         params = criteria)
        r.raise_for_status()

        if onlyIdentifiers:
            return list(zip(self._extractTagValues(r.json(), _STUDY_INSTANCE_UID),
                            self._extractTagValues(r.json(), _SERIES_INSTANCE_UID)))
        else:
            return r.json()


    # Look for DICOM instances whose tags match the "criteria"
    # dictionary (QIDO-RS request). If the "onlyIdentifiers" argument
    # is true, the method returns the "Study Instance UID", the
    # "Series Instance UID", and the "SOP Instance UID" tags of all
    # the matching instances. Otherwise, the DICOM tags at the study,
    # series, and instances modules are returned, formatted using the
    # DICOMweb JSON format.
    def lookupInstances(self, criteria, onlyIdentifiers = False):
        r = requests.get('%s/instances' % self.url,
                         auth = self._getAuthentication(),
                         params = criteria)
        r.raise_for_status()

        if onlyIdentifiers:
            return list(zip(self._extractTagValues(r.json(), _STUDY_INSTANCE_UID),
                            self._extractTagValues(r.json(), _SERIES_INSTANCE_UID),
                            self._extractTagValues(r.json(), _SOP_INSTANCE_UID)))
        else:
            return r.json()


    # Render the DICOM instance that corresponds to the instance whose
    # "SOP Instance UID" is provided (WADO-RS request). The "Study
    # Instance UID" and the "Series Instance UID" of the parent
    # study/series must also be provided. If the "decode" argument is
    # true, the method returns a PIL/Pillow image. Otherwise, the
    # method is a plain PNG file.
    def getRenderedInstance(self, studyInstanceUid, seriesInstanceUid, sopInstanceUid, decode = True):
        r = requests.get('%s/studies/%s/series/%s/instances/%s/rendered' %
                         (self.url, studyInstanceUid, seriesInstanceUid, sopInstanceUid),
                         auth = self._getAuthentication(),
                         headers = {
                             # Ask the DICOMweb server to generate a lossless rendering
                             'Accept' : 'image/png',
                         })
        r.raise_for_status()

        if decode:
            return PIL.Image.open(io.BytesIO(r.content))
        else:
            return r.content
