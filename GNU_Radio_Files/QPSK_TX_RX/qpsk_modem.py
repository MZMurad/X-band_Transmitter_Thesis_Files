#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: QPSK Modulator / Demodulator (modem)
# Author: Barry Duggan, modified by Gary Schafer
# GNU Radio version: 3.10.9.2

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
import pmt
from gnuradio import digital
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import soapy
import math
import sip



class qpsk_modem(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "QPSK Modulator / Demodulator (modem)", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("QPSK Modulator / Demodulator (modem)")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "qpsk_modem")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.sps = sps = 4
        self.samp_rate = samp_rate = 1e6*7
        self.qpsk = qpsk = digital.constellation_rect([-0.707-0.707j, 0.707-0.707j, +0.707+0.707j, -0.707+0.707j], [0, 1, 3, 2],
        4, 2, 2, 1, 1).base()
        self.preamble_size = preamble_size = 384*35
        self.postamble_size = postamble_size = 64*35*5
        self.phase_bw = phase_bw = 0.0628
        self.payload_size = payload_size = 64
        self.hdr = hdr = digital.header_format_default(digital.packet_utils.default_access_code, 0)
        self.f0 = f0 = 2.4e9
        self.excess_bw = excess_bw = 0.5

        ##################################################
        # Blocks
        ##################################################

        self.soapy_limesdr_source_0 = None
        dev = 'driver=lime'
        stream_args = ''
        tune_args = ['']
        settings = ['']

        self.soapy_limesdr_source_0 = soapy.source(dev, "fc32", 1, 'driver=lime,serial=1DA15123B2837C',
                                  stream_args, tune_args, settings)
        self.soapy_limesdr_source_0.set_sample_rate(0, samp_rate)
        self.soapy_limesdr_source_0.set_bandwidth(0, 0.0)
        self.soapy_limesdr_source_0.set_frequency(0, f0)
        self.soapy_limesdr_source_0.set_frequency_correction(0, 0)
        self.soapy_limesdr_source_0.set_gain(0, min(max(20.0, -12.0), 61.0))
        self.soapy_limesdr_sink_0 = None
        dev = 'driver=lime'
        stream_args = ''
        tune_args = ['']
        settings = ['']

        self.soapy_limesdr_sink_0 = soapy.sink(dev, "fc32", 1, 'driver=lime,serial=1DA15123B2837C',
                                  stream_args, tune_args, settings)
        self.soapy_limesdr_sink_0.set_sample_rate(0, samp_rate)
        self.soapy_limesdr_sink_0.set_bandwidth(0, 0.0)
        self.soapy_limesdr_sink_0.set_frequency(0, f0)
        self.soapy_limesdr_sink_0.set_frequency_correction(0, 0)
        self.soapy_limesdr_sink_0.set_gain(0, min(max(40, -12.0), 64.0))
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            'Output Spectrum', #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0.enable_grid(False)
        self.qtgui_freq_sink_x_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_freq_sink_x_0_win)
        self.qtgui_const_sink_x_0 = qtgui.const_sink_c(
            1024, #size
            'Output Const', #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_0.set_update_time(0.10)
        self.qtgui_const_sink_x_0.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_0.enable_autoscale(False)
        self.qtgui_const_sink_x_0.enable_grid(False)
        self.qtgui_const_sink_x_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_0_win = sip.wrapinstance(self.qtgui_const_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_const_sink_x_0_win)
        self.digital_protocol_formatter_bb_0 = digital.protocol_formatter_bb(hdr, 'packet_len')
        self.digital_crc32_bb_0 = digital.crc32_bb(False, "packet_len", True)
        self.digital_constellation_modulator_0 = digital.generic_mod(
            constellation=qpsk,
            differential=True,
            samples_per_symbol=sps,
            pre_diff_code=True,
            excess_bw=excess_bw,
            verbose=False,
            log=False,
            truncate=False)
        self.blocks_vector_source_x_0_0 = blocks.vector_source_b([0xc0, 0xaf], True, 1, [])
        self.blocks_vector_source_x_0 = blocks.vector_source_b([0xc0, 0xaf], True, 1, [])
        self.blocks_tagged_stream_mux_0 = blocks.tagged_stream_mux(gr.sizeof_char*1, 'packet_len', 0)
        self.blocks_stream_to_tagged_stream_0_0_0_0_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, postamble_size, "packet_len")
        self.blocks_stream_to_tagged_stream_0_0_0_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, preamble_size, "packet_len")
        self.blocks_stream_to_tagged_stream_0_0_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, payload_size, "packet_len")
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_gr_complex*1)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_cc(0.3)
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_char*1, '/home/rango/Desktop/QPSK_TRIAL/QPSK_Thisone/images.jpeg', False, 0, 0)
        self.blocks_file_source_0.set_begin_tag(pmt.PMT_NIL)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_file_source_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.qtgui_const_sink_x_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.qtgui_freq_sink_x_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.soapy_limesdr_sink_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0, 0), (self.digital_crc32_bb_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0_0, 0), (self.blocks_tagged_stream_mux_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0_0_0_0_0, 0), (self.blocks_tagged_stream_mux_0, 3))
        self.connect((self.blocks_tagged_stream_mux_0, 0), (self.digital_constellation_modulator_0, 0))
        self.connect((self.blocks_vector_source_x_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0_0, 0))
        self.connect((self.blocks_vector_source_x_0_0, 0), (self.blocks_stream_to_tagged_stream_0_0_0_0_0, 0))
        self.connect((self.digital_constellation_modulator_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.digital_crc32_bb_0, 0), (self.blocks_tagged_stream_mux_0, 2))
        self.connect((self.digital_crc32_bb_0, 0), (self.digital_protocol_formatter_bb_0, 0))
        self.connect((self.digital_protocol_formatter_bb_0, 0), (self.blocks_tagged_stream_mux_0, 1))
        self.connect((self.soapy_limesdr_source_0, 0), (self.blocks_null_sink_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "qpsk_modem")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.qtgui_freq_sink_x_0.set_frequency_range(0, self.samp_rate)
        self.soapy_limesdr_sink_0.set_sample_rate(0, self.samp_rate)
        self.soapy_limesdr_source_0.set_sample_rate(0, self.samp_rate)

    def get_qpsk(self):
        return self.qpsk

    def set_qpsk(self, qpsk):
        self.qpsk = qpsk

    def get_preamble_size(self):
        return self.preamble_size

    def set_preamble_size(self, preamble_size):
        self.preamble_size = preamble_size
        self.blocks_stream_to_tagged_stream_0_0_0_0.set_packet_len(self.preamble_size)
        self.blocks_stream_to_tagged_stream_0_0_0_0.set_packet_len_pmt(self.preamble_size)

    def get_postamble_size(self):
        return self.postamble_size

    def set_postamble_size(self, postamble_size):
        self.postamble_size = postamble_size
        self.blocks_stream_to_tagged_stream_0_0_0_0_0.set_packet_len(self.postamble_size)
        self.blocks_stream_to_tagged_stream_0_0_0_0_0.set_packet_len_pmt(self.postamble_size)

    def get_phase_bw(self):
        return self.phase_bw

    def set_phase_bw(self, phase_bw):
        self.phase_bw = phase_bw

    def get_payload_size(self):
        return self.payload_size

    def set_payload_size(self, payload_size):
        self.payload_size = payload_size
        self.blocks_stream_to_tagged_stream_0_0_0.set_packet_len(self.payload_size)
        self.blocks_stream_to_tagged_stream_0_0_0.set_packet_len_pmt(self.payload_size)

    def get_hdr(self):
        return self.hdr

    def set_hdr(self, hdr):
        self.hdr = hdr

    def get_f0(self):
        return self.f0

    def set_f0(self, f0):
        self.f0 = f0
        self.soapy_limesdr_sink_0.set_frequency(0, self.f0)
        self.soapy_limesdr_source_0.set_frequency(0, self.f0)

    def get_excess_bw(self):
        return self.excess_bw

    def set_excess_bw(self, excess_bw):
        self.excess_bw = excess_bw




def main(top_block_cls=qpsk_modem, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
