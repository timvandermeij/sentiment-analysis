import sys
import os
import numpy as np
import pandas as pd
import matplotlib
# Make it possible to run matplotlib in SSH
NO_DISPLAY = 'DISPLAY' not in os.environ or os.environ['DISPLAY'] == ''
if NO_DISPLAY:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt

def do_plot(name):
    # Finish plotting by saving or showing file.
    if NO_DISPLAY:
        print('Saving plot to {}'.format(name))
        plt.savefig(name)
    else:
        print("Close the plot window to continue.")
        try:
            plt.show()
        except:
            # Sometimes things go wrong in the plot display (such as when 
            # clicking close button too fast), so ignore those errors.
            pass

def main(argv):
    file = argv[0] if len(argv) > 0 else "score.dat"
    plot = argv[1] if len(argv) > 1 else "score.eps"

    M = pd.read_csv(file, delimiter="\t", names=['x','y'])
    # Sort rows on first column's value
    # TODO: Keep groups in account...
    M = M.sort(['x'])

    # widths of bars
    width = (len(M) / 201.) / 100.

    plt.title(file)
    plt.xlabel('score')
    plt.ylabel('frequency')
    plt.grid(True)
    plt.xlim(-1.0,1.0 + width)
    plt.axhline(0, color='black')

    # "Clever" way of showing negative part as negative cumulative part of the 
    # plot and the positive part cumulative from there as well.
    d = -1
    zero = M[M['x'] == 0.00].index[0] # index of zero point
    parts = np.split(M, [zero, zero+1])
    colors = {-1: 'red', 0: 'white', 1: 'green'}
    for p in parts:
        p = p.reset_index(drop=True)
        if d != 0:
            p.loc[0,'y'] *= d

        # Plot the part of the histogram
        # TODO: Step histtype might look better, but for some reason it breaks 
        # matplotlib and would need to change the previous "clever" code
        plt.bar(p['x'].tolist(), p['y'].cumsum().tolist(), color=colors[d],width=width, linewidth=0.5)#, histtype='step')
        d = d + 1

    do_plot(plot)

if __name__ == "__main__":
    main(sys.argv[1:])
