"""
Screen Capture of the HP8562A Spectrum Analyzer
    - This script will simply return a CSV and a plot of the screen.
"""


import pyvisa
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

rm = pyvisa.ResourceManager()
print("VISA resources:", rm.list_resources())

GPIB_ID = "GPIB0::18::INSTR"
print("Using: "+GPIB_ID)

inst = rm.open_resource(GPIB_ID)
inst.timeout = 10000

# ---- Get frequency settings ----
center_freq = float(inst.query("CF?"))
span = float(inst.query("SP?"))
rbw = float(inst.query("RB?"))  # may need adjustment

print(f"Center Frequency: {center_freq} Hz")
print(f"Span: {span} Hz")
print(f"RBW: {rbw} Hz")

# ---- Ensure trace is active ----
inst.write("VIEW TRA")

# ---- Get trace data ----
raw_data = inst.query("TRA?")
print("Raw trace received")

# ---- Convert to numeric array ----
data_array = []
for item in raw_data.replace("\n", "").split(","):
    item = item.strip()
    if item:
        data_array.append(float(item))

data_array = np.array(data_array)

print(f"Number of points: {len(data_array)}")

# ---- Build frequency axis ----
start_freq = center_freq - span / 2
stop_freq = center_freq + span / 2
freqs = np.linspace(start_freq, stop_freq, len(data_array))

# ---- Save using np.savetxt ----
name = "replace_text_with_file_name" # Replace with file name
date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
fileLocation = r"replace_this_with_your_directory" # Replace with directory to save to
filename = fileLocation + f"\{date_str}_{name}.csv"

# Stack data into 2 columns
output_data = np.column_stack((freqs, data_array))

# Create header string (will appear at top of file)
header = (
    f"Date: {date_str}\n"
    f"Center Frequency (Hz): {center_freq}\n"
    f"Span (Hz): {span}\n"
    f"RBW (Hz): {rbw}\n"
    f"ID: 8562A {GPIB_ID}\n"
    "Frequency (Hz),Power (dBm)"
)

# Save file
np.savetxt(
    filename,
    output_data,
    delimiter=",",
    header=header,
    comments=''  # removes '#' from header lines
)

print(f"\nData saved   to: {filename}")

# ---- Plot ----
plt.figure()
plt.plot(freqs/1e9, data_array) # Was deviding the wrong thing with 1e9
plt.xlabel("Frequency (GHz)")
plt.ylabel("Power (dB)")
plt.title("Spectrum Capture")
plt.grid()
plt.savefig(fileLocation+f"\{date_str}_{name}.png")
plt.show()
inst.close()