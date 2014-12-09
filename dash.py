__author__ = 'pokey'

from trace import Trace
import random

""" DASH metrics. Time unit is milliseconds """


class Segment:
    def __init__(self, type, bps=0, duration_seconds=0):
        self.duration_seconds = duration_seconds
        self.bps = bps
        self.type_str = type
        self.size_jitter = random.randrange(-5000, 5000, 1)  # add some slight randomness to the size

    @property
    def size(self):
        return int(self.duration_seconds * self.bps / 8.0) + self.size_jitter

    def real_download_time(self, at_bps):
        return self.size / float(at_bps / 8.0)

    def real_bps(self):
        """
        get the minimum required download speed in bps to finish the download in less than the segment duration
        :return: minimum required bps
        """
        exact_bps = 8 * (self.size / float(self.duration_seconds))
        return exact_bps

    @staticmethod
    def find_segment_for_bitrate(segments, bps):
        x = None
        for x in segments:
            if x.bps == bps:
                break
        return x

    def __unicode__(self):
        return "Segment:\n\tDuration:\t%.2f\n\tSize:\t%d\n\tbps:\t%d\n\tDLTime:\t%.2f\n\tRealBps:\t%d" % (
            self.duration_seconds,
            self.size,
            self.bps,
            self.real_download_time(self.real_bps()),
            self.real_bps()
        )

    def __str__(self):
        return self.__unicode__()


class HttpMetric:
    def __init__(self, bps, segment):
        self.bps = bps
        self.segment = segment
        self.http_trace = []
        self.tcp_metric = None
        if self.segment is None:
            self.time_left = 0
        else:
            self.time_left = segment.real_download_time(bps)

    @property
    def duration_ms(self):
        ms = self.segment.real_download_time(self.bps) * 1000.0
        print "DL time: %.2fsec (actual bps: %.2fkbps [downloadTime@%dkbps: %.2fs])  -  Segment(%dkb, %dkbps [%dkb/s]) @ %dkbps [%dkb/s]" % (
            ms / 1000.0,
            self.min_required_dl_speed_bps() / 1000.0,
            self.segment.bps / 1000.0,
            self.steady_state_dl_time_seconds(),
            int(self.segment.size/1000.0),
            self.segment.bps/1000.0,
            self.segment.bps/1000.0/8.0,
            self.bps/1000.0,
            self.bps/1000.0/8)
        return ms

    def steady_state_dl_time_seconds(self):
        return self.segment.real_download_time(self.segment.bps)

    def min_required_dl_speed_bps(self):
        """
        get the minimum required download speed in bps to finish the download in less than the segment duration
        :return: minimum required bps
        """
        return self.segment.real_bps()

    def __unicode__(self):
        return "HttpMetric:\n\tbps: %d\n\tSegment size: %d bytes\n\tDuration sec: %.2f\n\tTime left: %.2f" % (
            self.bps, self.segment.size, self.duration_ms / 1000.0, self.time_left)

    def __str__(self):
        return self.__unicode__()


class BufferLevelMetric(Trace):
    def __init__(self):
        Trace.__init__(self, "seconds", "seconds")
        self._level = 0.0 # in seconds
        self._underruns = Trace("seconds", "underrun duration (seconds)")

    @property
    def underrun_count(self):
        return self._underruns.count

    def increase_by(self, absolute_time, level_increase):
        val = self.current_value
        if val is None:
            val = 0.0
        self.append(absolute_time, val + level_increase)

    def decrease_by(self, absolute_time, level_decrease):
        val = self.current_value
        if val is None:
            val = 0.0
        val -= level_decrease
        if val <= 0.0:
            # record an underrun [time, duration_of_underrun]
            self._underruns.append(absolute_time, abs(val))
            # clamp level to 0.0
            val = 0.0
        self.append(absolute_time, val)

    @property
    def level(self):
        """
        Alias for current_value or current_y_value
        :return: current_y_value
        """
        return self.current_value

    def __unicode__(self):
        val = self.current_value
        if val is not None:
            return "BufferLevel(t=%.2fs): %.2fs" % (self.current_x_value, self.current_value)
        else:
            return "BufferLevel(t=0): 0"

    def __str__(self):
        return self.__unicode__()


class PerformanceMetric:
    def __init__(self):
        self.switches = {"VIDEO": Trace("seconds", "bps"), "AUDIO": Trace("seconds", "bps")}
        self.buffer_levels = {"VIDEO": BufferLevelMetric(), "AUDIO": BufferLevelMetric()}
        self.bps_history = Trace("seconds", "bps")

        self.bps_history.append(0, 0)
        self.buffer_levels["VIDEO"].append(0, 0)
        self.buffer_levels["AUDIO"].append(0, 0)
        self.switches["VIDEO"].append(0, 0)
        self.switches["AUDIO"].append(0, 0)

    @property
    def underrun_count(self):
        return self.buffer_levels["VIDEO"].underrun_count + self.buffer_levels["AUDIO"].underrun_count

    def min_buffer_level(self):
        return min(self.buffer_levels["VIDEO"].current_value, self.buffer_levels["AUDIO"].current_value)

    """ So far, use reciproc of underruns to give a score. 1.0 perfect score """

    def score(self):
        return 1.0 / (self.underrun_count + 1)

    def print_stats(self):
        print("Score: %.4f" % self.score())
        print("Underruns: %d" % self.underrun_count)
        print self.switches["VIDEO"]
        # print("AvgKBPS: %.4f" % np.mean(arr))
