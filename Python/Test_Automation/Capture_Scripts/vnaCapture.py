"""
Screen Capture of the HP5262A VNA
    - This script will simply return a CSV and a plot of the screen.
    - The CSV is a colletction of all s-parameters in real an imag
    - This script will always capture all 4 parameters
"""

import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import time
import re
from datetime import datetime

# ---------------------------
# USER SETTINGS
# ---------------------------
GPIB_ADDRESS = "GPIB0::16::INSTR"
TIMEOUT_MS = 60000
S_PARAMS = ["S11", "S21", "S12", "S22"]

# ---------------------------
# HELPERS
# ---------------------------
def q_float(inst, cmd):
    return float(inst.query(cmd).strip())

def q_int(inst, cmd):
    return int(float(inst.query(cmd).strip()))

def q_str(inst, cmd, default="UNKNOWN"):
    try:
        return inst.query(cmd).strip()
    except Exception:
        return default

def sanitize(text):
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', text)

def read_trace_ascii(inst):
    inst.write("OUTPDATA")
    time.sleep(0.5)

    raw = inst.read_raw()
    text = raw.decode(errors="ignore")

    nums = re.findall(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][-+]?\d+)?', text)
    vals = np.array([float(x) for x in nums], dtype=float)

    return vals

# ---------------------------
# CONNECT
# ---------------------------
rm = pyvisa.ResourceManager()
vna = rm.open_resource(GPIB_ADDRESS)

vna.timeout = TIMEOUT_MS
vna.write_termination = "\n"
vna.read_termination = "\n"

# ---------------------------
# SETUP
# ---------------------------
vna.write("FORM4")

f_start = q_float(vna, "STAR?")
f_stop  = q_float(vna, "STOP?")
npts    = q_int(vna, "POIN?")
ifbw    = q_str(vna, "IFBW?")

freq_hz = np.linspace(f_start, f_stop, npts)

print(f"Start: {f_start} Hz | Stop: {f_stop} Hz | Points: {npts}")
print(f"IFBW: {ifbw}")

# ---------------------------
# READ DATA
# ---------------------------
results = {}

for sp in S_PARAMS:
    print(f"Reading {sp}...")

    vna.write(f"CHAN1;{sp};LOGM")
    vna.write("SING")
    time.sleep(2.0)

    vna.read_termination = None
    vals = read_trace_ascii(vna)
    vna.read_termination = "\n"

    if len(vals) != 2 * npts:
        raise RuntimeError(f"{sp}: expected {2*npts}, got {len(vals)}")

    results[sp] = vals[0::2] + 1j * vals[1::2]

# ---------------------------
# BUILD ARRAY FOR SAVING
# ---------------------------
data = np.column_stack([
    freq_hz,
    results["S11"].real, results["S11"].imag,
    results["S21"].real, results["S21"].imag,
    results["S12"].real, results["S12"].imag,
    results["S22"].real, results["S22"].imag,
])

# ---------------------------
# FILENAME
# ---------------------------
date_str = datetime.now().strftime("%Y-%m-%d")
fileLocation = r"replace_this_with_your_directory"  # Replace with directory to save to
fname = fileLocation + f"\{date_str}_{sanitize(GPIB_ADDRESS)}_replace_with_your_name.csv" # Replace with file name

# ---------------------------
# HEADER (for savetxt)
# ---------------------------
header = (
    f"Date: {date_str}\n"
    f"IFBW: {ifbw}\n"
    f"GPIB: {GPIB_ADDRESS}\n"
    f"Start_Hz: {f_start}\n"
    f"Stop_Hz: {f_stop}\n"
    f"Points: {npts}\n"
    "Columns:\n"
    "Freq_Hz, "
    "S11_Re, S11_Im, "
    "S21_Re, S21_Im, "
    "S12_Re, S12_Im, "
    "S22_Re, S22_Im"
)

# ---------------------------
# SAVE USING NUMPY
# ---------------------------
np.savetxt(
    fname,
    data,
    delimiter=",",
    header=header,
    comments="CalKitAttenuator_2X10dB"
)

print(f"\nSaved file: {fname}")

# ---------------------------
# PLOT (dB magnitude)
# ---------------------------
plt.figure()

for sp in S_PARAMS:
    mag_db = 20 * np.log10(np.abs(results[sp]))
    plt.plot(freq_hz/1e9, mag_db, label=sp)

plt.xlabel("Frequency (GHz)")
plt.ylabel("Magnitude (dB)")
plt.title("S-Parameters vs Frequency")
plt.legend()
plt.grid()

plt.show()

# ---------------------------
# CLEANUP
# ---------------------------
vna.close()
rm.close()