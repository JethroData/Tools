import sys
from os import listdir
from os.path import join, isfile, dirname
import re, fnmatch

from itertools import takewhile
from getopt import getopt, GetoptError
from operator import itemgetter

queries = []
rows = []

delimiter = '\t'

def allnamesequal(name):
    return all(n==name[0] for n in name[1:])

def commonprefix(paths, sep='/'):
    prefix = ''
    if len(paths) == 1:
        prefix = dirname(paths[0])
    else:
        bydirectorylevels = zip(*[p.split(sep) for p in paths])
        prefix =  sep.join(x[0] for x in takewhile(allnamesequal, bydirectorylevels))
    return prefix
        
def getFilePaths(path, pattern):
    files = []
    if isfile(path):
        files.append(path)
    else:
        files = [ join(path,f) for f in listdir(path) if isfile(join(path,f)) and (pattern == '' or fnmatch.fnmatch(f, pattern)) ]
        
    return files

def removeComments(query):
    new_query = ''
    matches = re.findall("([^/]+)(/\\*[^/]+/)?", query, re.S)
    for m in matches:
        new_query += m[0].strip('\n')
        
    return new_query
        
def readQueries(inputfile, prefix, ignoreComments):
    global queries, rows
    logfile = open(inputfile, "r")
   
    log = logfile.read()
    logfile.close()
   
    fileId = inputfile[len(prefix) + 1:]
    matches = re.findall("(?i)(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}:\d+)[^\n]+\nQuery ended=>\s+(SELECT.*?)Total query time: (\d+\.\d{6})", log, re.S)
    for m in matches:
        time = m[0]
        query = m[1]
        duration = m[2]
        
        if ignoreComments and query.find('/*') != -1: 
            query = removeComments(query)
        
        if query not in queries:
            queries.append(query)
        
        qid = queries.index(query) + 1
        rows.append((qid, fileId, duration, time))
        
    print "Found " + str(len(matches)) + " matches in " + fileId
  
def writeRows(forJethro):
    global queries, rows
    rows = sorted(rows, key=itemgetter(2), reverse=True )
    rows = sorted(rows, key=itemgetter(0))
    
    outfile = open("stats.csv", 'w')
    if forJethro == False:
        outfile.write("Query ID" + delimiter + "File ID" + delimiter + "Duration" + delimiter + "Change" + delimiter + "Execution Time" + delimiter + "SQL\n")
    
    last_id = 1
    last_duration = 0
    
    for row in rows:
        qid = row[0]
        duration = float(row[2])
        if qid > last_id:
            last_id = qid
            last_duration = 0
        change = ''
        if last_duration > 0:
            '''change = str(round(((duration / last_duration) - 1) * 100, 2))'''
            change = str(duration - last_duration)
        last_duration = duration
        if qid > last_id:
            if forJethro == False:
                outfile.write(delimiter + delimiter + delimiter + delimiter + delimiter + "\n")
            last_id = qid
        query = queries[qid - 1]
        if forJethro == False:
            outfile.write(str(qid) + delimiter + row[1] + delimiter  + str(duration) + delimiter + change + delimiter + row[3] +  delimiter + query.replace('\n', ' ')  + "\n")
        else:
            outfile.write(str(qid) + delimiter + row[1] + delimiter  + str(duration) + delimiter + change + delimiter + row[3] +  "\n")
            
    outfile.close()
    
def writeQueries():
    global queries
    outfile = open("queries.csv", 'w')
    qid = 1
    for query in queries:
        outfile.write(str(qid) + delimiter + query.replace('\n', ' ') + '\n')
        qid += 1
    outfile.close()
    
    
def main(argv):
    try:
        opts, args = getopt(argv, 'p:rj')
    except GetoptError:
        print('JethroQueryStats.py [-r][-j][-p <file pattern>] <list of files|directories>\n')
        sys.exit(2)
        
    ignoreComments = False
    forJethro = False
    files = []
    pattern = ''
    for opt, arg in opts:
        if opt == '-p':
            pattern = arg
        elif opt == '-r':
            ignoreComments = True
        elif opt == '-j':
            forJethro = True
            
    
    if len(args) == 0:
        print('JethroQueryStats.py [-r][-j][-p <file pattern>] <list of files|directories>\n')
        sys.exit(2)
        
    for inputfile in args:
        files.extend(getFilePaths(inputfile, pattern))
    
    prefix = commonprefix(files, '\\')
    
    
    for f in files:
        readQueries(f, prefix, ignoreComments)
    writeRows(forJethro)
    if forJethro == True:
        writeQueries()
   
if __name__ == "__main__":
    main(sys.argv[1:])
   
   


