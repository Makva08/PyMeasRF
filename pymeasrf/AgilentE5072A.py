import visa
import numpy as np
import time


class AgilentE5072A:
    """Class to control the Keysight E5072A ENA Vector Network Analyzer."""

    def __init__(self, resource):
        self.instr = resource
        self.instr.timeout = 10000
        self.write("*CLS")
        self.write(":FORM:DATA ASC")

    def write(self, command):
        self.instr.write(command)

    def query(self, command):
        return self.instr.query(command).strip()

    def set_frequency(self, start_freq, stop_freq):
        self.write(f":SENS:FREQ:START {start_freq}")
        self.write(f":SENS:FREQ:STOP {stop_freq}")

    def set_points(self, num_points):
        self.write(f":SENS:SWE:POIN {num_points}")

    def set_power(self, power_dbm):
        self.write(f":SOUR:POW {power_dbm}")

    def set_port(self, source_port):
        if source_port not in [1, 2]:
            raise ValueError("Source port must be 1 or 2.")
        self.write(f":SOUR:PORT {source_port}")

    def single_sweep(self):
        self.write(":SENS:SWE:MODE SING")
        self.write(":INIT:IMM")
        self.write("*OPC")
        while int(self.query("*OPC?")) != 1:
            time.sleep(0.1)

    def get_trace_data(self, s_parameter="S21"):
        """What parameters want retreived"""
        valid_params = ["S11", "S21", "S12", "S22"]
        if s_parameter not in valid_params:
            raise ValueError(f"S-parameter must be one of {valid_params}")
        self.write(f":CALC:PAR1:DEF {s_parameter}")
        data = self.query(":CALC:DATA:SDAT?")
        data_list = [float(x) for x in data.split(",")]
        real = data_list[0::2]  # Real parts
        imag = data_list[1::2]  # Imag parts
        return real, imag

    def close(self):
        self.instr.close()
