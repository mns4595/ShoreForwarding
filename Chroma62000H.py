#!/usr/bin/env python

# References
#  - http://www.batronix.com/pdf/Rigol/ProgrammingGuide/DP800_ProgrammingGuide_EN.pdf
#  - https://github.com/freq0ut/Python-PyVisa
#  - http://juluribk.com/2015/05/08/controlling-rigol-dp832-with-python/
# Instructions
# - Download and install National Instruments VISA software (https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html#442805)
# - Download and install PyVISA (eg. "pip install -U pyvisa" from command line)

from dataclasses import dataclass
from pyvisa import ResourceManager
from visa import *
import time

_delay = 0.01  # in seconds

# Make a struct for the status


@dataclass
class ChromaStatus:
    ovp: bool = False
    ocp: bool = False
    opp: bool = False
    remote_inhibit: bool = False
    otp: bool = False
    fan_lock: bool = False
    sense_fault: bool = False
    series_fault: bool = False
    ac_fault: bool = False
    fold_back_cv_2_cc: bool = False
    fold_back_cc_2_cv: bool = False
    output_state: str = "OFF"
    cvcc: str = "CV"


class CHROMA_62000H:
    kMaxPossibleVoltage = 1000.0
    kMaxPossibleCurrent = 15.0
    kMaxPossiblePower = 15000.0

    def __init__(self, usb_or_serial='USB0'):
        try:
            self.rm = ResourceManager()
            self.instrument_list = self.rm.list_resources()

            self.address = [elem for elem in self.instrument_list if (elem.find('USB') != -1 and elem.find(
                usb_or_serial) != -1)]  # Search a instrument with USB and serial number in the instrument list

            if self.address.__len__() == 0:
                self.status = "Not Connected"
                self.error_reason = "Could not connect to device"
            else:
                self.address = self.address[0]
                self.device = self.rm.open_resource(self.address)
                # print("Connected to " + self.address)
                self.status = "Chroma 62000H Supply Connected"
                self.connected_with = 'USB'

        except:
            self.status = "Not Connected"
            self.error_reason = "except: PyVISA is not able to find any devices"

    def IsConnected(self):
        return self.status

    def ConfigureDefaultProtections(self):
        # Configure default protection limits
        kMinAllowableCurrent = 0.0
        kMaxAllowableCurrent = 15.0
        self.SetCurrentLimits(kMinAllowableCurrent, kMaxAllowableCurrent)

        kMinAllowableVoltage = 0.0
        kMaxAllowableVoltage = 706.0
        self.SetVoltageLimits(kMinAllowableVoltage, kMaxAllowableVoltage)

        kAbsoluteMaxVoltage = 708.0
        kAbsoluteMaxCurrent = 15.0
        kApsoluteMaxPower = 15000.0
        self.SetOVP(kAbsoluteMaxVoltage)
        self.SetOCP(kAbsoluteMaxCurrent)
        self.SetOPP(kApsoluteMaxPower)

        self.SetVoltage(0)
        self.SetCurrent(0)

    def WriteCommand(self, command):
        self.device.write(command)
        time.sleep(_delay)

    def Abort(self):
        command = ':ABOR'
        self.WriteCommand(command)

        self.SetVoltage(0)
        self.SetCurrent(0)

    def EnableOutput(self):
        command = ':CONF:OUTP ON'
        self.WriteCommand(command)

    def DisableOutput(self):
        command = ':CONF:OUTP OFF'
        self.WriteCommand(command)

    def SetVoltage(self, val):
        command = ':SOUR:VOLT %s' % val
        self.WriteCommand(command)

    def SetVoltageLimits(self, minVolt, maxVolt):
        if (maxVolt > self.kMaxPossibleVoltage):
            maxVolt = self.kMaxPossibleVoltage
        if (minVolt < 0):
            minVolt = 0.0

        command = ':SOUR:VOLT:LIMIT:LOW %s' % minVolt
        self.WriteCommand(command)

        command = ':SOUR:VOLT:LIMIT:HIGH %s' % maxVolt
        self.WriteCommand(command)

    def SetCurrent(self, val):
        command = ':SOUR:CURR %s' % val
        self.WriteCommand(command)

    def SetCurrentLimits(self, minCurr, maxCurr):
        if(maxCurr > self.kMaxPossibleCurrent):
            maxCurr = self.kMaxPossibleCurrent
        if (minCurr < 0):
            minCurr = 0.0

        command = ':SOUR:CURR:LIMIT:LOW %s' % minCurr
        self.WriteCommand(command)

        command = ':SOUR:CURR:LIMIT:HIGH %s' % maxCurr
        self.WriteCommand(command)

    def SetOVP(self, val):
        command = ':SOUR:VOLT:PROT:HIGH %s' % val
        self.WriteCommand(command)

    def SetOCP(self, val):
        command = ':SOUR:CURR:PROT:HIGH %s' % val
        self.WriteCommand(command)

    def SetOPP(self, val):
        command = ':SOUR:POW:PROT:HIGH %s' % val
        self.WriteCommand(command)

    def GetOutputState(self):
        query = ':CONF:OUTP?'
        out_state = self.device.query(query)
        if (out_state == "ON\n"):
            return True
        return False

    def GetConfiguredVoltage(self):
        query = ':SOUR:VOLT?'
        voltage = self.device.query(query)
        return voltage

    def GetVoltageLimits(self):
        query = ':SOUR:VOLT:LIMIT:LOW?'
        low = self.device.query(query)
        query = ':SOUR:VOLT:LIMIT:HIGH?'
        high = self.device.query(query)
        return (low, high)

    def GetConfiguredCurrent(self):
        query = ':SOUR:CURR?'
        current = self.device.query(query)
        return current

    def GetCurrentLimits(self):
        query = ':SOUR:CURR:LIMIT:LOW?'
        low = self.device.query(query)
        query = ':SOUR:CURR:LIMIT:HIGH?'
        high = self.device.query(query)
        return (low, high)

    def GetOVP(self):
        query = ':SOUR:VOLT:PROT:HIGH?'
        ovp = self.device.query(query)
        return ovp

    def GetOCP(self):
        query = ':SOUR:CURR:PROT:HIGH?'
        ocp = self.device.query(query)
        return ocp

    def GetOPP(self):
        query = ':SOUR:POW:PROT:HIGH?'
        opp = self.device.query(query)
        return opp

    def MeasureVoltage(self):
        command = ':MEAS:VOLT?'
        volt = self.device.query(command)
        volt = float(volt)
        return volt

    def MeasureCurrent(self):
        query = ':MEAS:CURR?'
        curr = self.device.query(query)
        curr = float(curr)
        return curr

    def MeasurePower(self):
        query = ':MEAS:POW?'
        power = self.device.query(query)
        power = float(power)
        return power

    def FetchStatus(self):
        query = ':FETC:STAT?'
        raw = self.device.query(query)
        status0 = ord(raw[0])
        status1 = ord(raw[1])

        status_struct = ChromaStatus()

        status_struct.ovp = status0 & 0x01
        status_struct.ocp = (status0 >> 1) & 0x01
        status_struct.opp = (status0 >> 2) & 0x01
        status_struct.remote_inhibit = (status0 >> 3) & 0x01
        status_struct.otp = (status0 >> 4) & 0x01
        status_struct.fan_lock = (status0 >> 5) & 0x01
        status_struct.sense_fault = (status0 >> 6) & 0x01
        status_struct.series_fault = (status0 >> 7) & 0x01

        status_struct.ac_fault = (status1 >> 9) & 0x01
        status_struct.fold_back_cv_2_cc = (status1 >> 10) & 0x01
        status_struct.fold_back_cc_2_cv = (status1 >> 11) & 0x01
        # TODO Arg2 and Arg3
        return status_struct
