#AgilentPNAXUtils.py
'''
@author: Jackson Anderson
ander906@purdue.edu
HybridMEMS
'''

import visa
import numpy as np
import re as re
import warnings

class AgilentPNAx:
    def __init__(self, resource):
        '''
        Create a new PNAx instance.
        
        Parameters:
        -----------
        resource : str
            A string containing the VISA address of the device.
        
        Returns:
        ----------
        N/A
        '''
        self.connect(resource)
        # socket communication slow - add delay between write and read
        # to prevent "103 - invalid separator" errors
        if re.search(r'.*SOCKET.*', resource):
            self.visaobj.query_delay = 1 
            self.visaobj.read_termination = '\n'
    
    def connect(self, resource):
        '''
        Connect to the PNA. 
        
        Parameters:
        -----------
        resource : str
            A string containing the VISA address of the device.
        
        Returns:
        ----------
        N/A
        '''
        rm = visa.ResourceManager()
        
        # VisaIOError VI_ERROR_RSRC_NFOUND
        try:
          self.visaobj = rm.open_resource(resource)
        except visa.VisaIOError as e:
          print(e.args)
          raise SystemExit(1)

    def pnaInitSetup(self):
        '''
        Perform initial setup of the PNA after connecting.
        
        Deletes old parameters, puts trigger on hold, and turns display on.
        
        Parameters:
        -----------
        N/A
        
        Returns:
        ----------
        N/A
        '''
        pna = self.visaobj
    #    pna.write("SYST:FPReset") # reset, delete measurements, traces, & windows
    #    pna.write('*CLS')
    #    pna.query('*OPC?')
        pna.write('CALCulate:PARameter:DELete:ALL')
        pna.write('SENSe1:SWEep:MODE HOLD')
        pna.write('DISPlay:ENABLE ON') # set to OFF to speed up measurement
        
       

    def clearWindow(self,winNum):
        '''
        Deletes all traces in the windows with the given number.
        
        Parameters:
        -----------
        winNum : int
            Number of window to clear.
        
        Returns:
        ----------
        N/A
        '''
        traces = self.visaobj.query('DISPlay:WINDow{}:CATalog?'.format(winNum))
        if re.search("EMPTY",traces):
            next
        else:
            traces = traces.split(',')
            for trace in traces:
                self.visaobj.write("DISPlay:WINDow{}:{}:DELete".format(winNum,trace)) 
            
    def disconnect(self):
        '''
        Turns output off and disconnects from PNA.
        
        Parameters:
        -----------
        N/A
        
        Returns:
        ----------
        N/A
        '''
        self.outputOff()
#        self.clearWindows()
        self.visaobj.close()
        
        
    def pnaSetup(self, portNums, ifBandwidth = None, startFreq = None, stopFreq = None,
                 centFreq = None, spanFreq = None, srcPower = None, nPoints = None, 
                 avgMode = None, nAvg = None):
        '''
        PNA measurement setup. Unpacks a dict of setup 
        
        Parameters:
        -----------
        ifBandwidth: int
            IF (receiver) bandwidth. Allowable values include:
            1,          2,    3,    5,    7,
            10,   15,   20,   30,   50,   70,
            100,  150,  200,  300,  500,  700,
            1k,   1.5k, 2k,   3k,   5k,   7k,
            10k,  15k,  20k,  30k,  50k,  70k,
            100k,       200k, 280k, 360k, 600k
        centerFreq & spanFreq : int
            frequency range of measurement. Max: 50 GHz. Cannot be used with start/stopFreq.
        startFreq & stopFreq : int
            frequency range of measurement. Max: 50 GHz. Cannot be used with center/spanFreq.
        srcPower : int
            Source power in dBm to set all the ports at.
        nPoints : int
            number of points in measurement (1 to 32,001)
        avgMode : string
            Determines type of averaging done by PNA. 
            POINT : averages at each frequency point before moving on
            SWEEP : averages the results of n sweeps 
        nAvg : int
            number of averages to take
    
        Returns:
        ----------
        N/A
        '''
        #set up channel here: power, cal, if bandwidth, # pts, sweep settings, avg, trigger
        pna = self.visaobj
        pna.write('CALCulate:PARameter:DELete:ALL')
        
        # TODO: Fix window creation. Currently, error caused if quad windows not specified on PNA.
        for n in portNums: 
          pna.write('DISPlay:WINDow{}:STATE ON'.format(n))
          self.clearWindow(n)
    
        if nPoints: pna.write('SENSe1:SWEep:POINts '+str(nPoints))
        pna.write('SENSe1:SWEep:GENeration ANALog')
        pna.write('SENSe1:SWEep:TIME:AUTO ON')
        # Frequencies shouldn't be changed outside callibrated range
        if startFreq and stopFreq: 
          pna.write('SENSe1:FREQuency:STARt {}'.format(startFreq)) 
          pna.write('SENSe1:FREQuency:STOP {}'.format(stopFreq))
        if centFreq and spanFreq: 
          pna.write('SENSe1:FREQuency:CENTer {}'.format(centFreq))
          pna.write('SENSe1:FREQuency:SPAN {}'.format(spanFreq))
        if srcPower:
          for i in [1,2,3,4]:
              maxPower = pna.query('SOURce{}:POWer? MAX'.format(i))
              minPower = pna.query('SOURce1:POWer? MIN')
              if srcPower >= minPower and srcPower <= maxPower:
                  pna.write('SOURce{}:POWer1 {}'.format(i,srcPower))
              else:
                  warnings.warn('Specified source power of {} for port {} not\
                                within the allowed range of {} to {} dBm.'
                                .format(srcPower,i,minPower,maxPower))
        ###
        if avgMode: pna.write('SENSe1:AVERage:MODE {}'.format(avgMode))
        if nAvg: pna.write('SENSe1:AVERage:COUNt {}'.format(nAvg))
        if ifBandwidth: pna.write('SENSe1:BANDwidth {}'.format(ifBandwidth))

        
    def sMeas(self, sPorts, savedir, localsavedir, testname, power = None, pnaparms = None, bal = False, phase = 0):
        '''
        Perform and save an s-parameter measurement.
        
        Parameters:
        -----------
        sPorts : string
            Comma seperated list of ports to be used in S-parameter measurement.
        savedir : string
            The directory on the PNA in which to save snp files.
        localsavedir : string    
            The local directory where SMU data will be saved.
        testname : string
            Identifier for the test that will be used in saved filenames.
        pnaparms : dict
            A dictionary containing test parameters to set on the pna.
        bal : bool
            Toggles Balanced-Balanced measurements with integrated true mode stimulus on/off.
        phase : float
            Phase offset in degrees to be applied to balanced port 1.
            
        Returns:
        ----------
        N/A
        
        Raises
        ------
        ValueError
            Number of ports doesn't match physically available port numbers.
        '''
        
        sParmsBBal = np.array([['SDD11','SDD12','SDC11','SDC12'],
                               ['SDD21','SDD22','SDC21','SDC22'],
                               ['SCD11','SCD12','SCC11','SCC12'],
                               ['SCD21','SCD22','SCC21','SCC22']])
        
        pna = self.visaobj
        
        sParms = []
        nums = sPorts.split(',')
        
        if len(nums) < 1 or len(nums) > 4:
            raise ValueError('Please Specify a number of ports between 1 and 4. '
                             'Currently, {} ports are specified.'.format(str(len(nums))))
        if bal and len(nums) != 4:
            raise ValueError('Bal-Bal measurement selected but number of ports does not equal 4.')
            
        filename = '{}.s{}p'.format(testname,str(len(nums)))
        if pnaparms:
            self.pnaSetup(nums, **pnaparms)
        else:
            self.pnaSetup(nums)
        self.checkCal()
        
        for i in nums:
            for j in nums:
                s = 'S{}_{}'.format(i,j)
                sParms.append('S{}_{}'.format(i,j))
                measName = 'meas'+s 
                pna.write("CALCulate:PARameter:DEFine:EXTended \'{}\',{}".format(measName,s))
                if bal:
                    pna.write("CALCulate:PARameter:SELect \'{}\'".format(measName))
                    pna.write("CALCulate:FSIMulator:BALun:PARameter:STATe ON")
                    pna.write("CALCulate:FSIMulator:BALun:PARameter:BBALanced:DEFine {}".format(sParmsBBal[int(i)-1,int(j)-1]))
                pna.write("DISPlay:WINDow{}:TRACe{}:FEED \'{}\'".format(i,j,measName))
        
        
        if bal: 
            pna.write("CALCulate1:FSIMulator:BALun:STIMulus:MODE TM")
            pna.write("CALCulate:FSIMulator:BALun:DEVice BBALanced")
            pna.write("CALCulate:FSIMulator:BALun:TOPology:BBALanced:PPORts 1,3,2,4")
  #          pna.write("CALCulate:FSIMulator:BALun:FIXTure:OFFSet:PHASe 0")
  #          pna.write("CALCulate:FSIMulator:BALun:BPORt1:OFFSet:PHASe {}".format(phase))
        else:
            pna.write("CALCulate1:FSIMulator:BALun:STIMulus:MODE SE")

        if power != None:
            if bal:
                portnames = ['Bal Port 1','Bal Port 2']
            else:
                portnames = ['Port 1', 'Port 2', 'Port 3', 'Port 4']
            for p in portnames:
#                maxPower = pna.query('SOURce1:POWer? MAX,\"{}\"'.format(p))
#                minPower = pna.query('SOURce1:POWer? MIN,\"{}\"'.format(p))
#                if power >= minPower and power <= maxPower:
                    print('Setting {} power to {} dbm.'.format(p,power))
                    pna.write('SOURce1:POWer {},\"{}\"'.format(power,p))
#                else:
#                    warnings.warn('Specified source power of {} for {} not\
#                                    within the allowed range of {} to {} dBm.'
#                                    .format(power,p,minPower,maxPower)) 
#                            
        pna.timeout = 9000000
        pna.write("SENSe1:SWEep:MODE SINGle") 
        pna.query('*OPC?')
#            pna.write("DISPlay:WINDow1:TRACe1:DELete")    
        print('Saving snp data on PNA in {}\\{}'.format(savedir,filename)) # query unterminated, also need to insert quotes around directory name
        pna.write(':CALCulate1:DATA:SNP:PORTs:SAVE \'{}\',\'{}\\{}\''.format(sPorts,savedir,filename)) #read 16 S parms in SNP format
        pna.query('*OPC?') 
        pna.timeout = 2000
        self.outputOff()

    def outputOff(self):
        '''
        Turns PNA output off by putting trigger in hold.
        
        Parameters:
        -----------
        N/A
        
        Returns:
        ----------
        N/A
        '''
        self.visaobj.write('SENSe1:SWEep:MODE HOLD') 


    ###############################
    # Wincal saves calfiles with format
    # CalSet_###
    ##########################
    
    def checkCal(self):
        '''
        Fetches active calibration set and prints the name, throwing an error if none is selected.
        
        Parameters:
        -----------
        N/A
        
        Returns:
        ----------
        N/A
        
        Raises
        ------
        ValueError
            No active calset.
        '''
        calname = self.visaobj.query('SENSe1:CORRection:CSET:ACTivate? NAME')
        if calname == "No Calset Selected":
            raise ValueError('No active calset for the measurement. Aborting')
        else:
            print('Current calibration: {}'.format(calname))
            
    def getCalInfo(self):
        '''
        Prints active calibration set as well as all cal sets present on PNA.
        
        Parameters:
        -----------
        N/A
        
        Returns:
        ----------
        N/A
        '''
        print(self.visaobj.query('SENSe1:CORRection:CSET:ACTivate? NAME'))
        print(self.visaobj.query('SENSe1:CORRection:CSET:TYPE:CATalog? NAME'))
        
    def getAvailCals(self):
        '''
        Prints all available cal sets present on PNA.
        
        Parameters:
        -----------
        N/A
        
        Returns:
        ----------
        N/A
        '''
        print(self.visaobj.query('CSET:CATalog?'))
        
    def saveState(self, filename):
        '''
        Saves the stimulus state of the instrument in an .sta file.
        
        Parameters:
        -----------
        filename: filename (including path) you wish to save data under.
        
        Returns:
        -----------
        N/A
        '''
        self.visaobj.write('MMEMory:STORe:STATe {}'.format(filename))

    def saveCal(self, filename):
        '''
        Saves the calibration of the instrument in a .cal file.
        
        Parameters:
        -----------
        filename: filename (including path) you wish to save data under.
        
        Returns:
        -----------
        N/A
        '''
        self.visaobj.write('MMEMory:STORe:CORRection {}'.format(filename))
        
    def saveStateCal(self, filename):
        '''
        Saves the stimulus settings and calibration of the instrument in a .csa file.
        
        Parameters:
        -----------
        filename: filename (including path) you wish to save data under.
        
        Returns:
        -----------
        N/A
        '''
        self.visaobj.write('MMEMory:STORe:CSARchive {}'.format(filename))