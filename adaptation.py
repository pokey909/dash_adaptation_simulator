__author__ = 'pokey'

from trace import Trace
from dash import *
from abc import ABCMeta, abstractmethod
import algorithms as alg
import bisect
import copy
from itertools import ifilter

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


class StateVars:
    def __init__(self):
        self.bps_history = Trace("time", "bps")
        self.ma4_history = Trace("time", "bps ma4")
        self.ma10_history = Trace("time", "bps ma10")
        self.ma50_history = Trace("time", "bps ma50")
        self.buffer_history = Trace("sec", "sec")
        self.buffer_ma4_history = Trace("sec", "sec")
        self.buffer_ma10_history = Trace("sec", "sec")

class CastLabsAdaptation(Adaptation):
    MA_SIZE = 5

    def __init__(self, bitrates):
        Adaptation.__init__(self, bitrates)
        self.max_seconds = 50.0
        self.level_critical_seconds = 20.0  # critical buffer level. Fill as fast as possible until level_high_seconds reached if below this value
        self.level_low_seconds = 50.0  # low buffer level. Fill as fast as possible until level_high_seconds reached if below this value
        self.level_high_seconds = 100.0  # stable buffer level. Try to maintain current bitrate or improve it
        self.bitrate_selections = {"AUDIO": Trace("time", "Audio-Bitrate selections"),
                                   "VIDEO": Trace("time", "Video-Bitrate selections")}

        self.sim_state = None
        self.segment_choices = []

        self.buffer_ma4 = alg.IterativeMovingAverage(4)
        self.buffer_ma10 = alg.IterativeMovingAverage(10)

        self.ma4_filter = alg.IterativeMovingAverage(4)
        self.ma10_filter = alg.IterativeMovingAverage(10)
        self.ma50_filter = alg.IterativeMovingAverage(80)

        self. last_index = {"VIDEO": 0, "AUDIO": 0}

        self.fix_bps = False

        self.state_vars = StateVars()
        self.state_vars.bps_history = Trace("time", "bps")
        self.state_vars.ma4_history = Trace("time", "bps ma4")
        self.state_vars.ma10_history = Trace("time", "bps ma10")
        self.state_vars.ma50_history = Trace("time", "bps ma50")
        self.state_vars.buffer_history = Trace("sec", "sec")
        self.state_vars.buffer_ma4_history = Trace("sec", "sec")
        self.state_vars.buffer_ma10_history = Trace("sec", "sec")
        self.state_vars.name = Trace("sec", "sec")
        self.selected_bps = {"AUDIO": 0, "VIDEO": 0}

        self.hold_bps = 0

    def current_buffer_level(self, type_str):
        return self.simulator.buffer_level(type_str)

    def min_buffer_level(self):
        return self.sim_state.metric.min_buffer_level()

    def clamp(self, val, range):
        return min(max(range[0], val), range[1])


    def update_state_vars(self, state):
        self.sim_state = state
        t = self.sim_state.t
        buffer_level = self.sim_state.metric.min_buffer_level()
        if self.sim_state.http is not None:
            bps = self.sim_state.http.bps
            self.state_vars.bps_history.append(t, bps)
            self.state_vars.ma4_history.append(t, self.ma4_filter(bps))
            self.state_vars.ma10_history.append(t, self.ma10_filter(bps))
            self.state_vars.ma50_history.append(t, self.ma50_filter(bps))

        self.state_vars.buffer_history.append(t, buffer_level)
        self.state_vars.buffer_ma4_history.append(t, self.buffer_ma4(buffer_level))
        self.state_vars.buffer_ma10_history.append(t, self.buffer_ma10(buffer_level))

        self.my_buffer = self.buffer_ma10

    def predict_next_bps(self):
        # simplest prediction possible: assume next bps is equal to last measured bps
        cur_bps = self.state_vars.ma10_history.current_value
        if cur_bps is None:
            cur_bps = self.segment_choices[0].bps  # assume 50% faster than lowest bitrate
        return cur_bps

    def segment_index_by_bps(self, seg_list, bps):
        next(index for (index, d) in enumerate(seg_list) if d.bps == bps)

    def segment_by_bps(self, seg_list, bps):
        next((x for x in seg_list if x.bps == bps), None)

    def next_higher_bitrate(self, segs, bps_reference):
        for seg in sorted(segs, key=lambda k: k.bps, reverse=False):
            if seg.bps > bps_reference:
               return seg.bps
        return segs[0].bps

    def next_lower_bitrate(self, segs, bps_reference):
        for seg in sorted(segs, key=lambda k: k.bps, reverse=True):
            if seg.bps < bps_reference:
               return seg.bps
        return segs[0].bps

    def next_bitrate(self, type_str, segs):
        index = 0
        # if type_str == "VIDEO":
        #     return segs[3].bps
        # else:
        #     return segs[0].bps

        estimated_bps = self.predict_next_bps()
        cur_level = self.state_vars.buffer_history.current_value
        dur = segs[0].duration_seconds

        bps = []
        for seg in segs:
            dl_time = seg.real_download_time(estimated_bps)
            buffer_delta = seg.duration_seconds - dl_time
            bps.append({'delta': buffer_delta, 'seg': seg})
            bps = sorted(bps, key=lambda k: k['delta'], reverse=True)
            # print "Estimated delta @ %d bps for dur %.2f: %.2f" % (seg.bps, seg.duration_seconds, buffer_delta)
        if cur_level <= self.level_critical_seconds:
            segs_sorted = sorted(self.segment_choices, key=lambda k: k.bps)
            self.selected_bps[type_str] = segs_sorted[0].bps
            self.hold_bps = 5
            if type_str == "VIDEO":
                print "State 0 t=%.2f\nSelected %d bps at time [%.2f]" %(self.sim_state.t, self.selected_bps[type_str], self.sim_state.t)
        elif cur_level <= self.level_low_seconds:
            print "State 1 t=%.2f" % self.sim_state.t
            thr = 0.7 * dur
            # Build buffer state
            # Gradually increases bitrate while making sure the buffer level keeps increasing
            # selects the next higher bitrate segment which would still gain >= 3s buffer time
            if self.hold_bps == 0:
                for x in sorted(ifilter(lambda k: k['delta'] >= thr, bps), key=lambda k: k['seg'].bps, reverse=True):
                    seg = x['seg']
                    delta = x['delta']
                    segs_sorted = sorted(self.segment_choices, key=lambda k: k.bps, reverse=True)
                    buffer_dt = self.state_vars.buffer_ma4_history.y_data[-1] - self.state_vars.buffer_ma4_history.y_data[-2]
                    improve = self.next_higher_bitrate(segs_sorted, seg.bps)
                    if buffer_dt <  -delta:
                        print "Buffer DT: %.4f" % buffer_dt
                        self.selected_bps[type_str] = self.next_lower_bitrate(segs_sorted, self.selected_bps[type_str])
                        self.hold_bps = 1
                    elif improve > self.selected_bps[type_str]:
                        self.selected_bps[type_str] = self.next_higher_bitrate(segs_sorted, self.selected_bps[type_str])
                        self.hold_bps = 1
                    else:
                        self.selected_bps[type_str] = self.next_lower_bitrate(segs_sorted, self.selected_bps[type_str])
                        self.hold_bps = 2
                    if type_str == "VIDEO":
                        print "Selected %d bps at time [%.2f] with delta=%.2f / dur: %.2f / dltime: %.2f / est bps: %d" %(self.selected_bps[type_str], self.sim_state.t, x['delta'], seg.duration_seconds, seg.real_download_time(estimated_bps), estimated_bps)
                    break
                if self.selected_bps[type_str] == 0:
                    self.selected_bps[type_str] = segs[0].bps
                    if type_str == "VIDEO":
                        print "Selected %d bps at time [%.2f]" %(self.selected_bps[type_str], self.sim_state.t)
            self.hold_bps = max(0, self.hold_bps - 1)
        elif cur_level <= self.level_high_seconds:
            print "State 2 t=%.2f" % self.sim_state.t
            if self.hold_bps == 0:
                # Maintain buffer level. Prefer (high+low) / 2
                set_point = (self.level_high_seconds + self.level_low_seconds) / 2.0
                thr = 0.3 * dur
                if cur_level < set_point:
                    candidate_bps = 0
                    for x in sorted(ifilter(lambda k: k['delta'] > 0, bps), key=lambda k: k['seg'].bps, reverse=True):
                        candidate_bps = x['seg'].bps
                        break
                    if candidate_bps != 0:
                        if candidate_bps < self.selected_bps[type_str]:
                            # self.selected_bps[type_str] = self.next_lower_bitrate(segs, self.selected_bps[type_str])
                            pass  # dont lower bitrate until we hit the lower buffer limit
                        elif candidate_bps > self.selected_bps[type_str]:
                            self.selected_bps[type_str] = self.next_higher_bitrate(segs, self.selected_bps[type_str])
                    if type_str == "VIDEO":
                        print "Selected %d bps at time [%.2f]" %(self.selected_bps[type_str], self.sim_state.t)
                    self.hold_bps = 1
            self.hold_bps = max(0, self.hold_bps - 1)
        else:
            print "State 3 t=%.2f" % self.sim_state.t
            segs_sorted = sorted(self.segment_choices, key=lambda k: k.bps, reverse=True)
            self.selected_bps[type_str] = self.next_higher_bitrate(segs_sorted, self.selected_bps[type_str])
            if type_str == "VIDEO":
                print "Selected %d bps at time [%.2f]" %(self.selected_bps[type_str], self.sim_state.t)
        return self.selected_bps[type_str]

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
        self.segment_choices = copy.deepcopy(seg_choices)
        self.update_state_vars(state)

        # sort by bps in descending order
        seg_choices = sorted(self.segment_choices, key=lambda k: k.bps, reverse=False)

        bps = self.next_bitrate(next_segment_type, self.segment_choices)

        if bps != self.bitrate_selections[next_segment_type].current_value:
            # if next_segment_type == "VIDEO" and self.state_vars.bps_history.length > 0:
            #      print "SWITCH @ t=%.2f: %d -> %d [Avg: %.2f / idx: %d]" % (self.sim_state.t, self.bitrate_selections[next_segment_type].current_value, bps, self.state_vars.bps_history.current_value, self.last_index[next_segment_type])

            if next_segment_type == "VIDEO":
                self.bitrate_selections[next_segment_type].append(state.t, bps)

        return Segment.find_segment_for_bitrate(self.segment_choices, bps)


