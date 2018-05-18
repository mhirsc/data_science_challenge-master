"""Class for parsing DICOM files."""
import os
from dicom_server import DicomServer


class DicomParser:
    """Class for parsing DICOM files."""

    def __init__(self, **kwargs):
        """Initialize with url to DICOM server."""
        self.server = DicomServer(**kwargs)

    def get_info(self, patient):
        """Return main DICOM tags from Orthanc."""
        url = os.path.join('patients', patient)
        return self.server.api(url)['MainDicomTags']

    def radiation_total_dose(self, patient):
        """Calculate total dose in Gy of treatment plan."""
        
        url = os.path.join('patients', patient)
        PatientID = self.server.api(url)['MainDicomTags']['PatientID']
                
        studies = self.server.api(url)['Studies']

        BeamDoses = 0
        
        for study in studies:
            series = []
            flat_series_list = []
        
            studies_url = os.path.join('studies',study)
            series.append(self.server.api(studies_url)['Series'])
            
            for sublist in series:
                for item in sublist:
                    flat_series_list.append(item)
                    
            for a_series in flat_series_list:
                
                instances = []
                flat_instances_list = []
                
                series_url = os.path.join('series',a_series)
    
                if self.server.api(series_url)['MainDicomTags']['Modality'] == 'RTPLAN':
                    instances.append(self.server.api(series_url)['Instances'])

                for sublist in instances:
                    for item in sublist:
                        flat_instances_list.append(item)
        
                for instance in flat_instances_list:
                    instance_tags = self.server.api(os.path.join('instances', instance, 'simplified-tags'))
                    beam_sequences = []
                    if 'FractionGroupSequence' in instance_tags.keys():
                        for i in instance_tags['FractionGroupSequence']:
                            beam_sequences.append(i['ReferencedBeamSequence'])
                            
                        beam_seqs_flattened = []
                        
                        for j in beam_sequences:
                            for item in j:
                                beam_seqs_flattened.append(item)
                                    
                        for k in beam_seqs_flattened:
                            BeamDoses = BeamDoses + float(k['BeamDose'])
                                
                            
        return {'PatientID':PatientID,'radiation_total_dose':BeamDoses}

#%%
        
 # This method does not return the same doses as in the clinical files -- it outputs ~10 whereas
 # the clinical files output ~40-50. This might be because the dicom sets for each patient might not 
 # be complete. However, the method cannot be changed in any way that will remedy this.      
            

        
