# This script file contains  the an implementation of qtl mapping using r-qtl2
# For r-qtl1 implementation see: Scripts/rqtl_wrapper.R
# load the library

library(qtl2)
library(rjson)
library(stringi)
library(stringr)

options(stringsAsFactors = FALSE);
args = commandArgs(trailingOnly=TRUE)

# get the json file path with pre metadata required to create the cross


if (length(args)==0) {
  stop("Argument for the metadata file is Missing ", call.=FALSE)
} else {

  json_file_path = args[1]
  # convert this to an absolute file path 
  
}

# validation for the json file 
if (!(file.exists(json_file_path))) {
   stop("The input file path does not exists")
} else {
str_glue("The input path for the metadata >>>>>>> {json_file_path}")
json_data  = fromJSON(file = json_file_path)
}


# generate random string file path here
genRandomFileName <- function(prefix,file_ext=".txt"){

	randStr = paste(prefix,stri_rand_strings(1, 9, pattern = "[A-Za-z0-9]"),sep="_")

	return(paste(randStr,file_ext,sep=""))
}

# this should be read from the json file assigned to variables
# TODO improve on this or use option


crosstype <- json_data$crosstype
geno_file <- json_data$geno_file
pheno_file <- json_data$pheno_file
geno_map_file <- json_data$geno_map_file 
pheno_covar_file <- json_data$phenocovar_file
alleles <- json_data$alleles

# geno_codes  handle the geno codes here 

# make assertion for the geno_file and the geno_file exists
# make assertion for the physical map file or the geno map file exists

# create temp directory for this workspace 
control_file_path  <- file.path("/home/kabui", genRandomFileName(prefix="control_", file_ext=".json"))

str_glue(
  "Generated control file path is  {control_file_path}"
)



# create the cross file here from the arguments provided
# todo add more validation checks here 

# issue I can no define the different paths for files for example pheno_file 

dataset <- write_control_file(control_file_path,
    crosstype= crosstype,
    geno_file= geno_file,
    pheno_file= pheno_file,    
    gmap_file= geno_map_file,
    phenocovar_file= pheno_covar_file,
    geno_codes=c(L=1L, C=2L),
    alleles= alleles,    
    na.strings=c("-", "NA"),
    overwrite = TRUE)


# make validation for the data
dataset  <- read_cross2(control_file_path, quiet = FALSE) # replace this with a dynamic path

# check integrity of the cross
cat("Check the integrity of the cross object")
check_cross2(dataset)
if (check_cross2(dataset)){
  print("Dataset meets required specifications for a cross")
} else {
  print("Dataset does not meet required specifications")
}

# Dataset Summarys 
cat("A Summary about the Dataset You Provided\n")
summary(dataset)
n_ind(dataset)
n_chr(dataset)
cat("names of markers in the  object\n")
marker_names(dataset)
cat("names of phenotypes in a the object")
pheno_names(dataset)
cat("IDs for all individuals in the dataset cross object that have genotype data\n")
ind_ids_geno(dataset)
cat(" IDs for all individuals in the dataset object that have phenotype data")
ind_ids_pheno(dataset)
cat("Name of the founder Strains/n")
founders(dataset)
