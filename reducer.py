import sys

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"

    last_group = None
    last_score = None
    count = 0
    for line in sys.stdin:
        parts = line[:-1].split('\t')
        g = parts[0]
        s = parts[1] if group != "score" else g
        if (last_group is not None and g != last_group) or \
           (last_score is not None and s != last_score):
            print("{}\t{}".format("{}\t{}".format(last_group, last_score) if group != "score" else last_group, count))
            count = 0

        last_group = g
        last_score = s
        count = count + 1

    if last_group is not None:
        print("{}\t{}".format("{}\t{}".format(last_group, last_score) if group != "score" else last_group, count))

if __name__ == "__main__":
    main(sys.argv[1:])
