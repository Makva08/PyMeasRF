# Combining RF generator and PXA
import visa
from pymeasrf.KeysightE8257D import KeysightE8257D
from pymeasrf.AgilentN9030A import AgilentN9030A
import numpy as np
import time

device_name = "LGSX001D1A"
power_dbm = 0
num_points = 20001
start_freq = 1e9
stop_freq = 2e9

rm = visa.ResourceManager()

sig_gen_address = "GPIB0::19::INSTR"  # Keysight E8257D
analyzer_address = "GPIB0::18::INSTR"  # Agilent N9030A

sig_gen = KeysightE8257D(rm.open_resource(sig_gen_address))
analyzer = AgilentN9030A(rm.open_resource(analyzer_address))

try:
    # Sig Gen
    sig_gen.set_power(power_dbm)
    sig_gen.set_frequency(start_freq, stop_freq)
    sig_gen.set_points(num_points)
    sig_gen.output_on()

    # Sig Analyzer
    analyzer.set_frequency_range(start_freq, stop_freq)
    analyzer.set_points(num_points)
    analyzer.set_max_hold(True)

    print("Starting single sweep on signal generator...")
    sig_gen.single_sweep()

    print("Starting max hold sweep on analyzer...")
    analyzer.initiate_sweep()

    sweep_time = (stop_freq - start_freq) / num_points * 1e-3  # Rough estimate, the bigger the better
    time.sleep(sweep_time + 2)  # Adding some buffer time

    freqs, amplitudes = analyzer.get_trace_data()
    filename = f"{device_name}_{start_freq / 1e9}GHz-{stop_freq / 1e9}GHz_{num_points}pts_{power_dbm}dBm.txt"

    with open(filename, 'w') as f:
        f.write("Frequency(Hz),Amplitude(dBm)\n")
        for freq, amp in zip(freqs, amplitudes):
            f.write(f"{freq},{amp}\n")
    print(f"Data saved to {filename}")

finally:
    sig_gen.output_off()
    sig_gen.close()
    analyzer.close()
    rm.close()
    print("Instruments disconnected.")