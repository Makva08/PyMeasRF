from pymeasrf.AgilentE5072A import AgilentE5072A
import visa
import numpy as np
# Example usage with port control
if __name__ == "__main__":
    # User inputs
    device_name = "device1"
    num_points = 20001
    start_freq = 1e9
    stop_freq = 2e9
    power_dbm = 0
    source_port = 1
    s_parameter = "S21"

    rm = visa.ResourceManager()
    vna_address = "GPIB0::16::INSTR"

    try:
        vna = AgilentE5072A(rm.open_resource(vna_address))

        vna.set_frequency(start_freq, stop_freq)
        vna.set_points(num_points)
        vna.set_power(power_dbm)
        vna.set_port(source_port)  # Set source port

        print(f"Starting single sweep on E5072A with source port {source_port}...")
        vna.single_sweep()

        real, imag = vna.get_trace_data(s_parameter=s_parameter)
        freqs = np.linspace(start_freq, stop_freq, num_points)

        filename = f"{device_name}_{start_freq / 1e9}GHz-{stop_freq / 1e9}GHz_{num_points}pts_{power_dbm}dBm_{s_parameter}_port{source_port}.txt"

        with open(filename, 'w') as f:
            f.write(f"Frequency(Hz),{s_parameter}_Real,{s_parameter}_Imag\n")
            for freq, r, i in zip(freqs, real, imag):
                f.write(f"{freq},{r},{i}\n")
        print(f"Data saved to {filename}")

    finally:
        vna.close()
        rm.close()
        print("Instrument disconnected.")