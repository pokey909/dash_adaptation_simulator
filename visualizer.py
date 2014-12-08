__author__ = 'pokey'

import matplotlib.pyplot as plt
import numpy as np
import copy


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
        rate /= 8000.0
        ax.axhline(y=rate, color='k', linewidth=0.5)

    # plot actual bps history
    bps_x = np.array(bps_traces.x_data)
    bps_y = np.array(bps_traces.y_data) / 1000.0 / 8.0

    print bps_y
    ax.plot(bps_x, bps_y)

    switches_x = switch_traces["VIDEO"].x_data
    switches_y = np.array(switch_traces["VIDEO"].y_data) / 8000.0

    ax.plot(switches_x, switches_y, linewidth=3)

    ax.set_ylabel('bitrate')

    ax1 = ax.twinx()
    ax1.set_ylabel('buffer fullness (sec)', color='k')
    levels_x = buffer_traces["VIDEO"].x_data
    levels_y = buffer_traces["VIDEO"].y_data
    ax.plot(levels_x, levels_y, color='k')

    # plt.ylim(ymin=-5000, ymax=bitrates["VIDEO"][-1] + 10)
    plt.show()

