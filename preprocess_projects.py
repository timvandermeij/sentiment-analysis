import sys
import gzip
import sqlparse

def main(argv):
    mysql_file = argv[0] if len(argv) > 0 else "projects.sql.gz"

    done = False
    langs = {}
    l = 0
    with gzip.open(mysql_file, 'rb') as f:
        for line in f:
            l = l + 1
            if line.startswith('INSERT INTO `projects` VALUES'):
                sql = sqlparse.parse(line)
                tokens = sql[0].tokens
                for i in xrange(8, len(tokens), 2):
                    project = str(tokens[i].tokens[1].tokens[2])[1:-1]
                    language = str(tokens[i].tokens[1].tokens[10])[1:-1]
                    # We could convert language to int using 
                    # https://raw.githubusercontent.com/github/linguist/master/lib/linguist/languages.yml
                    # That could save space but is not very worthwhile.
                    langs[project] = language

                done = True
                print('Line {}'.format(l))
            elif done:
                break

    print(langs)

if __name__ == "__main__":
    main(sys.argv[1:])
