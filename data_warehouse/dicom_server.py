"""Class for interacting with DICOM servers."""
import requests
import json
import os

dicom_url = os.getenv('DICOM_URL', None)


class DicomServer:
    """Class for interacting with DICOM servers.

    Implements some of the commands from the DICOM Message Service Element (DIMSE):
    http://dicom.nema.org/dicom/2013/output/chtml/part07/sect_7.5.html

    These commands are executed via the Orthanc REST API:
    https://docs.google.com/spreadsheets/u/1/d/1muKHMIb9Br-59wfaQbDeLzAfKYsoWfDSXSmyt6P4EM8/pubhtml
    """

    def __init__(self, DICOM_URL=None):
        """Initialize with url to DICOM server."""
        self.dicom_url = DICOM_URL if DICOM_URL else os.getenv('DICOM_URL', None)
        self.api_level = {'Patient': 'patients', 'Study': 'studies', 'Series': 'series'}

        # Check if a DICOM server has been supplied
        if not self.dicom_url:
            raise ValueError("DICOM server url must be supplied.")

        # Get server configuration information
        system = requests.get(os.path.join(self.dicom_url, 'system'))
        for arg, val in system.json().items():
            setattr(self, arg, val)

    def echo(self, modality='self'):
        """Test DICOM server using C-ECHO DIMSE protocol.

        Uses Orthanc REST API to test if DICOM server is running
        and accessible. This is basically `ping` for testing the DICOM server.

        Parameters
        ----------
        modality : string, url or container name to ping

        Returns
        -------
        response status code
        """
        # Create path to dicom server to test
        echo_url = os.path.join(self.dicom_url, 'modalities', modality, 'echo')
        r = requests.post(echo_url)
        return r.status_code

    def find(self, query, level='Study'):
        """Search DICOM server using C-FIND DIMSE protocol.

        Uses Orthanc REST API to POST request to DICOM server.

        Parameters
        ----------
        query : dict, fields to search for
        level : str in self.api_level , level of DICOM files to search

        Returns
        -------
        queries : queries to search modality
        """
        # Generate request
        data = {'Level': level, 'Query': query}
        find_url = os.path.join(self.dicom_url, 'tools', 'find')
        r = requests.post(find_url, data=json.dumps(data))
        find_hash = r.json()
        # Add the query level to the hash values
        paths_hash = [os.path.join(self.api_level[level], item) for item in find_hash]
        return paths_hash

    def api(self, endpoint, data=None):
        """Use Orthanc's REST API.

        Documentation:
        https://docs.google.com/spreadsheets/u/1/d/1muKHMIb9Br-59wfaQbDeLzAfKYsoWfDSXSmyt6P4EM8/pubhtml

        Parameters
        ----------
        endpoint : str, API endpoint to use
        data : dict, used for POST requests

        Returns
        -------
        queries : queries to search modality
        """
        url = os.path.join(self.dicom_url, endpoint)
        if data:
            r = requests.post(url, data=json.dumps(data))
        else:
            r = requests.get(url)
        return r.json()
