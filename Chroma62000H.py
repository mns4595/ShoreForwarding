#!/usr/bin/env python

# References
#  - http://www.batronix.com/pdf/Rigol/ProgrammingGuide/DP800_ProgrammingGuide_EN.pdf
#  - https://github.com/freq0ut/Python-PyVisa
#  - http://juluribk.com/2015/05/08/controlling-rigol-dp832-with-python/
# Instructions
# - Download and install National Instruments VISA software (https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html#442805)
# - Download and install PyVISA (eg. "pip install -U pyvisa" from command line)

from pyvisa import ResourceManager
from visa import *
import time

_delay = 0.01  # in seconds


class CHROMA_62000H:
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

    def WriteCommand(self, command):
        self.device.write(command)
        time.sleep(_delay)

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
        command = ':SOUR:VOLT:LIMIT:LOW %s' % minVolt
        self.WriteCommand(command)

        command = ':SOUR:VOLT:LIMIT:HIGH %s' % maxVolt
        self.WriteCommand(command)

    def SetCurrent(self, val):
        command = ':SOUR:CURR %s' % val
        self.WriteCommand(command)

    def SetCurrentLimits(self, minCurr, maxCurr):
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
        return out_state

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
        status = self.device.query(query)

        ovp = status & 0x01
        ocp = (status >> 1) & 0x01
        opp = (status >> 2) & 0x01
        remote_inhibit = (status >> 3) & 0x01
        otp = (status >> 4) & 0x01
        fan_lock = (status >> 5) & 0x01
        sense_fault = (status >> 6) & 0x01
        series_fault = (status >> 7) & 0x01
        ac_fault = (status >> 9) & 0x01
        fold_back_cv_2_cc = (status >> 10) & 0x01
        fold_back_cc_2_cv = (status >> 11) & 0x01

        return (ovp, ocp, opp, remote_inhibit, otp, fan_lock, sense_fault, series_fault, ac_fault, fold_back_cv_2_cc, fold_back_cc_2_cv)
