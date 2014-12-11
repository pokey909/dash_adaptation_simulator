__author__ = 'pokey'

import matplotlib.pyplot as plt
import numpy as np
import copy
import algorithms as alg


def make_step_paths(arr):
    """
    Makes a list of step line segments from a list of points
    :param arr: list of [x,y] pairs
    :return: list of [x,y] pairs that form a step function for plotting

    >>> make_step_paths([[0,1], [1,2], [2,2], [3,2], [4,1], [5,3], [6,1]])
    [[0, 1], [1, 1], [1, 2], [2, 2], [2, 2], [3, 2], [3, 2], [4, 2], [4, 1], [5, 1], [5, 3], [6, 3], [6, 1]]
    """
    out = []
    for i in range(len(arr)):
        out.append(arr[i])
        if i+1 < len(arr):
            vert = [arr[i+1][0], arr[i][1]]
            out.append(vert)
    return out

def bitswitch_plot(bitrates, buffer_traces, bps_traces, switch_traces):
    fig, ax = plt.subplots()

    ax.hold(True)
    for rate in bitrates["VIDEO"]:
        rate /= 1000000.0
        ax.axhline(y=rate, color='k', linewidth=0.5)

    # plot actual bps history
    bps = copy.deepcopy(bps_traces)
    bps.y_data = (np.array(bps.y_data) / 1000000.0)

    ax.plot(bps.x_data, bps.y_data)

    ma2_filter = alg.IterativeMovingAverage(10)
    ma2 = []
    for i in bps_traces.y_data:
        ma2.append(ma2_filter(i / 1000000.0))

    ax.plot(bps.x_data, ma2, color='y', linewidth=3)

    switches_x = switch_traces["VIDEO"].x_data
    switches_y = np.array(switch_traces["VIDEO"].y_data) / 1000000.0

    print switches_y

    xy = []
    for i in range(len(switches_x)):
        xy.append([switches_x[i], switches_y[i]])

    xy = make_step_paths(xy)

    x = []
    y = []
    for val in xy:
        x.append(val[0])
        y.append(val[1])

    print y
    # draw bitrate switches
    # x = []
    # y = []
    # for i in range(len(switches_x)):
    #     x.append(switches_x[i])
    #     y.append(switches_y[i])
    #     if i+1 < len(switches_x):
    #         x.append(switches_x[i + 1])
    #         y.append(switches_y[i])
    ax.plot(x, y, linewidth=5, color='k')

    ax.set_xlabel(bps_traces.x_label, color='k')
    ax.set_ylabel('Mbps')

    ax1 = ax.twinx()
    ax1.set_ylabel(buffer_traces["VIDEO"].y_label, color='k')
    levels_x = buffer_traces["VIDEO"].x_data
    levels_y = np.array(buffer_traces["VIDEO"].y_data)
    ax1.plot(levels_x, levels_y, color='g', linewidth=2)

    plt.show()

# def plot(trace, color='b'):
#     plt.plot(trace.x_data, trace.y_data, color=color)
#
# def step(trace):
#     x = []
#     y = []
#
#     for i in range(trace.length):
#         x.append(trace.x_data[i])
#         y.append(trace.y_data[i])
#         if i+1 < trace.length:
#             x.append(trace.x_data[i + 1])
#             y.append(trace.y_data[i])
#
#     plt.plot(x, y, linewidth=3)
#     plt.grid(True)
#
# def show():
#     plt.show()


if __name__ == '__main__':
    import doctest
    doctest.testmod()