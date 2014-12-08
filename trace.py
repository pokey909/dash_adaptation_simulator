__author__ = 'pokey'

import algorithms as alg
import copy


class Trace(object):
    class Axis:
        def __init__(self):
            self._label = ""
            self._data = []

        @property
        def label(self):
            return self._label
        @label.setter
        def label(self, label_str):
            self._label = label_str

        @property
        def data(self):
            return self._data

        @data.setter
        def data(self, dat):
            self._data = dat

    def __init__(self, x_label="", y_label=""):
        self.data = {"x": Trace.Axis(), "y": Trace.Axis()}
        self.data["x"].label = x_label
        self.data["x"].data = []
        self.data["y"].label = y_label
        self.data["y"].data = []

    def __unicode__(self):
        return "__str__ and __unicode__ NOT IMPLEMENTED"

    def __str__(self):
        return self.__unicode__()

    @property
    def max(self):
        return max(self.data["y"].data)

    @property
    def min(self):
        return min(self.data["y"].data)

    @property
    def count(self):
        return len(self.data["x"].data)

    @property
    def length(self):
        return self.count

    @property
    def x_label(self):
        return self.data["x"].label

    @x_label.setter
    def x_label(self, label):
        self.data["x"].label = label

    @property
    def y_label(self):
        return self.data["y"].label

    @y_label.setter
    def y_label(self, label):
        self.data["y"].label = label

    @property
    def x_data(self):
        return self.data["x"].data

    @x_data.setter
    def x_data(self, data):
        self.data["x"].data = data

    @property
    def y_data(self):
        return self.data["y"].data

    @y_data.setter
    def y_data(self, data):
        self.data["y"].data = data

    def append(self, x_data, y_data):
        self.x_data.append(x_data)
        self.y_data.append(y_data)

    @property
    def current_y_value(self):
        if len(self.y_data):
            return self.y_data[-1]
        else:
            return None

    @property
    def current_x_value(self):
        if len(self.x_data):
            return self.x_data[-1]
        else:
            return None

    @property
    def current_value(self):
        return self.current_y_value

    @property
    def current_time(self):
        return self.x_data[-1]

    def moving_average(self, window_size):
        """
        Moving average filter of size window_size
        :param window_size: size of the filter window
        :return: Trace of MA filtered data
        """
        trace = copy.deepcopy(self)
        trace.y_label = self.y_label + " (MA" + str(window_size) + ")"
        trace.y_data = alg.moving_average(self, window_size)
        trace.x_data = trace.x_data[window_size-1:]
        return trace

    def dy_dt(self, order=1):
        """
        Discrete n-th order difference of data trace. I.e. calculate slope of function
        :param order: n-th order difference
        :type order: int
        :return: Trace with length equal to the original minus order
        """
        trace = copy.deepcopy(self)
        trace.y_label = self.y_label + " (dy/dx order=" + str(order) + ")"
        trace.y_data = alg.dy_dt(self, order)
        trace.x_data = trace.x_data[:-order]
        return trace
