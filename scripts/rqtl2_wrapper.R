# This script file contains  the an implementation of qtl mapping using r-qtl2
# For r-qtl1 implementation see: Scripts/rqtl_wrapper.R
# load the library

library(qtl2)
library(rjson)
library(stringi)
library(stringr)
library(optparse)



option_list <- list(
  make_option(c("-c", "--cores"), type="integer", default=1, help="No of cores to use while making
  computation"),
make_option(c("-i", "--input_file"), action="store", default=NULL, type='character', help="a yaml or json file with required data to create the cross file"),
make_option(c("-p", "--nperm"), type="integer", default= 1,  action="store_true", help="No  of permutations "),
 make_option(c("-d", "--directory"), action = "store", default = NULL, type = "character", help="Temporary working directory: should also host the input file ."),
 make_option(c("-m", "--method"), action = "store", default = "HK", type = "character", help="Scan Mapping Method - HK (Haley Knott), LMM( Linear Mixed Model ), LOCO (Leave one Chromosome Out)"),
make_option(c("-o", "--output_file"), action="store", default=NULL, type='character', help="a file name of where to write the output json results"),
  make_option(c("--pstrata"), action="store_true", default=NULL, help="Use permutation strata")
)


opt <- parse_args(OptionParser(option_list=option_list))
# check for mandatory args
if(is.null(opt$directory)){
stop("You need  to specify  a working temporary directory which should have be base_dir for the input file")
}

NO_OF_CORES = opt$cores
SCAN_METHOD = opt$method
NO_OF_PERMUTATION = opt$nperm

# get the json file path with pre metadata required to create the cross
# assumption is that the input file should be in the  temp working directory

if (is.null(opt$input_file)) {
  stop("Argument for the Input metadata file is Missing ", call. = FALSE)
} else {
   input_file = opt$input_file
}
if (is.null(opt$output_file)){
stop("You need to provide an output file to write the ouput data")
}

# file_path

input_file_path = file.path(opt$directory, input_file)

if (!(file.exists(input_file_path))) {
  str_glue("The input file {opt$input_file} path does not exists in the directory {opt$directory}")
  stop("The input file does not exists the temp directory")
} else {
  str_glue("The input path for the metadata >>>>>>> {input_file_path}")
  json_data  = fromJSON(file = input_file_path)
}

# generate random string file paths

genRandomFileName <- function(prefix, file_ext = ".txt") {
  randStr = paste(prefix, stri_rand_strings(1, 9, pattern = "[A-Za-z0-9]"), sep =
                    "_")
  return(paste(randStr, file_ext, sep = ""))
}

# TODO work on the optional parameters e.g cores, type of computation

# TODO create temp directory for this workspace pass this as argument

control_file_path  <- file.path(opt$directory,
                                genRandomFileName(prefix = "control_", file_ext = ".json"))

str_glue("Generated control file path is  {control_file_path}")

if (is.null(json_data$sep)){
cat("Using ',' as a default sep for cross file\n")
json_data$sep = ","
}
if (is.null(json_data$na.strings)){
cat("Using '-' and 'NA' as the default na.strings\n")
 json_data$na.strings = c("-" , "NA")
}

# use this better defaults
default_keys = c(
                "geno_transposed", "founder_geno_transposed",
                "pheno_transposed" , "covar_transposed",
		"phenocovar_transposed")

for (item in default_keys) {
if (!(item %in% names(json_data))){
  cat("Using FALSE as default parameter for ", item)
  cat("\n")
  json_data[item] =  FALSE
}
}

generate_cross_object  <- function(json_data) {
 # function to write the cross object from a json data object
  return (
    write_control_file(
      control_file_path,
      crosstype = json_data$crosstype,
      geno_file = json_data$geno_file,
      pheno_file = json_data$pheno_file,
      gmap_file = json_data$geno_map_file,
      pmap_file = json_data$pheno_map_file,
      phenocovar_file = json_data$phenocovar_file,
      geno_codes = json_data$geno_codes,
      alleles = json_data$alleles,
      na.strings = json_data$na.strings,
      geno_transposed = json_data$geno_transposed,
      sex_file = json_data$sex_file,
      founder_geno_file = json_data$founder_geno_file,
      covar_file = json_data$covar_file,
      sex_covar = json_data$sex_covar,
      sex_codes = json_data$sex_codes,
      crossinfo_file = json_data$crossinfo_file,
      crossinfo_covar = json_data$crossinfo_covar,
      crossinfo_codes = json_data$crossinfo_codes,
      xchr = json_data$xchr,
      overwrite = TRUE
    )
  )
}

# generate the cross file

generate_cross_object(json_data)

# read from the cross file path
dataset  <- read_cross2(control_file_path, quiet = FALSE) # replace this with a dynamic path

# check integrity of the cross

cat("Check the integrity of the cross object")
check_cross2(dataset)
if (check_cross2(dataset)) {
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

# Function for  computing the genetic probabilities
perform_genetic_pr <- function(cross,
                               cores = 1,
			       step=1,
			       map=NULL,
			       use_pseudomarkers=FALSE,
			       map_function=c("haldane", "kosambi", "c-f", "morgan"),
                               error_prob = 0.002
                               ) {
    #' Function to calculate the  genetic probabilities
    #' @description function to perform genetic probabilities
    #' @param  cores number no of cores to use Defaults to "1"
    #' @param map  Genetic map of markers.  defaults to "NONE"
    #' @param  use_pseudomarkers option to insert pseudo markers in the gmap default "FALSE"
    #' @param error_prob
    #' @param map_function Character string indicating the map function to use to convert genetic
    #' @param step for  default "1"
    #' @return a list of three-dimensional arrays of probabilities, individuals x genotypes x pst

  cat("Finding the  genetic Probabilities\n")
  if (use_pseudomarkers){
  map <- insert_pseudomarkers(cross$gmap, step=step)
  return(calc_genoprob(cross, map=map,
                       error_prob=error_prob, map_function=map_function,
		       quiet=FALSE, cores=cores))
  }
  else {
      return (calc_genoprob(cross, map=map, error_prob=error_prob,
                           quiet = FALSE, map_function =map_function,
                           cores = cores))
  }}

Pr = perform_genetic_pr(dataset)
cat("Summaries  on the genetic probabilites \n")
print(Pr)
summary(Pr)


#Function to  Calculate genotyping error LOD scores
cat("Calculate genotype error LOD scores\n")
error_lod <- calc_errorlod(dataset, Pr, quiet = FALSE, cores = NO_OF_CORES)
# combine into one matrix
error_lod <- do.call("cbind", error_lod)
print(error_lod)




#  Perform genome scan
# TODO! rework on this issue
## grab phenotypes and covariates; ensure that covariates have names attribute
pheno <- dataset$pheno
covar <- match(dataset$covar$sex, c("f", "m")) # make numeric
names(covar) <- rownames(dataset$covar)
Xcovar <- get_x_covar(dataset)
print(pheno)
print(covar)
print(Xcovar)



# TODO: rework on fetching th Xcovar and getting the covar data

# Function to perform scan1


cat("Computing the kinship")
if (opt$method == "LMM"){
    kinship = calc_kinship(genome_prob)
} else if (opt$method == "LOCO"){
    kinship = calc_kinship(genome_prob, "loco")
}else {
 kinship = NULL
}


perform_genome_scan <- function(cross,
                                genome_prob,
                                method="HK",
                                addcovar = NULL,
				intcovar = NULL,
				kinship = NULL,
				model = c("normal","binary"),
                                Xcovar = NULL) {
    #' perform genome scan
    #' @description  perform scan1 using haley-knott regression, perform scan1 using haley-knott      #'  or linear model, or LOCO linear model
    #' the cross object required to pull the pheno
    #' @param  method to method to perform scan1 either by haley-knott regression(HL),
    #' linear mixed model(LMM) or , for the LOCO method(LOCO)
    #' @param intcovar A numeric optional matrix of interactive covariates.
    #' @param addcovar An optional numeric matrix of additive covariates.
    #' @param Xcovar An optional numeric matrix with additional additive covariates used for null     #'  used for null hypothesis when scanning the X chromosome.
    #' @param model Indicates whether to use a normal model (least squares) or binary model
    #' @return An object of class "scan1"


  if (method == "LMM") {
    # provide parameters for this
    cat("Performing scan1 using Linear mixed model\n")
    out  <- scan1(
      genome_prob,
      cross$pheno,
      kinship = kinship,
      addcovar = covar,
      Xcovar = Xcovar,
      intcovar = intcovar,
      model = model,
      cores = NO_OF_CORES
    )
  }  else if (method == "LOCO") {
    cat("Performing scan1 using Leave one chromosome out\n")
    out <- scan1(
      genome_prob,
      cross$pheno,
      kinship = kinship,
      addcovar = covar,
      intcovar = intcovar,
      model = model,
      Xcovar = Xcovar,
      cores = NO_OF_CORES
    )
  }
  
  else if (method == "HK"){
    cat("Performing scan1 using Haley Knott\n")
    out <- scan1(genome_prob,
                 cross$pheno,
                 addcovar = NULL,
		 intcovar = intcovar,
		 model = model,
                 Xcovar = Xcovar,
		 cores = NO_OF_CORES		 
		 )
  }


  return (out)
}

# Perform the genome scan for the cross object
scan_results <- perform_genome_scan(cross = dataset,
                               genome_prob = Pr,
			       kinship = kinship,
                               method = SCAN_METHOD)

scan_results

# plot for the LOD scores from  performing the genome scan
generate_lod_plot <- function(cross, scan_result, method, base_dir = ".") {
  #' @description Plot LOD curves for a genome scan
  #' @param the cross object
  #' @param scan1 results
  #' @param the method used to compute the scan1 results HK,LMM or LOCO
  #' @param base_dir the path to write the generated plot
  #' @return a string with the file path for the plot
  color <- c("slateblue", "violetred", "green3")
  par(mar = c(4.1, 4.1, 1.6, 1.1))
  ymx <- maxlod(scan_result)
  file_name = genRandomFileName(prefix = "RQTL_LOD_SCORE_", file_ext = ".png")
  image_loc = file.path(base_dir , file_name)
  png(image_loc,
      width = 1000,
      height = 600,
      type = 'cairo-png')
  plot(
    scan_result,
    cross$gmap,
    lodcolumn = 1,
    col = color[1],
    main = colnames(cross$pheno)[1],
    ylim = c(0, ymx * 1.02)
  )
  legend(
    "topleft",
    lwd = 2,
    col = color[1],
    method,
    bg = "gray90",
    lty = c(1, 1, 2)
  )
  dev.off()
  return (image_loc)
}


lod_plot_path <- generate_lod_plot(dataset, scan_results, "HK", base_dir=opt$directory)
lod_plot_path


# perform  permutation tests for single-QTL method

perform_permutation_test <- function(cross,
                                     genome_prob,
                                     n_perm,
                                     method = "HKK",
                                     covar = NULL,
                                     Xcovar = NULL,
				     addcovar = NULL,
				     intcovar = NULL,
				     perm_Xsp = FALSE,
				     kinship = NULL,
				     model = c("normal", "binary"),
				     chr_lengths = NULL,
                                     perm_strata = NULL) {

  #' Function to peform permutation tests for single QTL method
  #' @description The scan1perm() function takes the
  #' same arguments as scan1(), plus additional a #rguments to control the permutations:  
  #' @param cross the cross object required to fetch the pheno
  #' @param genome_prob the genomic probability matrix
  #' @param method to computation method used to perform the genomic scan
  #' @param intcovar
  #' @param addcovar
  #' @param Xcovar
  #' @param perm_Xsp  If TRUE, do separate permutations for the autosomes and the X chromosome.
  #' @param perm_strata Vector of strata, for a stratified permutation test.  
  #' @param n_perm Number of permutation replicates.
  #' @param chr_lengths engths of the chromosomes;
  #' @return  object of class "scan1perm". 
  cat("performing permutation test for the cross object\n")
  return (scan1perm(
      genome_prob,
      cross$pheno,
      kinship = kinship,
      Xcovar = Xcovar,
      intcovar = intcovar,
      addcovar = addcovar,
      n_perm = n_perm,
      perm_Xsp = perm_Xsp,
      model = model,
      chr_lengths = chr_lengths,
      cores = NO_OF_CORES
    ))
}




# check if pstrata

if (!(is.null(opt$pstrata)) && (!is.null(Xcovar))){
perm_strata <- mat2strata(Xcovar)
} else {
perm_strata <- NULL
}

perm <- perform_permutation_test(dataset, Pr, n_perm = NO_OF_PERMUTATION,perm_strata = perm_strata, method = "LMM")

# get the permutation summary with a significance threshold
get_lod_significance <- function(perm, threshold = c(0.2, 0.05)){
      cat("Fetch the lod with significance thresholds ")
      cat(threshold)
      cat("\n")
      summary(perm, alpha = threshold)
}
lod_significance <- get_lod_significance(perm)



# get the lod peaks
# TODO fix issue when fetching the gmap or allow to use pseudomarkers

cat("Fetching the lod peaks\n")
lod_peaks = find_peaks(
  scan_results,
  threshold =0,
  map = dataset$gmap,
  cores = NO_OF_CORES
)

lod_peaks
cat("Generating the ouput data as  vector\n")
output = list(lod_peaks = lod_peaks,
             scan_results =scan_results,
	     lod_significance = lod_significance,
	     permutation_results = perm,
	     lod_peaks = lod_peaks,
	     lod_plot_path =lod_plot_path,
	     scan_method = SCAN_METHOD  
	     )

output_json_data <-toJSON(output)
output_file_path = file.path(opt$directory , opt$output_file)
str_glue("The output file path is  {output_file_path}")
cat("Writing to the output file\n")
write(output_json_data, file=output_file_path)

