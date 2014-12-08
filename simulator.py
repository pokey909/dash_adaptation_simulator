__author__ = 'pokey'

from dash import *
import adaptation
from trace import Trace
from visualizer import bitswitch_plot

class SimulatorState(object):
    def __init__(self):
        self.t = 0
        self.http = None    # next http transfer to finish
        self.metric = PerformanceMetric()
        self.current_bitrate = 0

    def buffer_level(self, type_str):
        return self.metric.buffer_levels[type_str]


class Statistics(object):
    def __init__(self):
        self.bitrate_selections = {"AUDIO": Trace("time", "Audio-Bitrate selections"),
                                   "VIDEO": Trace("time", "Video-Bitrate selections")}


class Simulator(object):
    TOLERANCE_SEC = 0.0001

    def __init__(self):
        self.bitrates = {"VIDEO": [2000000, 3000000, 5000000, 8000000, 9000000, 15000000], "AUDIO": [128000]}  # bps
        self.segment_length = {"VIDEO": 6.0, "AUDIO": 3.0}
        self.segment_count = 1000
        self.random_size_factor = 0.05
        self._generate_segments()
        self.sample = {"VIDEO": [], "AUDIO": []}
        self.state = SimulatorState()
        self.stats = Statistics()

    def _generate_segments(self):
        self.segments = {"VIDEO": [], "AUDIO": []}
        for i in range(self.segment_count):
            for type_str in self.bitrates:
                v = []
                for bps in self.bitrates[type_str]:
                    seg = Segment(type_str, bps, self.segment_length[type_str])
                    v.append(seg)
                self.segments[type_str].append(v)

    def buffer_level(self, type_str):
        return self.state.metric.buffer_levels[type_str].level

    def read_sample_file(self, filename):
        with open(filename) as f:
            data = map(float, f)
        self.sample = {"VIDEO": [], "AUDIO": []}
        # mu, std = norm.fit(data)
        # m = self.fit_poisson(data)
        while len(data) > 1:
            self.sample["VIDEO"].append(data.pop())
            self.sample["AUDIO"].append(data.pop())

    def next_segment_choices(self):
        # determine what should be fetched next. The lower buffer wins
        if self.buffer_level("AUDIO") < self.buffer_level("VIDEO") and len(self.sample["AUDIO"])>0:
            type_str = "AUDIO"
        else:
            type_str = "VIDEO"
        next_segment_choices = self.segments[type_str].pop()
        return type_str, next_segment_choices

    def request_scheduler(self, adaptation):
        # simulate download
        type_str, choices = self.next_segment_choices()
        next_seg = adaptation.evaluate(type_str, choices, self.state)
        if next_seg.bps != self.stats.bitrate_selections[type_str].current_value:
            self.stats.bitrate_selections[type_str].append(self.state.t, next_seg.bps)
        self.state.http = HttpMetric(self.sample[type_str].pop() * 1000.0, next_seg)
        # print self.state.http
        self.state.metric.switches[type_str] = adaptation.bitrate_selections[type_str]

    def timestep(self, is_buffering):
        tx_time_s = self.state.http.time_left
        seg_duration = self.state.http.segment.duration_seconds
        type_str = self.state.http.segment.type_str

        # dynamic timestep until the download finished. Linear interpolation
        self.state.t += tx_time_s
        print("Timestep %.4f -> %.4f" % (self.state.t - tx_time_s, self.state.t))
        print self.state.http
        self.state.metric.bps_history.append(self.state.t, self.state.http.bps)

        if not is_buffering:
            print("Consuming %.2fs of buffer..." % tx_time_s)
            self.state.buffer_level("VIDEO").decrease_by(self.state.t, tx_time_s)
            self.state.buffer_level("AUDIO").decrease_by(self.state.t, tx_time_s)

        # fixed timestep where downloaded data is added to the buffer
        self.state.t += self.TOLERANCE_SEC
        print("Inc %.2fs of buffer..." % seg_duration)
        self.state.buffer_level(type_str).increase_by(self.state.t, seg_duration)

        print "[VIDEO]\t" + self.state.buffer_level("VIDEO").__unicode__()
        print "[AUDIO]\t" + self.state.buffer_level("AUDIO").__unicode__()

    def run(self, filename):
        adap = adaptation.CastLabsAdaptation(self.bitrates)
        self.state.metric = PerformanceMetric()
        self.state.simulator = self

        # initialize data
        self.read_sample_file(filename)
        self._generate_segments()

        # run simulation loop
        while len(self.sample["VIDEO"]) > 0 and len(self.sample["AUDIO"]) > 0:
            self.request_scheduler(adap)    # simulate new http request if the current one has finished
            self.timestep(adap.is_buffering())

        self.state.metric.print_stats()
        bitswitch_plot(self.bitrates, self.state.metric.buffer_levels, self.state.metric.bps_history, self.state.metric.switches)

