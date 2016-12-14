'''
Created on Nov 2, 2015

@author: yuvals
'''

import sys
from getopt import getopt, GetoptError
import commands

instance = ''
url = ''
delimiter = ','
nullStr = ''
rejects = 100
tsFormat = 'yyyy-MM-dd'

def sqlCommand(sql):
    global instance, url
    command =  'JethroClient ' + instance + ' ' + url + ' -p jethro --quiet -q '
    output = commands.getoutput(command + sql)
    rows = output.split('\n')
    return rows

def getTableColumns(table):
    sql = '"describe ' + table + '"'
    rows = sqlCommand(sql)
    names = []
    if 'Query failed:' in rows:
        return names

    for row in rows[4:]:
        cols = map(str.strip, row.split('|'))
        if cols[0] != '' and cols[0] != 'Partition by':
            names.append(cols)
            
    return names

def tableToDescFile(table):
    global delimiter, nullStr, rejects
    cols = getTableColumns(table)
    if len(cols) == 0:
        sys.stderr.write('ERROR: No columns found for table ' + table + '\n')
        return
    else:
        print("Creating description file for table " + table + " with columns:")
        for col in cols:
            sys.stdout.write(col[0] + ' ')
        print("")

    outfile = open(table + '.desc', 'w')
    outfile.write("TABLE " + table + "\n")
    outfile.write("row format delimited\n")
    outfile.write("\tfields terminated by '" + delimiter + "'\n")
    outfile.write("\tnull defined as '" + nullStr + "'\n")
    outfile.write("options\n\trow reject limit " + str(rejects) + "\n(\n")

    i = 1
    for col in cols:
        outfile.write("  " + col[0])
        if col[1] == 'TIMESTAMP':
            outfile.write(" format='" + tsFormat + "'")
        if i < len(cols):
            outfile.write(",")
        outfile.write("\n")
        i += 1
    outfile.write(")\n")
    outfile.close()

def main(argv):
    global instance, url, delimiter, nullStr, rejects, tsFormat
    try:
        opts, args = getopt(argv,"i:u:d:n:f:r:")
    except GetoptError:
        sys.stderr.write('TableToDesc.py -i <instance name> -u <Connection URL> [-d <delimiter>] [-n <null string>] [-r <reject limit>] [-f <timstamp format>] [Table name]\n')
        sys.exit(2)

    if len(opts) < 2:
        sys.stderr.write('TableToDesc.py -i <instance name> -u <Connection URL> [-d <delimiter>] [-n <null string>] [-r <reject limit>] [-f <timstamp format>] [Table name]\n')
        sys.exit(2)

    tables = []
    for opt, arg in opts:
        if opt == '-i':
            instance = arg
        elif opt == '-u':
            url = arg
        elif opt == '-d':
            delimiter = arg
        elif opt == '-n':
            nullStr = arg
        elif opt == '-f':
            tsFormat = arg
        elif opt == '-r':
            rejects = int(arg)

    if len(args) > 0:
        tables.append(args[0])
    else:
        sql = '"show tables"'
        tables = sqlCommand(sql)
        tables = map(str.strip, tables[4:])

    for table in tables:
        tableToDescFile(table)

if __name__ == "__main__":
    main(sys.argv[1:])
