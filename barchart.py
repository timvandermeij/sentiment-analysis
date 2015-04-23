import sys
import json
import numpy as np
import matplotlib.pyplot as plt

def main(argv):
    bar_width = 0.5
    
    # Read the data from the experiment results JSON file
    data = {}
    with open('experiment_results.json', 'r') as results:
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
        rects = ax.bar(x_groups, average, bar_width, color='b', ecolor='k', alpha=0.5, yerr=std_dev)

        ax.set_xlabel('Parameters')
        ax.set_ylabel('Accuracy')
        ax.set_title(algorithm)
        ax.set_xticks(x_groups + (bar_width / 2.0))
        ax.set_xticklabels(combinations.keys())

        plt.grid(True)
        plt.show()

if __name__ == "__main__":
    main(sys.argv[1:])
