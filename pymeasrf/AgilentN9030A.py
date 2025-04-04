#Agilent33220a.py
'''
@author: Jackson Anderson
ander906@purdue.edu
HybridMEMS
'''

import visa
import numpy as np

class AgilentN9030A:
    '''
    A class for controlling the Agilent N9030A PXA Signal Analyzer 
    using VISA commands. 
    '''
    
    
    def __init__(self, resource, label = None):
        '''
        Creates a new instrument instance and attempts connection. 
        
        Parameters:
        -----------
        resource : str
            A string containing the VISA address of the device.
        label : str
            The name of the device that will be used to label data uniquely.
        
        Returns:
        ----------
        N/A
        '''
        self.connect(resource, label) 
    
    def connect(self, resource, label = None):
        '''
        Connect to the instrument. 
        
        Parameters:
        -----------
        resource : str
            A string containing the VISA address of the device.
        label : str
            The name of the device that will be used to label data uniquely.
        Returns:
        ----------
        N/A
        '''
        rm = visa.ResourceManager()
        self.label = label
        
        # VisaIOError VI_ERROR_RSRC_NFOUND
        try:
          self.visaobj = rm.open_resource(resource)
        except visa.VisaIOError as e:
          print(e.args)
          raise SystemExit(1)

    def read(self, mode):
        '''
        Takes a measurement using current instrument measurement settings.

        
        Parameters:
        -----------
        mode : string
            The instrument mode you wish to take a measurement in. 
            Possible modes include, but no limited to:
                
                SAN : Signal analyzer 
        
        Returns:
        ----------
        data : str
            The measured data.
        '''
        self.visaobj.timeout = 60000 # set timeout to 60s for measurement
        data = self.visaobj.query(':READ:{}?'.format(mode))
        self.visaobj.timeout = 2000 # set timeout back to 2s
        return data  
        
    def disconnect(self):
        '''
        Turns off output and disconnects from the SMU. 
        
        Parameters:
        -----------
        N/A
        
        Returns:
        ----------
        N/A
        '''
        self.visaobj.control_ren(6) # sends GTL (Go To Local) command
        self.visaobj.close()