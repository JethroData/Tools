#JethroQueryStats

JethroQueryStats parses the jethro server logs, extracts the executed queries and reports statistics about them

Prerequisites:
Python 2.6 or higher installed.


Run:
From the command line, run the command:
Linux: python JethroQueryStats.py parameters
Windows: JethroQueryStats.py parameters

It accepts the following command line parameters:

-r -j -p file pattern list of files|directories

Where:
list of files|directories - The list of log files or directories to parse.

file pattern - The file pattern to match in the input directories.

-r - Remove comments from the queries.

-j - Jenerate the output files in a way that can be loaded to Jethro


JethroQueryStats reads the input files, searches for executed queries and generates a report file named stats.csv. Each row in the file contains the follwoing information about an executed query:

- Query ID - A unique identifier for the query. Queries that were exected more than once, will have the same ID.
- File ID - A unique identifier for the file which the query was found in. It contains file path after removing the largest common prefix.
- Duration - The time in seconds it took to execute the query.
- Change - The duration difference between the last time the same query was executed and the current.
- Execution time - The date and time of the query execution.
- SQL - The executed SQL.

The first row in the file contains a header with the column names.
The file is sorted by query ID where every group of queries with the same query ID are separated by an empty line.

If the -j parameter is specified, the output consists of 2 files: stats.csv and queries.csv.
stats.csv is the same as above but without the SQL column, the header and the separating empty lines.
queries.csv contains a line for each unique query. Each line contains the query ID and the SQL.

These 2 files can be loaded into Jethro using the following create table commands and description files:

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


#ExtractQueries

ExtractQueries parses the jethro server logs and extracts the executed queries together with their execution time and duration.

Prerequisites:
Python 2.6 or higher installed.


Run:
From the command line, run the command:
Linux: python ExtractQueries.py log file
Windows: ExtractQueries.py log file

ExtractQueries reads the input file, searches for executed queries and generates a report file named queries.csv. Each row in the file contains the follwoing information about an executed query:

- Execution time - The date and time of the query execution.
- Duration - The time in seconds it took to execute the query.
- SQL - The executed SQL.


#TableToDesc

TableToDesc reads table defintions from Jethro using the JethroClient, and creates a description file for the table.

Prerequisites:
Python 2.6 or higher installed.
TableToDesc should run on a linux server where jethro is installed.

Run:
From the command line, run the command:
python TableToDesc.py -i instance name -u Connection URL [-d delimiter] [-n null string] [-r reject limit] [-f timstamp format] [Table name]

where:
instance name is the name of the jethro instance.
Connection URL is the Jethro host and port in the form host:port. For example localhost:9111
delimiter is the delimiter of the raw data. Default=','.
null string is the null string of the input data. Default is empty string.
reject limit is the number of rejects to allow before aborting the load. Default=100.
timstamp format is the format for timstamp columns. Default='yyyy-MM-dd'.
Table name is an optional table name to create the description file for. If no table name is specified, then a description file will be created to every table in the instance.







