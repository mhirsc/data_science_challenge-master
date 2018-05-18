#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu May 10 22:21:15 2018

@author: Michal
"""

"""Extract data form DICOM server and store in mongo."""
import os
from pymongo import MongoClient
from dicom_server import DicomServer
from dicom_parser import DicomParser

# Instantiate server object
server = DicomServer()

# Check that DICOM server is working
print 'Checking if server is working...'
print 'Should get response 200, got response {}'.format(server.echo())


# Search DICOM server using DicomServer methods

patients = server.api('patients')

# Store data in mongo

# Create connection to database
client = MongoClient(os.getenv('MONGODB_URL'))
db = client.get_default_database()
print str(db)

# Instantiate object to parse DICOM data
parser = DicomParser()
db['dicom'].remove({})
db['series_numbers'].drop()
# Store patient data in database
for patient in patients:
    document = parser.radiation_total_dose(patient)
    print parser.radiation_total_dose(patient)
    db['dicom'].insert_one(document)
