import sys
import os
import json
import numpy as np
import pandas as pd
from math import factorial
import matplotlib
# Make it possible to run matplotlib in SSH
NO_DISPLAY = 'DISPLAY' not in os.environ or os.environ['DISPLAY'] == ''
if NO_DISPLAY:
    matplotlib.use('Agg')
else:
    matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt

class Plot(object):
    def __init__(self, group, data_file):
        self.group = group
        self.data_file = data_file
        self.plot_ext = 'eps'

    def read_data(self, cols):
        return pd.read_csv(self.data_file, delimiter="\t", names=cols)

    def end_plot(self, plot_file):
        # Finish plotting by saving or showing file.
        if NO_DISPLAY:
            print('Saving plot to {}'.format(plot_file + '.' + self.plot_ext))
            plt.savefig(plot_file)
        else:
            print("Close the plot window to continue.")
            sys.stdout.flush()
            try:
                plt.show()
            except:
                # Sometimes things go wrong in the plot display (such as when 
                # clicking close button too fast), so ignore those errors.
                pass

class FreqPlot(Plot):
    def __init__(self, *a):
        super(FreqPlot, self).__init__("score", *a)
        self.title = "Histogram"
        self.bins = 100

    def make_plot(self):
        cols = ['x', 'y']
        D = self.read_data(cols)
        M = D[cols].values
        print(M)

        # Sort rows on first column's value
        M = M[M[:,0].argsort()]

        x = M[:,0]
        y = M[:,1]

        # widths of bars
        window = 101
        width = (len(M) / float(self.bins)) / float(window)

        plt.title(self.title)
        plt.xlabel('score')
        plt.ylabel('frequency')
        plt.grid(True)
        plt.xlim(-1.0,1.0)
        plt.axhline(0, color='black')
        plt.hist(x, self.bins, weights=y, width=width, linewidth=0.5,alpha=0.5)

        # Draw a smooth curve
        # Split the region in two sections (negative, positive) to ensure the 
        # very noisy point of 0.0 is not taken into account in smoothening.
        zero = np.where(x == 0)[0][0]

        yNeg = self.savitzky_golay(y[0:zero], window, 3)
        yPos = self.savitzky_golay(y[zero:-1], window, 3)
        plt.plot(x[0:zero], yNeg, 'r')
        plt.plot(x[zero:-1], yPos, 'g')

        self.end_plot(os.path.splitext(self.data_file)[0])

    # Source: http://wiki.scipy.org/Cookbook/SavitzkyGolay
    def savitzky_golay(self, y, window_size, order, deriv=0, rate=1):
        try:
            window_size = np.abs(np.int(window_size))
            order = np.abs(np.int(order))
        except ValueError:
            raise ValueError("window_size and order have to be of type int")
        if window_size % 2 != 1 or window_size < 1:
            raise TypeError("window_size size must be a positive odd number")
        if window_size < order + 2:
            raise TypeError("window_size is too small for the polynomials order")
        order_range = range(order+1)
        half_window = (window_size -1) // 2
        
        # Precompute coefficients
        b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
        m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
        
        # Pad the signal at the extremes with values taken from the signal itself
        firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
        lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
        y = np.concatenate((firstvals, y, lastvals))
        return np.convolve( m[::-1], y, mode='valid')

class GroupPlot(Plot):
    def __init__(self, *a):
        super(GroupPlot, self).__init__(*a)
        self.title = "Histogram"
        self.sort = True # Positives

    def make_plot(self):
        D = self.read_data([self.group, 'x', 'y'])
        x = []
        yNeg = []
        yPos = []
        for name, group in D.groupby(self.group):
            if name != '' and group.size > 100:
                x.append(name)
                gs = float((group['x'] != 0.0).size)
                yPos.append((group['x'] > 0.0).sum() / gs)
                yNeg.append(-(group['x'] < 0.0).sum() / gs)

        # Sort on positive, take only largest groups
        z = zip(x, yPos, yNeg)
        z.sort(key=lambda v: v[1 if self.sort else 2], reverse=self.sort)
        z = z[0:20]
        (x, yPos, yNeg) = zip(*z)

        width = 0.8
        plt.title(self.title)
        plt.xlabel(self.group)
        plt.ylabel('relative score')
        plt.grid(True)
        plt.axhline(0, color='black')
        xi = np.arange(len(x))
        plt.xticks(xi + width / 2., x, rotation=40)
        plt.bar(xi, yPos, width, color='g')
        plt.bar(xi, yNeg, width, color='r')

        self.end_plot(os.path.splitext(self.data_file)[0])

class AlgoPlot(Plot):
    def __init__(self, *a):
        super(AlgoPlot, self).__init__("algo", 'experiment_results.json', *a)
        self.bar_width = 0.5

    def make_plot(self):
        # Read the data from the experiment results JSON file
        data = {}
        with open(self.data_file, 'r') as results:
            data = json.load(results)

        for algorithm, combinations in data.iteritems():
            average = ()
            std_dev = ()
            for item in combinations.itervalues():
                average = average + (item['average'],)
                std_dev = std_dev + (item['standard_deviation'],)

            # Compose the plot
            x_groups = np.arange(len(combinations))
            fig, ax = plt.subplots()
            rects = ax.bar(x_groups, average, self.bar_width, color='b', ecolor='k', alpha=0.5, yerr=std_dev)

            ax.set_xlabel('Parameters')
            ax.set_ylabel('Accuracy')
            ax.set_title(algorithm)
            ax.set_xticks(x_groups + (self.bar_width / 2.0))
            ax.set_xticklabels(combinations.keys())

            plt.grid(True)
            self.end_plot(os.path.splitext(self.data_file)[0] + '-' + algorithm)

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"
    data_file = argv[1] if len(argv) > 1 else "score.dat"

    if group == "score":
        plot = FreqPlot(data_file)
    elif group == "algo":
        plot = AlgoPlot()
    else:
        plot = GroupPlot(group, data_file)

    plot.make_plot()

if __name__ == "__main__":
    main(sys.argv[1:])
