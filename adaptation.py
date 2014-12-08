__author__ = 'pokey'

from trace import Trace
from dash import *
from abc import ABCMeta, abstractmethod


class Adaptation(object):
    __metaclass__ = ABCMeta

    def __init__(self, bitrates):
        self.bitrates = bitrates

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
        self.bitrate_selections["VIDEO"].append(0, bitrates["VIDEO"][0])
        self.bitrate_selections["AUDIO"].append(0, bitrates["AUDIO"][0])

    def current_buffer_level(self, type_str):
        return self.simulator.buffer_level(type_str)

    def min_buffer_level(self):
        return self.sim_state.metric.min_buffer_level()

    def next_bitrate(self, type_str):
        # avg_bps = self.ma_bps_history()[-1] * 1000
        # print "AvgBPS\t%.1f" %  (avg_bps/1000.0)
        # if self.min_buffer_level() < 20:
        # for index, seg in enumerate(segment_choices):
        #         if seg.bps > avg_bps:
        #             idx = max(0, index-1)
        #             next_seg = segment_choices[idx]     # select last bitrate less than our average
        #             if self.sim_state.current_bitrate > next_seg and self.sim_state.metric.min_buffer_level() > 2:
        #                 print "TING!!!!!"
        #                 next_seg = segment_choices[index]
        #             return next_seg
        return self.bitrates[type_str][0]

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

        if bps / 1000.0 != self.bitrate_selections[next_segment_type].current_value:
            print "SWITCH: %d -> %d" % (self.bitrate_selections[next_segment_type].current_value, bps)
            self.bitrate_selections[next_segment_type].append(state.t, bps)

        return Segment.find_segment_for_bitrate(seg_choices, bps)


