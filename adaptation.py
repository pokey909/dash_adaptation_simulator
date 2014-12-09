__author__ = 'pokey'

from trace import Trace
from dash import *
from abc import ABCMeta, abstractmethod
import algorithms as alg
import bisect
import copy

class Adaptation(object):
    __metaclass__ = ABCMeta

    def __init__(self, bitrates):
        self.bitrates = copy.deepcopy(bitrates)

    @abstractmethod
    def is_buffering(self):
        pass

    @abstractmethod
    def evaluate(self, next_segment_type, seg_choices, state):
        """
        Selects the next segment to schedule for download, optimized by bitrate
        :param next_segment_type: Next segment type to fetch, either VIDEO or AUDIO
        :param seg_choices: A list of possible segments for the next timestep
        :param state: current simulator state
        :return: Next segment to download
        """
        pass


class CastLabsAdaptation(Adaptation):
    MA_SIZE = 5

    def __init__(self, bitrates):
        Adaptation.__init__(self, bitrates)
        self.max_seconds = 50.0
        self.level_low_seconds = 10.0  # critical buffer level. Fill as fast as possible until level_high_seconds reached if below this value
        self.level_high_seconds = 30.0  # stable buffer level. Try to maintain current bitrate or improve it
        self.bps_history = Trace("time", "bps")
        self.bitrate_selections = {"AUDIO": Trace("time", "Audio-Bitrate selections"),
                                   "VIDEO": Trace("time", "Video-Bitrate selections")}

        self.sim_state = None
        # self.bitrate_selections["VIDEO"].append(-1, 0)
        # self.bitrate_selections["AUDIO"].append(-1, 0)

        self.my_bps = Trace("seconds", "bps")

        self.ma4_filter = alg.IterativeMovingAverage(4)
        self.ma10_filter = alg.IterativeMovingAverage(10)
        self.ma50_filter = alg.IterativeMovingAverage(80)

        self. last_index = 0

    def current_buffer_level(self, type_str):
        return self.simulator.buffer_level(type_str)

    def min_buffer_level(self):
        return self.sim_state.metric.min_buffer_level()

    def clamp(self, val, range):
        return min(max(range[0], val), range[1])

    def next_bitrate(self, type_str):
        index  = 0
        avg = 0
        clamp_range = [0, len(self.bitrates[type_str]) - 1]
        if self.bps_history.length != 0:
            avg = self.ma50_filter(self.bps_history.current_value)
            index = self.clamp(bisect.bisect(self.bitrates[type_str], avg) - 1, clamp_range)
            self.last_index = index
            self.my_bps.append(self.sim_state.t, avg)
        bps = self.bitrates[type_str][index]
        return bps

    def is_buffering(self):
        if self.sim_state is None:
            return False
        else:
            return self.min_buffer_level() < 3.0

    def evaluate(self, next_segment_type, seg_choices, state):
        """
        Updates internal performance statistics
        :param state: current state of the player simulator including buffer levels and http statistics
        :type state: dict of states
        :param next_segment_type: Type of the next segment, "AUDIO" or "VIDEO"
        :type next_segment_type: string
        :return: Next segment that should be downloaded
        """
        self.sim_state = state
        if state.http is not None:
            self.bps_history.append(state.t, state.http.bps)

        bps = self.next_bitrate(next_segment_type)

        if bps != self.bitrate_selections[next_segment_type].current_value:
            if next_segment_type == "VIDEO" and self.my_bps.length > 0:
                print "SWITCH @ t=%.2f: %d -> %d [Avg: %.2f / idx: %d]" % (self.sim_state.t, self.bitrate_selections[next_segment_type].current_value, bps, self.my_bps.current_value, self.last_index)
                print self.bitrates[next_segment_type][self.last_index]
            self.bitrate_selections[next_segment_type].append(state.t, bps)
            print self.bitrate_selections[next_segment_type].x_data
            print self.bitrate_selections[next_segment_type].y_data
        return Segment.find_segment_for_bitrate(seg_choices, bps)


