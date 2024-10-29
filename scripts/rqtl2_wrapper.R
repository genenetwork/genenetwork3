# This script file contains  the an implementation of qtl mapping using r-qtl2
# For r-qtl1 implementation see: Scripts/rqtl_wrapper.R
# load the library

library(qtl2)
library(rjson)
library(stringi)
library(stringr)

options(stringsAsFactors = FALSE)

args = commandArgs(trailingOnly = TRUE)

NO_OF_CORES = 4
SCAN_METHOD = "HK"

# get the json file path with pre metadata required to create the cross

if (length(args) == 0) {
  stop("Argument for the metadata file is Missing ", call. = FALSE)
} else {
  json_file_path = args[1]
}

# TODO validation for the json file


if (!(file.exists(json_file_path))) {
  stop("The input file path does not exists")
} else {
  str_glue("The input path for the metadata >>>>>>> {json_file_path}")
  json_data  = fromJSON(file = json_file_path)
}

# generate random string file paths

genRandomFileName <- function(prefix, file_ext = ".txt") {
  randStr = paste(prefix, stri_rand_strings(1, 9, pattern = "[A-Za-z0-9]"), sep =
                    "_")
  return(paste(randStr, file_ext, sep = ""))
}

# TODO work on the optional parameters e.g cores, type of computation

# TODO create temp directory for this workspace pass this as argument

control_file_path  <- file.path("/home/kabui",
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

perform_genome_scan <- function(cross,
                                genome_prob,
                                method="HK",
                                addcovar = NULL,
				intcovar = NULL,
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
    kinship = calc_kinship(genome_prob)
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
    kinship = calc_kinship(genome_prob, "loco")
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

# TODO rename this to genome scan results 
scan_results <- perform_genome_scan(cross = dataset,
                               genome_prob = Pr,
                               method = SCAN_METHOD)


scan_results

# plot for the LOD scores from  performing the genome scan
generate_lod_plot <- function(cross, scan_result, method, base_dir = ".") {
  # Plot LOD curves for a genome scan
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

lod_file_path <- generate_lod_plot(dataset, scan_results, "HK")
lod_file_path


# Note pair scan does not exists in rqtl2

# perform  permutation tests for single-QTL method
perform_permutation_test <- function(cross,
                                     genome_prob,
                                     n_perm,
                                     method = "HKK",
                                     covar = NULL,
                                     Xcovar = NULL,
                                     perm_strata = NULL) {
				     
  # TODO! add chr_lengths and perm_Xsp

  cat("performing permutation tes for the cross object\n") 
  if (method == "HKK") {
    perm <- scan1perm(
      genome_prob,
      cross$pheno,
      Xcovar = Xcovar,
      n_perm = n_perm,
      perm_strata = perm_strata
    )
  }
  else if (method == "LMM") {
    kinship = calc_kinship(genome_prob)
    perm <- scan1perm(
      genome_prob,
      cross$pheno,
      kinship = kinship,
      Xcovar = Xcovar,
      n_perm = n_perm
    )
  }
  else if (method == "LOCO") {
    kinship = calc_kinship(genome_prob, "loco")
    perm <- scan1perm(
      genome_prob,
      cross$pheno,
      kinship = kinship ,
      perm_strata = perm_strata,
      Xcovar = Xcovar,
      n_perm = n_perm
    )
  }
  return (perm)
}

# TODO ! get these parameters from argument from the user
perm <- perform_permutation_test(dataset, Pr, n_perm = 2, method = "LMM")
# get the permutation summary with a significance threshold
summary(perm, alpha = c(0.2, 0.05))

#  function to perform the LOD peaks

find_lod_peaks <-function(scan_results, cross, threshold=4,  drop=1.5){
# can this take pmap??? which map should we use???
# TODO add more ags
print("Finding the lod peaks with thresholds n and drop n\n")
return (find_peaks(scan_results, cross$gmap, threshold= threshold, drop=drop))
}
# TODO! add the number of cores
lod_peaks <- find_lod_peaks(scan_results, dataset)
print(lod_peaks)

# TODO! format to return the data ??? 