# This script file contains  the an implementation of qtl mapping using r-qtl2
# For r-qtl1 implementation see: Scripts/rqtl_wrapper.R
# load the library

library(qtl2)
library(rjson)

library(stringi)
library(optparse)


option_list <- list(
   make_option(c("-d", "--directory"), action = "store", default = NULL, type = "character", help="Temporary working directory: should also host the input file ."),   
make_option(c("-i", "--input_file"), action="store", default=NULL, type='character', help="a yaml or json file with required data to create the cross file"),
 make_option(c("-o", "--output_file"), action="store", default=NULL, type='character', help="a file path  of where to write the output json results"),
   make_option(c("-c", "--cores"), type="integer", default=1, help="No of cores to use while making
  computation"),
  make_option(c("-p", "--nperm"), type="integer", default= 1,  action="store_true", help="No  of permutations "), 
 make_option(c("-m", "--method"), action = "store", default = "HK", type = "character", help="Scan Mapping Method - HK (Haley Knott), LMM( Linear Mixed Model ), LOCO (Leave one Chromosome Out)"),
  make_option(c("--pstrata"), action="store_true", default=NULL, help="Use permutation strata")
)

opt_parser = OptionParser(option_list=option_list);
opt <- parse_args(opt_parser)
NO_OF_CORES = opt$cores
SCAN_METHOD = opt$method
NO_OF_PERMUTATION = opt$nperm

# Step: check for mandatory file paths 
# NOTE this is the working dir where the cross file will be generated 
# NOTE this is where the cross file is generated

if(is.null(opt$directory) || !(dir.exists(opt$directory))){
# check if directory exists
stop("The working directory does not exists or is NULL\n")
}

INPUT_FILE_PATH = opt$input_file
OUTPUT_FILE_PATH = opt$output_file 
if (!(file.exists(INPUT_FILE_PATH))) {
  print_help(opt_parser)
  stop("The input file", INPUT_FILE_PATH, " you provided does not exists\n")
} else {
  cat("Input file exists Reading the input file .... \n")
}
if (!(file.exists(OUTPUT_FILE_PATH))) {
  print_help(opt_parser)
  stop("The output file  ",OUTPUT_FILE_PATH, " you provided does not exists\n")
} else {
  cat("Output file exists ...", OUTPUT_FILE_PATH, "\n")
}

# Utility function to generate random file names of size n:
genRandomFileName <- function(prefix, string_size = 9 , file_ext = ".txt") {
  randStr = paste(prefix, stri_rand_strings(1, string_size, pattern = "[A-Za-z0-9]"), sep =
                    "_")
  return(paste(randStr, file_ext, sep = ""))
}


# Step: Generate the control file name
control_file_path  <- file.path(opt$directory,
                                genRandomFileName(prefix = "control", file_ext = ".json"))
cat("Generated the control file path at ", control_file_path, "\n")


# Step: Reading and Parsing the input file
cat("Reading and parsing the input file \n")
json_data  = fromJSON(file = INPUT_FILE_PATH)
if (is.null(json_data$sep)){
cat("Using ',' as a default sep for cross file\n")
json_data$sep = ","
}
if (is.null(json_data$na.strings)){
cat("Using '-' and 'NA' as the default na.strings\n")
 json_data$na.strings = c("-" , "NA")
}
default_keys = c(
                "geno_transposed", "founder_geno_transposed",
                "pheno_transposed" , "covar_transposed",
		"phenocovar_transposed")

for (item in default_keys) {
if (!(item %in% names(json_data))){
  cat("Using FALSE as default parameter for ", item, "\n")
  json_data[item] =  FALSE
}
}



# Note the files below should be in the same directory as the location for the crosss file
generate_cross_object  <- function(control_file_path, json_data) {
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

# Step: generate the cross file
cat("Generating the cross object at ", control_file_path, "\n")
generate_cross_object(control_file_path, json_data)

cat("reading the cross object from", control_file_path, "\n")
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
                               cores =  NO_OF_CORES,
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


  if (use_pseudomarkers){
  cat("Using pseudo markers for genetic probabilites\n")
  map <- insert_pseudomarkers(cross$gmap, step=step)
  }
  return(calc_genoprob(cross, map=map,
                       error_prob=error_prob, map_function=map_function,
		       quiet=FALSE, cores=cores)) 
}

# Step: calculate the genetic probabilities
cat("Calculating the genetic probabilities\n")
Pr = perform_genetic_pr(dataset)


# Step: perform allele probabilites if cross ways
if (dataset$crosstype == "4way"){
 cat("Calculating Allele Genetic probability for 4way cross\n")
  aPr <- genoprob_to_alleleprob(pr)
}



#Function to  Calculate genotyping error LOD scores
cat("Calculating the  genotype error LOD scores\n")
error_lod <- calc_errorlod(dataset, Pr, quiet = FALSE, cores = NO_OF_CORES)
# combine into one matrix
error_lod <- do.call("cbind", error_lod)




## grab phenotypes and covariates; ensure that covariates have names attribute
# TODO rework on this 
cat("Getting the phenotypes and covariates\n")
pheno <- dataset$pheno

covar <- match(dataset$covar$sex, c("f", "m")) # make numeric
if (!is.null(covar)){
 names(covar) <- rownames(dataset$covar)
}
print("The covariates are")
print(covar)

Xcovar <- get_x_covar(dataset)
print("The Xcovar are ")
print(Xcovar)

#  Function to calculate the kinship 
get_kinship <- function(probability, method="LMM"){
if (opt$method == "LMM"){
    kinship = calc_kinship(genome_prob)
} else if (opt$method == "LOCO"){
    kinship = calc_kinship(genome_prob, "loco")
}else {
 kinship = NULL
}
}


cat("Calculating the kinship for the genetic probability\n")
if (dataset$crosstype == "4way"){
  kinship <- get_kinship(aPr, opt$method)
} else {
   kinship <- get_kinship(Pr, "loco")
}



# Function to perform genome scan
perform_genome_scan <- function(cross,
                                genome_prob,
                                method,
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
if (dataset$crosstype == "4way"){
  sex <- (DOex$covar$Sex == "male")*1
  names(sex) <- rownames(dataset$covar)
  sex <- setNames( (dataset$covar$Sex == "male")*1, rownames(DOex$covar))
  scan_results <- perform_genome_scan(aPr, dataset, kinship=kinship, method = "LOCO", addcovar = sex)  
} else {
  scan_results <- perform_genome_scan(cross = dataset,
                               genome_prob = Pr,
			       kinship = kinship,
                               method = SCAN_METHOD)
}
# function plot for the LOD scores from  performing the genome scan
generate_lod_plot <- function(cross, scan_result, method, base_dir = ".") {
  #' @description Plot LOD curves for a genome scan
  #' @param the cross object
  #' @param scan1 results
  #' @param the method used to compute the scan1 results HK,LMM or LOCO
  #' @param base_dir the path to write the generated plot
  #' @return a string with the file path for the plot
  cat("Generting the lod plot for the LOD scores\n")
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
cat("Generated the lod plot at ", lod_plot_path, "\n")


# function: perform  permutation tests for single-QTL method
perform_permutation_test <- function(cross,
                                     genome_prob,
                                     n_perm,
                                     method =  opt$method,
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
  cat("performing permutation test for the cross object with permutations", n_perm, "\n")
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

# Step: Performing the permutation test
perm <- perform_permutation_test(dataset, Pr, n_perm = NO_OF_PERMUTATION,perm_strata = perm_strata, method = opt$method)


# get the permutation summary with a significance threshold
get_lod_significance <- function(perm, threshold = c(0.2, 0.05)){
     cat("Getting the permutation summary with significance thresholds as ", threshold, "\n")
     summary(perm, alpha = threshold)
}

lod_significance <- get_lod_significance(perm)

# step: get the lod peaks
# TODO fix the threshold here


cat("Fetching the lod peaks\n")
lod_peaks = find_peaks(
  scan_results,
  threshold =0,
  map = dataset$gmap,
  cores = NO_OF_CORES
)


# step: get the estimated qtl effects
get_qtl_effect <- function(chromosome,geno_prob,pheno,covar=NULL,LOCO= NULL){
     cat("Finding the qtl effect\n")
     chr_Pr <- geno_prob[,chromosome]
     if (!is.null(chr_Pr)){
      cat("Finding qtl effect for chromosome ", chromosome, "\n")
     if (!is.null(LOCO)) {
        cat("Finding qtl effect for chromosome ", chromosome, "with LOCO \n")
     kinship <- calc_kinship(chr_Pr, "loco")[[chromosome]]
     return(scan1coef(chr_Pr, pheno, kinship, addcovar=covar))
     }
     else {
      return(scan1coef(chr_Pr, pheno, addcovar=covar))
     }
     }
    return(NULL)
}



# take the first phenotype in the dataset
# grab phenotypes and covariates; ensure that covariates have names attribute

pheno <- dataset$pheno[,1]
if (!is.null(dataset$covar) && !is.null(dataset$covar$sex)){
 covar <- match(dataset$covar$sex, c("f", "m")) # make numeric
 names(covar) <- rownames(dataset$covar)
} else {
covar  <- NULL
}



meffects <- c()
meffects_plots <- c()
# TODO add plots for meffects
for (chr in chr_names(dataset)){
  cat("Getting the qtl effect for chromosome", chr, "\n")
   if (dataset$crosstype == "4way"){
     coeff_results <- get_qtl_effect(chr, aPr, pheno, LOCO="LOCO", covar = sex)
     cat("Generating the qtl effects plots\n")
     file_name = genRandomFileName(prefix = "RQTL_EFFECT_", file_ext = ".png")
     image_loc = file.path(base_dir , file_name)
     par(mar=c(4.1, 4.1, 0.6, 0.6))
       png(image_loc,
      width = 1000,
      height = 600,
      type = 'cairo-png') 
      plot(
      coeff_results,
      cross$gmap[chr],
     bgcolor="gray95",
     legend="bottomleft"
     )
     meffects <- append(meffects_plots, image_loc)
   } else {
    coeff_results  <- get_qtl_effect(chr, Pr, pheno)
   } 
    meffects <- append(meffects, coeff_results)
}
output = list(lod_peaks = lod_peaks,
             scan_results =scan_results,
	     genetic_probabilities = Pr,
	     lod_significance = lod_significance,
	     permutation_results = perm,
	     lod_peaks = lod_peaks,
	     chromosomes  = chr_names(dataset),
	     meffects = meffects,
	     error_lod = error_lod,
	     meffects_plots = meffects_plots,
	     lod_plot_path =lod_plot_path,
	     scan_method = SCAN_METHOD  
	     )
output_json_data <-toJSON(output)
cat("The output file path generated is",  OUTPUT_FILE_PATH, "\n")
cat("Writing to the output file\n")
write(output_json_data, file=OUTPUT_FILE_PATH)

