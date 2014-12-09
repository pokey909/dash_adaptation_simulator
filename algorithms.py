__author__ = 'pokey'

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.misc import factorial
from scipy.stats import poisson, norm
import copy
from collections import deque


def moving_average(trace, window_size, opt='valid'):
    out = copy.deepcopy(trace)
    if trace.length == 0:
        out.x_data = []
        out.y_data = []
    else:
        weigths = np.repeat(1.0, window_size) / window_size
        out.y_data = np.convolve(trace.y_data, weigths, opt).tolist()
        missing = len(out.x_data)-len(out.y_data) - 1
        # out.x_data = out.x_data[missing + 1:]
        while missing > 0:
            out.y_data.insert(0, sum(trace.y_data[:missing]) / float(missing+1))
            missing -= 1
        out.y_data.insert(0, 0)
    return out


class IterativeMovingAverage():
    def __init__(self, window):
        assert window == int(window) and window > 0, "Window must be an integer >0"
        self.window = window
        self.stream = deque()

    def __call__(self, n):
        stream = self.stream
        stream.append(n)    # appends on the right
        streamlength = len(stream)
        if streamlength > self.window:
            stream.popleft()
            streamlength -= 1
        if streamlength == 0:
            average = 0
        else:
            average = sum(stream) / streamlength

        return average


def dy_dt(trace, order=1):
    """ n-th discrete derivative """
    data = trace.y_data

    if order > len(data) - 1:
        order = len(data) - 1

    if order < 1:
        return []
    else:
        return np.diff(data, order)


# poisson function, parameter lamb is the fit parameter
def poiss(self, k, lamb):
    return (lamb ** k / factorial(k)) * np.exp(-lamb)


def fit_poisson(self, data):
    # the bins should be of integer width, because poisson is an integer distribution
    entries, bin_edges, patches = plt.hist(data, bins=110, normed=True)
    # calculate binmiddles
    bin_middles = 0.5 * (bin_edges[1:] + bin_edges[:-1])
    # plt.show()
    # fit with curve_fit
    parameters, cov_matrix = curve_fit(self.poiss, bin_middles, entries)
    # plot poisson-deviation with fitted parameter
    # x_plot = np.linspace(0, max(data), 5000)
    # plt.plot(x_plot, self.poiss(x_plot/1000, *parameters), 'r-', lw=2)
    # plt.show()
    return parameters
