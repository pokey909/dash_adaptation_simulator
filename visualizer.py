__author__ = 'pokey'

import matplotlib.pyplot as plt

class Visualizer(object):

    def __init__(self):
        pass

    def plot(self, state):
        # f, axarr = plt.subplots(3, sharex=True)
        # axarr[0].plot(buf["VIDEO"])
        # axarr[1].plot(CastLabsAdaptation.moving_average(adaptation.bps_history, 10))
        # axarr[1].hold(True)
        # axarr[1].plot(adaptation.bitrate_selections["VIDEO"][0], adaptation.bitrate_selections["VIDEO"][1])
        # axarr[1].grid(True)
        # axarr[2].plot(adaptation.bitrate_selections["AUDIO"][0], adaptation.bitrate_selections["AUDIO"][1])
        # axarr[2].grid(True)
        # plt.show()

        print len(self.ma_bps_history_t())
        print len(self.ma_bps_history())

        fig, ax1 = plt.subplots()

        ax1.hold(True)
        for rate in self.bitrates["VIDEO"]:
            ax1.axhline(y=rate, color='k', linewidth=0.5)

        # print adaptation.ma_bps_history_t()
        ax1.plot(self.ma_bps_history_t(), adaptation.ma_bps_history())
        switches = self.bitrate_selections["VIDEO"]
        switches[0].append(self.state.t)
        switches[1].append(switches[1][-1])
        ax1.plot(switches[0], switches[1], linewidth=3)

        ax1.set_ylabel('bitrate')

        ax2 = ax1.twinx()
        ax2.set_ylabel('buffer fullness (sec)', color='k')
        levels = self.state.metric.buffer_levels["VIDEO"].to_list()
        #ax2.plot(levels[0], levels[1], color='k')

        plt.ylim(ymin=-5000, ymax=self.bitrates["VIDEO"][-1] + 10)
        plt.show()

