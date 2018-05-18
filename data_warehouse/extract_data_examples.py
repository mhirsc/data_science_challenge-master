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

# Find total number of patients
patients = server.api('patients')
print 'There are {} patients'.format(len(patients))

# Get the DICOM PatientID associated with each Orthanc patient id
for patient in patients:
    url = os.path.join('patients', patient)
    patient_id = server.api(url)['MainDicomTags']['PatientID']
    print 'Orthanc patient id: {}, DICOM PatientID: {}'.format(patient, patient_id)

# Find total number of male patients
query = {'PatientSex': 'M'}
print 'Searching for: {}'.format(query)
male_patients = server.find(query, level='Patient')
print 'There are {} male patients'.format(len(male_patients))

# Find total number of female patients
query = {'PatientSex': 'F'}
print 'Searching for: {}'.format(query)
female_patients = server.find(query, level='Patient')
print 'There are {} female patients'.format(len(female_patients))


# Explore the Orthanc REST API

# Get ids for all instances (=individual files) on server
endpoint = 'instances/'
print 'Posting to API endpoint: "{}"'.format(endpoint)
instances = server.api(endpoint)
print 'There are {} instances'.format(len(instances))

# GET simplified tags (=without full DICOM code) for particular file instance
instance_tags = server.api(os.path.join('instances', instances[0], 'simplified-tags'))
# NOTE: uncomment this to see the full structure of the tags
# print json.dumps(instance_tags, indent=4, sort_keys=True)


# Store data in mongo

# Create connection to database
client = MongoClient(os.getenv('MONGODB_URL'))
db = client.get_default_database()
print str(db)

# Instantiate object to parse DICOM data
parser = DicomParser()

# Store patient data in database
for patient in patients:
    document = parser.get_info(patient)
    print document
    print 'Inserting document for {}'.format(document['PatientID'])
    db['examples'].insert_one(document)
