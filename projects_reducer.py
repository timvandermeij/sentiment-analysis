import sys

def main():
    sys.stdout.write('{')
    first = True
    for line in sys.stdin:
        if first:
            first = False
        else:
            sys.stdout.write(',')
        parts = line[:-1].split("\t", 2)
        project = parts[1]
        language = parts[2]
        sys.stdout.write(repr(project) + ':' + repr(language))

    sys.stdout.write('}')

if __name__ == "__main__":
    main()
