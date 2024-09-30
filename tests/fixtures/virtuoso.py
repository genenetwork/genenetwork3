"""Provide the VIRTUOSO_INI_FILE that will be used to run RDF tests.
here we provide $dir_path as a template variable to set the paths of
various Virtuoso database file.

"""

VIRTUOSO_INI_FILE = """[Database]
DatabaseFile			= $dir_path/virtuoso.db
ErrorLogFile			= $dir_path/virtuoso.log
LockFile			= $dir_path/virtuoso.lck
TransactionFile			= $dir_path/virtuoso.trx
xa_persistent_file		= $dir_path/virtuoso.pxa
ErrorLogLevel			= 7
FileExtend			= 200
MaxCheckpointRemap		= 2000
Striping			= 0
TempStorage			= TempDatabase


[TempDatabase]
DatabaseFile			= $dir_path/virtuoso-temp.db
TransactionFile			= $dir_path/virtuoso-temp.trx
MaxCheckpointRemap		= 2000
Striping			= 0


[Parameters]
ServerPort			= 1112
LiteMode			= 0
DisableUnixSocket		= 1
DisableTcpSocket		= 0

MaxClientConnections		= 10
CheckpointInterval		= 60
O_DIRECT			= 0
CaseMode			= 2
MaxStaticCursorRows		= 5000
CheckpointAuditTrail		= 0
AllowOSCalls			= 0
SchedulerInterval		= 10
ThreadCleanupInterval		= 0
ThreadThreshold			= 10
ResourcesCleanupInterval	= 0
FreeTextBatchSize		= 100000
SingleCPU			= 0
PrefixResultNames               = 0
RdfFreeTextRulesSize		= 100
IndexTreeMaps			= 64
MaxMemPoolSize                  = 200000000
PrefixResultNames               = 0
MacSpotlight                    = 0
MaxQueryMem 		 	= 2G		; memory allocated to query processor
VectorSize 		 	= 1000		; initial parallel query vector (array of query operations) size
MaxVectorSize 		 	= 1000000	; query vector size threshold.
AdjustVectorSize 	 	= 0
ThreadsPerQuery 	 	= 4
AsyncQueueMaxThreads 	 	= 10

NumberOfBuffers          = 10000
MaxDirtyBuffers          = 6000


[HTTPServer]
ServerPort			= 8191
MaxClientConnections		= 10
DavRoot				= DAV
EnabledDavVSP			= 0
HTTPProxyEnabled		= 0
TempASPXDir			= 0
DefaultMailServer		= localhost:25
MaxKeepAlives			= 10
KeepAliveTimeout		= 10
MaxCachedProxyConnections	= 10
ProxyConnectionCacheTimeout	= 15
HTTPThreadSize			= 280000
HttpPrintWarningsInOutput	= 0
Charset				= UTF-8
MaintenancePage             	= atomic.html
EnabledGzipContent          	= 1


[AutoRepair]
BadParentLinks			= 0

[Client]
SQL_PREFETCH_ROWS		= 100
SQL_PREFETCH_BYTES		= 16000
SQL_QUERY_TIMEOUT		= 0
SQL_TXN_TIMEOUT			= 0

[VDB]
ArrayOptimization		= 0
NumArrayParameters		= 10
VDBDisconnectTimeout		= 1000
KeepConnectionOnFixedThread	= 0

[Replication]
ServerName			= db-localhost
ServerEnable			= 1
QueueMax			= 50000

[Striping]
Segment1			= 100M, db-seg1-1.db, db-seg1-2.db
Segment2			= 100M, db-seg2-1.db


[Zero Config]
ServerName			= virtuoso (localhost)


[Mono]


[URIQA]
DynamicLocal			= 0
DefaultHost			= localhost:8890


[SPARQL]
ResultSetMaxRows           	= 10000
MaxConstructTriples		= 10000
MaxQueryCostEstimationTime 	= 400	; in seconds
MaxQueryExecutionTime      	= 600	; in seconds
DefaultQuery               	= select distinct ?Concept where {[] a ?Concept} LIMIT 100
DeferInferenceRulesInit    	= 0  ; controls inference rules loading
MaxMemInUse			= 0  ; limits the amount of memory for construct dict (0=unlimited)

[Plugins]
Load1				= plain, wikiv
Load2				= plain, mediawiki
Load3				= plain, creolewiki
Load8		= plain, shapefileio
Load9		= plain, graphql
"""
