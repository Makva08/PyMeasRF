# Impedance Analyzer
# Currently highly depends on timeout function

import pyvisa
import time
import os

visa_address = "USB0::0x0957::0x1809::MY54100518::0::INSTR" # Enter visa adress of instrument
# Visa adress can be found in I/O Suite on instrument

save_directory = "D:\\Mar"

os.makedirs(save_directory, exist_ok=True) #making sure dir exists

rm = pyvisa.ResourceManager()
instrument = rm.open_resource(visa_address)
instrument.timeout = 60000

# Measurement setting:
num_points = 1601 # The more # of points, slower & more accurate the measurement
# Reset and configure the impedance analyzer
instrument.write("*RST")  # Reset instrument
time.sleep(2)
instrument.write(":SYST:PRES")  # Preset system to default state
time.sleep(2)
instrument.write(":DISP:PAGE MEAS")  # Ensure measurement display is active

instrument.write(":MMEM:STOR:S1P:FORM MA")  # Save as Linear Magnitude & Phase

def measure_and_save(f_start, f_stop, num_points):
    print(f"Measuring from {f_start / 1e6:.3f} MHz to {f_stop / 1e6:.3f} MHz...")
    instrument.write("*CLS")  # Clear errors
    instrument.write("*WAI")  # Wait until ready

    instrument.write(f":SENS:FREQ:STAR {f_start}")  # Set start frequency
    instrument.write(f":SENS:FREQ:STOP {f_stop}")  # Set stop frequency
    instrument.write(f":SENS:SWE:POIN {num_points}")  # Set number of points
    instrument.write(":SENS:SWE:TYPE LIN") # Set Sweep mode

    instrument.write(":TRIG:SOUR BUS")  # Set trigger source to BUS
    instrument.write(":TRIG:SEQ:SING")  # Ensure single sweep mode
    time.sleep(0.5)  # Allow settings to apply

    # **Start measurement**
    instrument.write(":INIT")
    time.sleep(1)

    start_time = time.time()
    while True:
        try:
            response = instrument.query("*OPC?").strip()
            if response == "1":
                break  # Measurement completed
        except pyvisa.errors.VisaIOError:
            pass
        time.sleep(0.5)

        # Timeout to prevent infinite loops
        if time.time() - start_time > 55:
            print(f"Warning: Measurement timeout for {f_start/1e6:.3f} MHz - {f_stop/1e6:.3f} MHz. Proceeding.")
            break

    def format_freq(freq):
        if freq < 1_000_000:  # Below 1 MHz → Display in kHz
            return f"{freq // 1000}kHz"
        else:  # 1 MHz and above → Display in MHz
            return f"{freq / 1_000_000:.3f}M".replace(".000", "")  # Remove unnecessary .000

    file_name = f"{save_directory}\\{format_freq(f_start)}-{format_freq(f_stop)}.s1p"
    instrument.write(f':MMEM:STOR:S1P "{file_name}"')
    print(f"Saved data to {file_name}")

# **Measurement Set 1: 300 kHz - 5 MHz in 100 kHz steps**
for f_start in range(300_000, 500_000, 100_000):
    f_stop = f_start + 100_000
    measure_and_save(f_start, f_stop, num_points)

# s2_sweeps = [
#     (100_000, 1_000_000)
# ]
#
# for f_start, f_stop in s2_sweeps:
#     measure_and_save(f_start, f_stop, 1601)
#
# # **Measurement Set 2: 1 MHz - 12 MHz in 1 MHz steps**
# for f_start in range(1_000_000, 2_000_000, 1_000_000):
#     f_stop = f_start + 1_000_000
#     measure_and_save(f_start, f_stop, 1601)
#
# s3_sweeps = [
#     (100_000, 500_000),
#     (500_000, 1_000_000)
# ]
#
# for f_start, f_stop in s3_sweeps:
#     measure_and_save(f_start, f_stop, 1601)
#
# # **Measurement Set 3: 100 kHz - 12 MHz in 0.5 MHz steps**
# for f_start in range(100_000, 1_000_000, 500_000):
#     f_stop = f_start + 500_000
#     measure_and_save(f_start, f_stop, 1601)
#
# # **Broadband Sweeps**
# broad_sweeps = [
#     (100_000, 5_000_000)
# ]
#
# for f_start, f_stop in broad_sweeps:
#     measure_and_save(f_start, f_stop, 1601)

# Close the connection
instrument.close()
rm.close()
print("All measurements completed successfully.")
