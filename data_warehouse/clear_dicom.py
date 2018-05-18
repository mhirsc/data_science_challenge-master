"""Delete all patients store in DICOM server."""
import os
import requests
from dicom_server import DicomServer

# Instantiate server object
server = DicomServer()
# Get patient hashes
patients = server.api('patients')

for patient in patients:
    url = os.path.join(os.getenv('DICOM_URL'), 'patients', patient)
    r = requests.delete(url)
    if r.status_code == 200:
        print 'Successfully deleted: {}'.format(patient)
    else:
        print 'Failed to delete: {}'.format(patient)
        print 'Status code: {}'.format(r.status_code)
