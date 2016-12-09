#!/usr/bin/python

import sys, csv, re, getopt, collections, calendar, time

csv_mode = False
try:
    from tabulate import tabulate
except ImportError:
    csv_mode = True
    
class Column:
    
    max_int = int('0x7FFFFFFF' , 16)
    min_int = -max_int-1
    datetime_regex = re.compile('^((\d{4}([-/.])(0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12][0-9]|3[01]))|((0?[1-9]|1[0-2])([-/\.])(0?[1-9]|[12][0-9]|3[01])[-/\.]\d{4})|(\d{4}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01]))|((0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])\d{4}))(([\sT])((0?[0-9]|1[0-9]|2[0-3])(:)([0-9]|[0-5][0-9]))(:([0-9]|[0-5][0-9]))?([:\.][0-9]{1,9}Z?)?)?$')
    date_formats = [['yyyy-M-d', '%Y-%m-%d', 1], ['M-d-yyyy', '%m-%d-%Y', 5], ['yyyyMMdd', '%Y%m%d', 9], ['MMddyyyy', '%m%d%Y', 12]] 
    time_formats = [['H:m', '%H:%M'], ['H:m:s', '%H:%M:%S']]
    separator_idx = 16
    time_index = 17
    sec_index = 22
    milli_idx = 23
    date_sparators = [2, 7]
    time_separator = 19
    string_list_max_size = 1001
    
    category_regex = [['Url', 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'],
                      ['Uuid', '[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}'],
                      ['Phone Number', '(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})'],
                      ['Email', '^[\w\.\+\-]+\@([\w]+\.)+[a-z]{2,3}$'],
                      ['IP Address' , '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'],
                      ['SQL', '(?i)^(SELECT|UPDATE|INSERT)[\s\S]+?\;?\s*?$']
                    ]
    
    null_strings = ['', 'NULL', '\N']
    boolean_strings = ['Y', 'N', 'YES', 'NO', 'T', 'F', 'TRUE', 'FALSE', '1', '0']
    
    def __init__(self, name):
        self.name = name
        self.type = 'STRING'
        self.category = ''
        self.rowcount = 0
        self.intcount = 0
        self.floatcount = 0
        self.timestampcount = 0
        self.perc = float('0.0')
        self.string_list = []
        self.int_list = []
        self.timestamp_list = []
        self.total_list_size = 0
        self.min_int_value = sys.maxint
        self.max_int_value = -sys.maxint-1
        self.max_float_size = 0
    
        
    def isInt(self, value):
        try:
            int(value)
            return True
        except ValueError:
            try:
                f = float(value)
                if (f.is_integer()):
                    return True
            except ValueError:
                return False
            return False
        
    def isFloat(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def hasTimePart(self, match):
        return match.groups()[Column.separator_idx - 1] != None
    
    def getTimestampFormat(self, match, jethroFormat):
        dateFormat = ''
        dateSeparator = ''
        separator = ''
        timeFormat = ''
        formatPos = 0
        if jethroFormat == False:
            formatPos = 1
        for df in self.date_formats:
            if match.groups()[df[2]] != None:
                dateFormat = df[formatPos]
                break
        
        if self.hasTimePart(match):
            time_separator = match.groups()[Column.time_separator]
            time_format_idx1 = 0
            time_format_idx2 = 0
            if jethroFormat == False:
                time_format_idx2 = 1
            if match.groups()[Column.sec_index] != None:
                time_format_idx1 = 1
            
            
            timeFormat = Column.time_formats[time_format_idx1][time_format_idx2].replace(':', time_separator)
            milli = match.groups()[self.milli_idx]
            if milli != None:
                if jethroFormat == True:
                    timeFormat += milli[0] + 'S'*(len(milli)-1)
                else:
                    timeFormat += milli[0] + '%f'
                 
            if match.groups()[self.separator_idx] != None:
                separator = match.groups()[self.separator_idx]
            
        
        for ds in self.date_sparators:
            if match.groups()[ds] != None:
                dateSeparator = match.groups()[ds]
                break
        
        return dateFormat.replace('-', dateSeparator) + separator + timeFormat
        
    def getColumnTimstampFormat(self):
        for v in self.timestamp_list:
            match = self.datetime_regex.match(v)
            if match != None:
                break
            
        return self.getTimestampFormat(match, True)
    
    def isValidTimestamp(self, value, match):
        tsFormat = self.getTimestampFormat(match, False)
        if tsFormat != '':
            errMessage = 'unconverted data remains: '
            try:
                tm = time.strptime(value, tsFormat)
            except ValueError as e:
                err = str(e)
                if err.startswith(errMessage):
                    tm = time.strptime(value[:-len(err[len(errMessage):])], tsFormat)
                else:
                    return False
            
            ts = calendar.timegm(tm)
            if ts > 0 and ts < sys.maxint:
                return True
        return False

    def isTimestamp(self, value):
        m = self.datetime_regex.match(value)
        if m != None and self.isValidTimestamp(value, m):
            return True
        else:
            return False
    
    def isPrimaryKey(self):
        if len(self.getValueList()) == self.rowcount and len(self.getExceptionList()) == 0:
            return True
        else:
            return False
        
    def isHighCardinality(self):
        return len(self.getValueList()) >= Column.string_list_max_size
                                                                                                             
    def addDistinct(self, value_list, value):
        if  len(value_list) < Column.string_list_max_size and value not in value_list:
            value_list.append(value)
                
    def addValue(self, value):
        self.rowcount += 1
        if self.isTimestamp(value.rstrip()):
            self.timestampcount += 1
            self.addDistinct(self.timestamp_list, value.rstrip())
        elif self.isInt(value):
            self.intcount += 1
            i = int(float(value))
            if i < self.min_int_value:
                self.min_int_value = i
            if i > self.max_int_value:
                self.max_int_value = i
            self.addDistinct(self.int_list, value.strip())
        elif self.isFloat(value):
            self.floatcount += 1
            if len(value) > self.max_float_size:
                self.max_float_size = len(value)
            self.addDistinct(self.int_list, value.strip())
        else:
            self.addDistinct(self.string_list, value)
    
    def excludeList(self, value_list, exclude_list, casesensitive=True):
        if casesensitive == True:
            return [e for e in value_list if e not in exclude_list]
        else:
            exclude_list = [element.upper() for element in exclude_list]
            return [e for e in value_list if e.upper() not in exclude_list]
            
    def isBoolean(self):
        if self.type != 'TIMESTAMP':
            if len(self.excludeList(self.getValueList(), Column.boolean_strings, False)) == 0:
                return True
        return False
        
    def getCategory(self):
        if self.isBoolean():
            return 'Boolean'
        elif self.type == 'TIMESTAMP':
            for v in self.timestamp_list:
                match = self.datetime_regex.match(v)
                if match != None:
                    break
            
            if self.hasTimePart(match):
                    return 'Datetime'
            return 'Date'
        elif self.type == 'STRING':
            i = 0
            for v in self.string_list:
                if v.upper() not in Column.null_strings:
                    break
                i += 1
            if i == len(self.string_list):
                return ''
               
            regx = []
            for r in Column.category_regex:
                if  re.match(r[1], v) != None:
                    regx = r
                    break
            if regx != []: 
                for v in self.string_list[i + 1:]:
                    if v.upper() not in Column.null_strings and re.match(regx[1], v) == None:
                        return ''
                return regx[0]
        return ''
                
            
            
    def computeType(self):
        if self.floatcount > 0 or self.intcount > 0:
            if self.floatcount > 0:
                if self.max_float_size > 8:
                    self.type = 'DOUBLE'
                else:
                    self.type = 'FLOAT'
            elif self.max_int_value > self.max_int or self.min_int_value < self.min_int:
                self.type = 'BIGINT'
            else:
                self.type = 'INTEGER'
            
            self.perc = (self.intcount + self.floatcount) * 1.0 / self.rowcount
        
        if self.timestampcount > 0:
            perc = self.timestampcount * 1.0 / self.rowcount
            if perc > self.perc:
                self.perc = perc
                self.type = 'TIMESTAMP'
                
        if self.perc == 0.0 or len(self.string_list) > 5:
            self.type = 'STRING'
            self.perc = 1.0
            
        
        self.total_list_size = len(self.int_list) + len(self.timestamp_list) + len(self.string_list)
        self.category = self.getCategory()
        if self.isPrimaryKey() == True:
            if self.category != '':
                self.category += ' - Primary Key'
            else:
                self.category = 'Primary Key'
        elif self.isHighCardinality() == True:
            if self.category != '':
                self.category += ' - High Cardinality'
            else:
                self.category = 'High Cardinality'
                  
    
    def getExceptionList(self):
        if self.type == 'STRING':
            return [e for e in self.string_list if e in Column.null_strings]
        elif self.type == 'TIMESTAMP':
            return self.int_list + self.string_list
        else:
            return self.timestamp_list + self.string_list
    
    def getValueList(self):
        if self.type == 'STRING':
            return self.excludeList(self.string_list, Column.null_strings, False) + self.int_list + self.timestamp_list
        elif self.type == 'TIMESTAMP':
            return self.timestamp_list
        else:
            return self.int_list

        
columns = []
    
def columnsToTable(columns):
    table = []
    i = 1;
    for column in columns:
        column.computeType()
        perc = str(int(column.perc * 100))
        if perc == '0':
            perc = '< 1'
        
        row = [i, column.name, column.rowcount, column.type, column.category, perc, ' '.join('"' + e + '"' for e in column.getExceptionList()[:5])] 
        if  column.total_list_size >= Column.string_list_max_size:
            row.append('> 1000')
        else:
            row.append(str(column.total_list_size))
        row.append(' '.join('"' + e[:50].replace('"', '\\"') + '"' for e in column.getValueList()[:10]))
        table.append(row)  
        i += 1
    return table
    
def analyzeData(inputcsv, delimiter, quotechar='"', with_header=False, number_of_rows=0):
    reader = csv.reader(inputcsv, delimiter=delimiter, quotechar=quotechar)
    header = next(reader)
    ncolumns = len(header)
    global columns
    for c in range(ncolumns):
        if with_header:
            column = Column(header[c])
        else:
            column = Column('c' + str(c + 1))
            column.addValue(header[c])
        columns.append(column)
    
    n = 1
    rot = ['|', '/', '-', '\\']
    for row in reader:
        if n == number_of_rows:
            break
        for  i in range(len(row)):
            if i == ncolumns:
                ncolumns += 1;
                columns.append(Column('c' + str(ncolumns)))
            columns[i].addValue(row[i])
        
        if number_of_rows > 0:
            sys.stderr.write('\r')
            sys.stderr.write("\r" + rot[n % 4])
            sys.stderr.write(" Processing " + str(int((n * 1.0 / number_of_rows) * 100)) + "%..." )
            sys.stderr.flush()
        n += 1   
    
    sys.stderr.write('\r')
    return columnsToTable(columns)


def printReport(table, csvmode=False):
    headers=['Number', 'Name', 'Rows', 'Type', 'Category', 'Percent', 'Exceptions', 'Distinct', 'Samples']
    if csvmode == True:
        print('\t'.join(headers))
        for row in table:
            print('\t'.join(str(e) for e in row))
    else:
        print tabulate(table, headers, tablefmt="psql")

def writeHeaders(ddlfile, descfile, table_name, delimiter, nullStr, with_header):
    ddlfile.write('create table ' + table_name)
    ddlfile.write('\n(\n')
    
    descfile.write('table ' + table_name + '\n')
    descfile.write('row format delimited\n')
    descfile.write("\tfields terminated by '" + delimiter + "'\n")
    descfile.write("\tnull defined as '" + nullStr + "'\n")
    if with_header == True:
        descfile.write("OPTIONS\n\tSKIP 1\n")
    descfile.write('(\n')

def writeFooters(ddlfile, descfile):
    ddlfile.write(');')
    descfile.write(')')
    
def getNullString(columns):
    nulls = collections.Counter()
    for c in columns:
        ex = c.getExceptionList()
        if len(ex) == 1:
            nulls.update(ex)
            
    null = nulls.most_common(1)
    if len(null) > 0:
        return null[0][0]
    else:
        return ''
            
            
def generateSchema(table_name, delimiter, with_header):
    global columns
    ddlfilename = table_name + '.ddl'
    descfilename = table_name + '.desc'
    try:    
        ddlfile = open(ddlfilename, 'w')
        descfile = open(descfilename, 'w')
        
    except IOError:
        print("Failed to open output file ")
        exit(-1)
    
    nullStr = getNullString(columns)
    writeHeaders(ddlfile, descfile, table_name, delimiter, nullStr, with_header)
    
    i = 0
    for c in columns:
        ctype = c.type
        exceptionList = c.getExceptionList()
        if len(exceptionList) > 1:
            ctype = 'STRING'
            
        ddlfile.write(c.name + ' ' + ctype)
        descfile.write(c.name)
        if c.type == 'TIMESTAMP':
            descfile.write(" format='" + c.getColumnTimstampFormat() + "'")
        
        if len(exceptionList) == 1 and exceptionList[0] != nullStr:
            descfile.write(" null defined as '" + exceptionList[0] + "'")
            
        i += 1
        if i < len(columns):
            ddlfile.write(',')
            descfile.write(',')
        
        ddlfile.write('\n')
        descfile.write('\n')
    
    writeFooters(ddlfile, descfile)
        
    ddlfile.close()
    descfile.close()
    
def printUsage():
    sys.stderr.write('AnalyzeData.py [-i <rows to read>] [-d <delimiter>] [-q <quote char>] [-n] [-c] [-g <table name>] [<input file>]\n')
    sys.stderr.write('    -i: Number of rows to read from the input.\n')
    sys.stderr.write('    -d: The input data delimiter.\n')
    sys.stderr.write('    -q: The input data quote character.\n')
    sys.stderr.write('    -n: Indicates whether the first row contains the column names.\n')
    sys.stderr.write('    -c: CSV formatted output. Write the output report as a tab delimited file instead of a formatted table.\n')
    sys.stderr.write('    -g: Generate a create table script and a description file using the given table name.\n')
    sys.stderr.write('    <input file>: The input file to read. If not specified, read from standard input.\n')
    
    
    
def main(argv):
    global csv_mode
    try:
        opts, args = getopt.getopt(argv,"i:d:q:ncg:")
    except getopt.GetoptError:
        printUsage()
        sys.exit(2)
    
    if len(args) == 1 and args[0] == '-h':
        printUsage()
        sys.exit(2)
        
    number_of_rows = 0
    delimiter = ','
    quotechar = '"'
    with_header = False
    csvmode = csv_mode
    table_name = ''
    for opt, arg in opts:
        if opt == '-i':
            try:
                number_of_rows = int(arg)
            except ValueError:
                sys.stderr.write("Invalid number of rows. Must be a number.\n")
        elif opt == '-d':
            delimiter = arg
            if delimiter.startswith('"') or delimiter.startswith("'"):
                delimiter = delimiter[1:-1]
            if len(delimiter) > 1 and not delimiter.startswith('\\'):
                sys.stderr.write("Invalid delimiter. Must be one character.\n")
                sys.exit(2)
        elif opt == '-q':
            quotechar = arg
            if len(quotechar) > 1 and (quotechar.startswith('"') or quotechar.startswith("'")):
                quotechar = quotechar[1:-1]
            if len(quotechar) > 1 and not quotechar.startswith('\\'):
                sys.stderr.write("Invalid quote char. Must be one character.\n")
                sys.exit(2)
        elif opt == '-n':
            with_header = True
        elif opt == '-c':
            csvmode = True
        if opt == '-g':
            table_name = arg

    if len(args) == 0:
        csvfile = sys.stdin
    else:
        csvfile = open(args[0], 'rb')
    
    table = analyzeData(csvfile, delimiter.decode('string_escape'), quotechar, with_header, number_of_rows)
    printReport(table, csvmode)
    if table_name != '':
        generateSchema(table_name, delimiter, with_header)
   
        
if __name__ == '__main__':
    main(sys.argv[1:])