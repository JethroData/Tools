#JethroQueryStats

JethroQueryStats parses the jethro server logs, extracts the executed queries and reports statistics about them

###Prerequisites
Python 2.6 or higher installed.


###Run
From the command line, run the command:
Linux: python JethroQueryStats.py parameters
Windows: JethroQueryStats.py parameters

It accepts the following command line parameters:

`-r -j -p file pattern list of files|directories`

####Where
* list of files|directories - The list of log files or directories to parse.

* file pattern - The file pattern to match in the input directories.

* -r - Remove comments from the queries.

* -j - Jenerate the output files in a way that can be loaded to Jethro


JethroQueryStats reads the input files, searches for executed queries and generates a report file named stats.csv. Each row in the file contains the follwoing information about an executed query:

* Query ID - A unique identifier for the query. Queries that were exected more than once, will have the same ID.
* File ID - A unique identifier for the file which the query was found in. It contains file path after removing the largest common prefix.
* Duration - The time in seconds it took to execute the query.
* Change - The duration difference between the last time the same query was executed and the current.
* Execution time - The date and time of the query execution.
* SQL - The executed SQL.

The first row in the file contains a header with the column names.
The file is sorted by query ID where every group of queries with the same query ID are separated by an empty line.

If the `-j` parameter is specified, the output consists of 2 files: stats.csv and queries.csv.
stats.csv is the same as above but without the SQL column, the header and the separating empty lines.
queries.csv contains a line for each unique query. Each line contains the query ID and the SQL.

These 2 files can be loaded into Jethro using the following create table commands and description files:

```
create table stats
(
	query_id int,
	file_id string,
	duration float,
	change float,
	execution_time timestamp
)

create table queries
(
	query_id int,
	sql string
)

table stats
overwrite
	row format delimited
	fields terminated by '|'
(
	query_id,
	file_id,
	duration,
	change,
	execution_time format = 'yyyy-MM-dd HH:mm:ss:SSSSSS'
)

table queries
overwrite
	row format delimited
	fields terminated by '|'
(
	query_id,
	sql
)
```

#ExtractQueries

ExtractQueries parses the jethro server logs and extracts the executed queries together with their execution time and duration.

###Prerequisites
Python 2.6 or higher installed.

###Run
From the command line, run the command:
Linux: python ExtractQueries.py log file
Windows: ExtractQueries.py log file

ExtractQueries reads the input file, searches for executed queries and generates a report file named queries.csv. Each row in the file contains the follwoing information about an executed query:

* Execution time - The date and time of the query execution.
* Duration - The time in seconds it took to execute the query.
* SQL - The executed SQL.


#TableToDesc

TableToDesc reads table defintions from Jethro using the JethroClient, and creates a description file for the table.

###Prerequisites
Python 2.6 or higher installed.
TableToDesc should run on a linux server where jethro is installed.

###Run
From the command line, run the command:
python TableToDesc.py -i instance name -u Connection URL [-d delimiter] [-n null string] [-r reject limit] [-f timstamp format] [Table name]

####where:
* instance name is the name of the jethro instance.
* Connection URL is the Jethro host and port in the form host:port. For example localhost:9111
* delimiter is the delimiter of the raw data. Default=','.
* null string is the null string of the input data. Default is empty string.
* reject limit is the number of rejects to allow before aborting the load. Default=100.
* timstamp format is the format for timstamp columns. Default='yyyy-MM-dd'.
* Table name is an optional table name to create the description file for. If no table name is specified, then a description file will be created to every table in the instance.


#AnalyzeData

AnalyzeData reads a sample of the input data that is going to be loaded into Jethro

#Prerequisites:
Python 2.6 or higher installed.
Python tabulate package (not required if report is issued in csv mode).
To install tabulate:
Linux: 
	`TABULATE_INSTALL=lib-only pip install tabulate`
Windows:
	```
	set TABULATE_INSTALL=lib-only
	pip install tabulate
	```

If pip is not installed:
	```
	wget https://bootstrap.pypa.io/get-pip.py
	python get-pip.py
	```
	
###Run

`AnalyzeData.py [-i <rows to read>] [-d <delimiter>] [-q <quote char>] [-n] [-c] [-g <table name>] [<input file>]`

####Where
* -i: Number of rows to read from the input.
* -d: The input data delimiter.
* -q: The input data quote character.
* -n: Indicates whether the first row contains the column names.
* -c: CSV formatted output. Write the output report as a tab delimited file instead of a formatted table. Installing tabulate is not required in this mode.
* -g: Generate a create table script and a description file using the given table name.
* <input file>: The input file to read. If not specified, read from standard input.
	
The input data is expected to be delimited rows of data. 
The data is read and analyzed and then a report such as the following is generated:
Number | Name | Rows | Type | Category | Percent | Exceptions | Distinct | Samples
------ | ---- | ---- | ---- | -------- | ------- | ---------- | -------- | -------
1 | name | 6 | STRING | Primary Key | 100 | | 6 | "aaa" "bbb" "ccc" "ddd" "eee" "fff"
2 | age | 6 | BIGINT | | 66 | "NULL" | 4 | "1234568674737747372" "-12" "341"
3 | birth date | 6 | TIMESTAMP | Date | 100 | | 5 | "2016-01-07" "2016-12-23" "2016-07-1" "20160714" "2016-07-14"
4 | balance | 6 | DOUBLE | | 83 | "-" | 6 | "1.23" "0.34" "12.0" "11" "0.00000537774"
5 | phone | 6 | STRING | Phone Number | 100 | | 5 | "201 239 3244" "201-345-2136" "" "(212) 435 9884" "917-234-0890"


* Number: The column serial number.
* Name: The column name if the data contains headers. Otherwise is is c1..cN.
* Rows: The number of rows for the column.
* Type: The suggested type to use based on the data. A non string type is suggested in case more than 50% of the values are of that type and there are 5 or less distinct exception values.
* Category: For certain string values, a category can be detected based on regular expressions. It also specifies "Primary Key" in case the column has unique values.
* Percent: The percentage of the values of the suggested type out of all values.
* Exceptions: A list of up to 5 exception values. Exception values are values that do not match the suggested type.
* Distinct: The number of distinct values.
* Samples: Sample values of the suggested type.

In addition, if the -g parameter is specified with a table name, then a create table script and a description file is generated based on the data.
For the above data, the following scripts are generated when given the table name "test":

```
create table test
(
name STRING,
age BIGINT,
birth date TIMESTAMP,
balance DOUBLE,
phone STRING
);

table test
row format delimited
	fields terminated by '|'
	null defined as 'NULL'
OPTIONS
	SKIP 1
(
name,
age,
birth date format='yyyy-M-d',
balance null defined as '-',
phone
)
```

####Notes
* If the suggested type is not STRING, but the exception list has more than one value, then the generated type will become STRING.
* The null definition is based on the most common exception value.
* If a column has a single exception value that is different that the most common null value, then a column specific null definition is generated for that column.
* If the input contains a header row, then a SKIP 1 option is added.
* The timestamp format is generated based on the first timestamp value in the column.





