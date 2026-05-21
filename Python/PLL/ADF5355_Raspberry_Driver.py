#!/usr/bin/env python3
"""
ADF5355 programmer for Raspberry Pi SPI0
Target setup:
- 50 MHz external single-ended reference
- RFOUTB enabled
- RFOUTA disabled
- Output = 7.6 GHz on RFOUTB
- MUXOUT = digital lock detect

Pi wiring (BCM numbering):
- GPIO10 (MOSI) -> DATA
- GPIO11 (SCLK) -> CLK
- GPIO8  (CE0)  -> LE
- GPIO25        -> CE   (optional; set GPIO_CE=None if CE is hard-wired high)
- GPIO24        -> MUXOUT (optional lock-detect input)
"""

import math
import time
import spidev

try:
    import RPi.GPIO as GPIO
    HAVE_GPIO = True
except ImportError:
    HAVE_GPIO = False


# -----------------------------
# User config
# -----------------------------
SPI_BUS = 0
SPI_DEV = 0
SPI_SPEED_HZ = 1_000_000
SPI_MODE = 0

GPIO_CE = 25         # Set to None if ADF5355 CE is tied high
GPIO_MUXOUT = 24     # Set to None if unused

REF_HZ = 50_000_000
TARGET_RFOUTB_HZ = 7_600_000_000

R_COUNTER = 1
REF_DOUBLER = 0
REF_DIV2 = 0

# Charge pump current code: 0..15
CP_CURRENT_CODE = 2

# RFOUTA power code: 0=-4 dBm, 1=-1 dBm, 2=+2 dBm, 3=+5 dBm
RFOUTA_POWER_CODE = 0

# Disable mute-till-lock during debug
MUTE_TILL_LOCK = 0


# -----------------------------
# ADF5355 constants
# -----------------------------
MOD1 = 1 << 24
MAX_MOD2 = 0x3FFF
RFOUTB_MIN_HZ = 6_800_000_000
RFOUTB_MAX_HZ = 13_600_000_000


# -----------------------------
# Register bit helpers
# -----------------------------
def reg0_int(x): return ((x & 0xFFFF) << 4)
def reg0_prescaler(x): return ((x & 0x1) << 20)
def reg0_autocal(x): return ((x & 0x1) << 21)

def reg1_frac1(x): return ((x & 0xFFFFFF) << 4)

def reg2_mod2(x): return ((x & 0x3FFF) << 4)
def reg2_frac2(x): return ((x & 0x3FFF) << 18)

def reg3_phase(x): return ((x & 0xFFFFFF) << 4)
def reg3_phase_adjust(x): return ((x & 0x1) << 28)
def reg3_phase_resync(x): return ((x & 0x1) << 29)
def reg3_exact_sdload_reset(x): return ((x & 0x1) << 30)

def reg4_counter_reset_en(x): return ((x & 0x1) << 4)
def reg4_cp_threestate_en(x): return ((x & 0x1) << 5)
def reg4_power_down_en(x): return ((x & 0x1) << 6)
def reg4_pd_polarity_pos(x): return ((x & 0x1) << 7)
def reg4_mux_logic(x): return ((x & 0x1) << 8)          # 1 = 3.3 V
def reg4_refin_mode_diff(x): return ((x & 0x1) << 9)    # 0 = single-ended
def reg4_charge_pump_curr(x): return ((x & 0xF) << 10)
def reg4_double_buff_en(x): return ((x & 0x1) << 14)
def reg4_r_counter(x): return ((x & 0x3FF) << 15)
def reg4_rdiv2_en(x): return ((x & 0x1) << 25)
def reg4_rmult2_en(x): return ((x & 0x1) << 26)
def reg4_muxout(x): return ((x & 0x7) << 27)

MUXOUT_THREESTATE = 0
MUXOUT_DVDD = 1
MUXOUT_GND = 2
MUXOUT_R_DIV_OUT = 3
MUXOUT_N_DIV_OUT = 4
MUXOUT_ANALOG_LOCK_DETECT = 5
MUXOUT_DIGITAL_LOCK_DETECT = 6

REG5_DEFAULT = 0x00800025

def reg6_output_power(x): return ((x & 0x3) << 4)       # RFOUTA power
def reg6_rfouta_enable(x): return ((x & 0x1) << 6)      # 1 = enable RFOUTA
def reg6_rfoutb_disable(x): return ((x & 0x1) << 10)    # 0 = enable RFOUTB
def reg6_mute_till_lock(x): return ((x & 0x1) << 11)
def reg6_cp_bleed_curr(x): return ((x & 0xFF) << 13)
def reg6_rf_div_sel(x): return ((x & 0x7) << 21)
def reg6_feedback_fund(x): return ((x & 0x1) << 24)
def reg6_neg_bleed_en(x): return ((x & 0x1) << 29)
def reg6_gated_bleed_en(x): return ((x & 0x1) << 30)

REG6_DEFAULT = 0x14000006

def reg7_ld_mode_int_n_en(x): return ((x & 0x1) << 4)
def reg7_frac_n_ld_precision(x): return ((x & 0x3) << 5)
def reg7_lol_mode_en(x): return ((x & 0x1) << 7)
def reg7_ld_cycle_cnt(x): return ((x & 0x3) << 8)
def reg7_le_synced_refin_en(x): return ((x & 0x1) << 25)

REG7_DEFAULT = 0x10000007
REG8_DEFAULT = 0x102D0428

def reg9_synth_lock_timeout(x): return ((x & 0x1F) << 4)
def reg9_alc_timeout(x): return ((x & 0x1F) << 9)
def reg9_timeout(x): return ((x & 0x3FF) << 14)
def reg9_vco_band_div(x): return ((x & 0xFF) << 24)

def reg10_adc_en(x): return ((x & 0x1) << 4)
def reg10_adc_conv_en(x): return ((x & 0x1) << 5)
def reg10_adc_clk_div(x): return ((x & 0xFF) << 6)

REG10_DEFAULT = 0x00C0000A
REG11_DEFAULT = 0x0061300B

def reg12_phase_resync_clk_div(x): return ((x & 0xFFFF) << 16)

REG12_DEFAULT = 0x0000041C


# -----------------------------
# Utility helpers
# -----------------------------
def ceil_div(a, b):
    return (a + b - 1) // b

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def calc_fpfd_hz():
    return REF_HZ * (1 + REF_DOUBLER) // (R_COUNTER * (1 + REF_DIV2))


# -----------------------------
# PLL math
# -----------------------------
def compute_n_params_for_rfoutb(target_rfoutb_hz):
    if not (RFOUTB_MIN_HZ <= target_rfoutb_hz <= RFOUTB_MAX_HZ):
        raise ValueError(
            f"RFOUTB must be in [{RFOUTB_MIN_HZ}, {RFOUTB_MAX_HZ}] Hz"
        )

    # ADF5355 RFOUTB = 2 * VCO
    vco_hz = target_rfoutb_hz // 2
    fpfd_hz = calc_fpfd_hz()

    n_num = vco_hz
    n_den = fpfd_hz

    integer = n_num // n_den
    remainder_hz = n_num % n_den

    if remainder_hz == 0:
        frac1 = 0
        frac2 = 0
        mod2 = 2
    else:
        frac1_full_num = remainder_hz * MOD1
        frac1 = frac1_full_num // n_den
        rem_after_frac1 = frac1_full_num % n_den

        mod2 = fpfd_hz
        frac2 = int(round(rem_after_frac1 * mod2 / n_den))

        while mod2 > MAX_MOD2:
            mod2 >>= 1
            frac2 >>= 1

        if frac2 == mod2:
            frac1 += 1
            frac2 = 0

        if frac2 != 0:
            d = gcd(frac2, mod2)
            frac2 //= d
            mod2 //= d
        else:
            mod2 = 2

    prescaler = 1 if integer >= 75 else 0

    return {
        "rfoutb_hz": target_rfoutb_hz,
        "vco_hz": vco_hz,
        "fpfd_hz": fpfd_hz,
        "int": integer,
        "frac1": frac1,
        "frac2": frac2,
        "mod2": mod2,
        "prescaler": prescaler,
        "rf_div_sel": 0,      # /1
    }


# -----------------------------
# Build registers
# -----------------------------
def build_regs(target_rfoutb_hz):
    p = compute_n_params_for_rfoutb(target_rfoutb_hz)

    regs = [0] * 13

    # R0
    regs[0] = (
        reg0_int(p["int"]) |
        reg0_prescaler(p["prescaler"]) |
        reg0_autocal(1) |
        0x0
    )

    # R1
    regs[1] = (
        reg1_frac1(p["frac1"]) |
        0x1
    )

    # R2
    regs[2] = (
        reg2_frac2(p["frac2"]) |
        reg2_mod2(p["mod2"]) |
        0x2
    )

    # R3
    regs[3] = (
        reg3_phase(1) |
        reg3_phase_adjust(0) |
        reg3_phase_resync(0) |
        reg3_exact_sdload_reset(0) |
        0x3
    )

    # R4
    regs[4] = (
        reg4_counter_reset_en(0) |
        reg4_cp_threestate_en(0) |
        reg4_power_down_en(0) |
        reg4_pd_polarity_pos(1) |
        reg4_mux_logic(1) |
        reg4_refin_mode_diff(0) |
        reg4_charge_pump_curr(CP_CURRENT_CODE) |
        reg4_double_buff_en(1) |
        reg4_r_counter(R_COUNTER) |
        reg4_rdiv2_en(REF_DIV2) |
        reg4_rmult2_en(REF_DOUBLER) |
        reg4_muxout(MUXOUT_DIGITAL_LOCK_DETECT) |
        0x4
    )

    # R5
    regs[5] = REG5_DEFAULT

    # R6
    regs[6] = (
        REG6_DEFAULT |
        reg6_output_power(RFOUTA_POWER_CODE) |
        reg6_rfouta_enable(0) |
        reg6_rfoutb_disable(0) |
        reg6_mute_till_lock(MUTE_TILL_LOCK) |
        reg6_cp_bleed_curr(0) |
        reg6_rf_div_sel(p["rf_div_sel"]) |
        reg6_feedback_fund(1) |
        reg6_neg_bleed_en(0) |
        reg6_gated_bleed_en(0)
    )

    # R7
    regs[7] = (
        REG7_DEFAULT |
        reg7_ld_mode_int_n_en(1) |
        reg7_frac_n_ld_precision(0) |
        reg7_lol_mode_en(0) |
        reg7_ld_cycle_cnt(0) |
        reg7_le_synced_refin_en(1)
    )

    # R8
    regs[8] = REG8_DEFAULT

    # R9
    fpfd = p["fpfd_hz"]
    timeout = clamp(ceil_div(fpfd, 20_000 * 30), 1, 1023)
    synth_lock_timeout = clamp(ceil_div(fpfd * 2, 100_000 * timeout), 1, 31)
    alc_timeout = clamp(ceil_div(fpfd * 5, 100_000 * timeout), 1, 31)
    vco_band_div = clamp(ceil_div(fpfd, 2_400_000), 1, 255)

    regs[9] = (
        reg9_synth_lock_timeout(synth_lock_timeout) |
        reg9_alc_timeout(alc_timeout) |
        reg9_timeout(timeout) |
        reg9_vco_band_div(vco_band_div) |
        0x9
    )

    # R10
    adc_div = clamp(math.ceil((fpfd / 100_000 - 2) / 4), 1, 255)

    regs[10] = (
        REG10_DEFAULT |
        reg10_adc_en(1) |
        reg10_adc_conv_en(1) |
        reg10_adc_clk_div(adc_div)
    )

    # R11
    regs[11] = REG11_DEFAULT

    # R12
    regs[12] = (
        REG12_DEFAULT |
        reg12_phase_resync_clk_div(1)
    )

    # Conservative delay >16 ADC clocks
    adc_clk = fpfd / (4 * adc_div + 2)
    delay_us = max(200, math.ceil((16 / adc_clk) * 1_000_000))

    info = {
        **p,
        "timeout": timeout,
        "synth_lock_timeout": synth_lock_timeout,
        "alc_timeout": alc_timeout,
        "vco_band_div": vco_band_div,
        "adc_div": adc_div,
        "delay_us": delay_us,
    }

    return regs, info


# -----------------------------
# SPI / GPIO
# -----------------------------
def spi_write_reg(spi, regval):
    spi.xfer2([
        (regval >> 24) & 0xFF,
        (regval >> 16) & 0xFF,
        (regval >> 8) & 0xFF,
        regval & 0xFF,
    ])

def setup_gpio():
    if not HAVE_GPIO:
        return

    GPIO.setmode(GPIO.BCM)

    if GPIO_CE is not None:
        GPIO.setup(GPIO_CE, GPIO.OUT, initial=GPIO.LOW)

    if GPIO_MUXOUT is not None:
        GPIO.setup(GPIO_MUXOUT, GPIO.IN)

def cleanup_gpio():
    if HAVE_GPIO:
        GPIO.cleanup()

def pll_enable():
    if HAVE_GPIO and GPIO_CE is not None:
        GPIO.output(GPIO_CE, GPIO.HIGH)

def pll_disable():
    if HAVE_GPIO and GPIO_CE is not None:
        GPIO.output(GPIO_CE, GPIO.LOW)

def read_muxout():
    if HAVE_GPIO and GPIO_MUXOUT is not None:
        return GPIO.input(GPIO_MUXOUT)
    return None


# -----------------------------
# Programming sequences
# -----------------------------
def initial_program(spi, regs, delay_us):
    # fPFD <= 75 MHz sequence: R12 ... R1, wait, then R0
    for reg_num in range(12, 0, -1):
        spi_write_reg(spi, regs[reg_num])

    time.sleep(delay_us / 1_000_000.0)
    spi_write_reg(spi, regs[0])

def frequency_update(spi, regs, delay_us):
    # fPFD <= 75 MHz update sequence
    r4_reset_on = (regs[4] | reg4_counter_reset_en(1))
    r4_reset_off = (regs[4] & ~reg4_counter_reset_en(1))
    r0_autocal_off = (regs[0] & ~reg0_autocal(1))
    r0_autocal_on = regs[0]

    spi_write_reg(spi, regs[10])
    spi_write_reg(spi, r4_reset_on)
    spi_write_reg(spi, regs[2])
    spi_write_reg(spi, regs[1])
    spi_write_reg(spi, r0_autocal_off)
    spi_write_reg(spi, r4_reset_off)
    time.sleep(delay_us / 1_000_000.0)
    spi_write_reg(spi, r0_autocal_on)

def dump_regs(regs):
    for i in range(12, -1, -1):
        print(f"R{i:02d} = 0x{regs[i]:08X}")


# -----------------------------
# Main
# -----------------------------
def main():
    regs, info = build_regs(TARGET_RFOUTB_HZ)

    print("ADF5355 target config")
    print(f"  REF input      : {REF_HZ} Hz")
    print(f"  PFD            : {info['fpfd_hz']} Hz")
    print(f"  RFOUTB target  : {info['rfoutb_hz']} Hz")
    print(f"  VCO            : {info['vco_hz']} Hz")
    print(f"  INT            : {info['int']}")
    print(f"  FRAC1          : {info['frac1']}")
    print(f"  FRAC2          : {info['frac2']}")
    print(f"  MOD2           : {info['mod2']}")
    print(f"  RF divider     : /{1 << info['rf_div_sel']}")
    print(f"  Delay          : {info['delay_us']} us")
    print()
    dump_regs(regs)
    print()

    spi = spidev.SpiDev()
    spi.open(SPI_BUS, SPI_DEV)
    spi.max_speed_hz = SPI_SPEED_HZ
    spi.mode = SPI_MODE
    spi.bits_per_word = 8

    try:
        setup_gpio()
        pll_disable()
        time.sleep(0.01)
        pll_enable()
        time.sleep(0.01)

        initial_program(spi, regs, info["delay_us"])
        time.sleep(0.05)

        ld = read_muxout()
        print("Initial program done.")
        if ld is not None:
            print(f"MUXOUT lock-detect = {ld}")

    finally:
        spi.close()
        cleanup_gpio()


if __name__ == "__main__":
    main()