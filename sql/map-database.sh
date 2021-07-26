#! /bin/sh -e

# This scripts visualizes schema.sql into schema.png and schema.svg. It uses
# sqlt-graph from the perl-sql-transform package. Sadly, perl-sql-transform is
# not packaged for Guix yet. We will likely deprecate this script in favor of
# a custom scheme script that does not depend on perl-sql-transform.

skip_tables=AvgMethod,CeleraINFO_mm6,Chr_Length,DatasetMapInvestigator,DatasetStatus,Dataset_mbat,EnsemblProbe,EnsemblProbeLocation,GORef,GeneCategory,GeneIDXRef,GeneList_rn3,GeneList_rn33,GeneMap_cuiyan,GeneRIFXRef,GenoCode,GenoFile,GenoSE,H2,InfoFiles,InfoFilesUser_md5,LCorrRamin3,RatSnpPattern,Sample,SampleXRef,SnpAllRat,SnpAllele_to_be_deleted,SnpPattern,SnpSource,Vlookup,metadata_audit,pubmedsearch,temporary

clusters="Others=AccessLog,Docs,Investigators,MachineAccessLog,News,Organizations,TableComments,TableFieldAnnotation,User,UserPrivilege,login,role,roles_users,user,user_collection,user_openids"

flags="--db MySQL --skip-tables $skip_tables --cluster $clusters"

sqlt-graph $flags --output-type png --output schema.png schema.sql
sqlt-graph $flags --output-type svg --output schema.svg schema.sql
