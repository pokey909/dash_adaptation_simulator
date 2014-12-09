__author__ = 'pokey'

import matplotlib.pyplot as plt
import numpy as np
import copy
import algorithms as alg


def bitswitch_plot(bitrates, buffer_traces, bps_traces, switch_traces):
    # f, axarr = plt.subplots(3, sharex=True)
    # axarr[0].plot(buf["VIDEO"])
    # axarr[1].plot(CastLabsAdaptation.moving_average(adaptation.bps_history, 10))
    # axarr[1].hold(True)
    # axarr[1].plot(adaptation.bitrate_selections["VIDEO"][0], adaptation.bitrate_selections["VIDEO"][1])
    # axarr[1].grid(True)
    # axarr[2].plot(adaptation.bitrate_selections["AUDIO"][0], adaptation.bitrate_selections["AUDIO"][1])
    # axarr[2].grid(True)
    # plt.show()

    # print len(self.ma_bps_history_t())
    # print len(self.ma_bps_history())

    fig, ax = plt.subplots()

    ax.hold(True)
    for rate in bitrates["VIDEO"]:
        rate /= 1000000.0
        ax.axhline(y=rate, color='k', linewidth=0.5)

    # plot actual bps history
    bps = copy.deepcopy(bps_traces)
    bps.y_data = (np.array(bps.y_data) / 1000000.0)

    ax.plot(bps.x_data, bps.y_data)

    ma = alg.moving_average(bps, 50)
    ma2_filter = alg.IterativeMovingAverage(50)
    ma2 = []
    for i in bps_traces.y_data:
        ma2.append(ma2_filter(i / 1000000.0))

    ax.plot(bps.x_data, ma.y_data, color='k', linewidth=3)
    ax.plot(bps.x_data, ma2, color='y', linewidth=3)

    switches_x = switch_traces["VIDEO"].x_data
    switches_y = np.array(switch_traces["VIDEO"].y_data) / 1000000.0

    # draw bitrate switches
    x = []
    y = []
    for i in range(len(switches_x)):
        x.append(switches_x[i])
        y.append(switches_y[i])
        if i+1 < len(switches_x):
            x.append(switches_x[i + 1])
            y.append(switches_y[i])
    ax.plot(x, y, linewidth=5, color='k')

    ax.set_xlabel(bps_traces.x_label, color='k')
    ax.set_ylabel('Mbps')

    ax1 = ax.twinx()
    ax1.set_ylabel(buffer_traces["VIDEO"].y_label, color='k')
    levels_x = buffer_traces["VIDEO"].x_data
    levels_y = np.array(buffer_traces["VIDEO"].y_data)
    ax1.plot(levels_x, levels_y, color='k')

    plt.show()

# x1 x2 x3
# x1 (x2) x2 (x3) x3 (x4)
# y1 y1 y2 y2
def plot(trace, color='b'):
    plt.plot(trace.x_data, trace.y_data, color=color)

def step(trace, ):
    x = []
    y = []

    for i in range(trace.length):
        x.append(trace.x_data[i])
        y.append(trace.y_data[i])
        if i+1 < trace.length:
            x.append(trace.x_data[i + 1])
            y.append(trace.y_data[i])

    plt.plot(x, y, linewidth=3)
    plt.grid(True)

def show():
    plt.show()