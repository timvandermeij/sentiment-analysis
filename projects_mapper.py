import sys
import re
import sqlparse

def get_repo(url):
    return re.search(r"repos/([^/]+/[^/]+)(/|$)", url).group(1)

def get_project_langs(mysql_file):
    done = False
    for line in mysql_file:
        if line.startswith('INSERT INTO `projects` VALUES'):
            # TODO: Replace SQL parsing with something quicker
            sql = sqlparse.parse(line)
            tokens = sql[0].tokens
            for i in xrange(8, len(tokens), 2):
                url = str(tokens[i].tokens[1].tokens[2])[1:-1]
                project = get_repo(url)
                language = str(tokens[i].tokens[1].tokens[10])[1:-1]
                print("0\t{}\t{}".format(project, language))

def main():
    get_project_langs(sys.stdin)

if __name__ =="__main__":
    main()
