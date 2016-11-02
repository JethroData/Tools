'''
Created on Jul 31, 2015

@author: yuvals
'''
import sys, re

delimiter = '\t'

def removeComments(query):
    new_query = ''
    matches = re.findall("([^/]+)(/\\*[^/]+/)?", query, re.S)
    for m in matches:
        new_query += m[0].strip('\n')
    return new_query

def readQueries(log, outputfile, ignoreComments):
    global queries, rows
   
    matches = re.findall("(?i)(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}:\d+)[^\n]+\nQuery ended=>\s+(SELECT.*?)Total query time: (\d+\.\d{6})", log, re.S)
    for m in matches:
        time = m[0]
        query = m[1]
        duration = m[2]
        
        if ignoreComments and query.find('/*') != -1: 
            query = removeComments(query)
        
        outputfile.write(time + delimiter + duration + delimiter + query.replace('\n', ' ') + "\n")
        
    print "Found " + str(len(matches)) + " matches"

def main(argv):
    if len(argv) == 0:
        print("Missing input log file\n")
        exit(-1)
        
    inputfile = argv[0]
   
    if inputfile == None or inputfile == '':
        print("Missing input log file\n")
        exit(-1)
    
    try:    
        logfile = open(inputfile, "r")
    except IOError:
        print("Failed to open log file " + inputfile + "\n")
        exit(-1)
        
    log = logfile.read()
    logfile.close()
    
    outfile = open("queries.csv", 'w') 
    readQueries(log, outfile, True)    
    outfile.close()
   
if __name__ == "__main__":
    main(sys.argv[1:])
   
   


