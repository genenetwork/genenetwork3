# This script file contains  the an implementation of qtl mapping using r-qtl2
# For r-qtl1 implementation see: Scripts/rqtl_wrapper.R
# load the library

library(qtl2)
library(rjson)
library(stringi)
library(stringr)

options(stringsAsFactors = FALSE)

args = commandArgs(trailingOnly = TRUE)

# get the json file path with pre metadata required to create the cross


if (length(args) == 0) {
  stop("Argument for the metadata file is Missing ", call. = FALSE)
} else {
  json_file_path = args[1]
}

# validation for the json file


if (!(file.exists(json_file_path))) {
  stop("The input file path does not exists")
} else {
  str_glue("The input path for the metadata >>>>>>> {json_file_path}")
  json_data  = fromJSON(file = json_file_path)
}



# generate random string file path here
genRandomFileName <- function(prefix, file_ext = ".txt") {
  randStr = paste(prefix, stri_rand_strings(1, 9, pattern = "[A-Za-z0-9]"), sep =
                    "_")
  return(paste(randStr, file_ext, sep = ""))
}

# this should be read from the json file assigned to variables
# TODO improve on this or use option



# should put constraints for items data required for this
crosstype <- json_data$crosstype
geno_file <- json_data$geno_file
pheno_file <- json_data$pheno_file
geno_map_file <- json_data$geno_map_file
pheno_covar_file <- json_data$phenocovar_file
alleles <- json_data$alleles
founder_geno_file = json_data$founder_geno_file
gmap_file = json_data$gmap_file


# work on the optional parameters

# better fit for reading the data
# make validations

# parsing the required data for example the geno_codes


# geno_codes  handle the geno codes here

# make assertion for the geno_file and the geno_file exists
# make assertion for the physical map file or the geno map file exists

# create temp directory for this workspace
control_file_path  <- file.path("/home/kabui",
                                genRandomFileName(prefix = "control_", file_ext = ".json"))

str_glue("Generated control file path is  {control_file_path}")



# create the cross file here from the arguments provided
# todo add more validation checks here

# issue I can no define the different paths for files for example pheno_file

# think about the issue about geno codes ~~~~
# function to generate a cross file from a json list

generate_cross_object  <- function(json_data) {
  return (
    write_control_file(
      control_file_path,
      crosstype = json_data$crosstype,
      geno_file = json_data$geno_file,
      pheno_file = json_data$pheno_file,
      gmap_file = json_data$geno_map_file,
      phenocovar_file = json_data$phenocovar_file,
      geno_codes = json_data$geno_codes,
      alleles = json_data$alleles,
      na.strings = json_data$na.strings,
      overwrite = TRUE
    )
  )
}


# alternatively pass a  yaml file with
dataset <- write_control_file(
  control_file_path,
  crosstype = crosstype,
  geno_file = geno_file,
  pheno_file = pheno_file,
  gmap_file = geno_map_file,
  phenocovar_file = pheno_covar_file,
  geno_codes = c(L = 1L, C = 2L),
  alleles = alleles,
  na.strings = c("-", "NA"),
  overwrite = TRUE
)

# make validation for the data
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

# Work on computing the genetic probabilities


analysis_type <- "single"


perform_genetic_pr <- function(cross,
                               cores = 1,
                               error_prob = 0.002,
                               analysis_type = "single") {
  # improve on this
  if (analysis_type == "single") {
    pr <- calc_genoprob(cross,
                        error_prob = error_prob,
                        quiet = FALSE,
                        cores = cores)
    return (pr)
  }
}

# get the genetic probability

Pr = perform_genetic_pr(dataset)
cat("Summaries  on the genetic probabilites \n")
print(Pr)
summary(Pr)


#calculate genotyping error LOD scores, to help identify potential genotyping errors (and problem markers and/or individuals
error_lod <- calc_errorlod(dataset, Pr, quiet = FALSE, cores = 4)
print(error_lod)


#  Perform genome scane

# rework on this issue
## grab phenotypes and covariates; ensure that covariates have names attribute
pheno <- dataset$pheno
covar <- match(dataset$covar$sex, c("f", "m")) # make numeric
names(covar) <- rownames(dataset$covar)
Xcovar <- get_x_covar(dataset)

print(pheno)
print(covar)
print(Xcovar)

# rework on fetching th Xcovar and getting the covar data

# perform kinship


perform_genome_scan <- function(cross,
                                genome_prob,
                                method,
                                covar = NULL,
                                xCovar = NULL)
  # perform scan1 using haley-knott regression or linear model, or LOCO linear model
{
  if (method == "LMM") {
    # provide parameters for this
    kinship = calc_kinship(genome_prob)
    out  <- scan1(
      genome_prob,
      cross$pheno,
      kinship = kinship,
      addcovar = covar,
      Xcovar = Xcovar
    )
  }
  
  if (method == "LOCO") {
    # perform kinship inside better option
    kinship = calc_kinship(genome_prob, "loco")
    out <- scan1(
      genome_prob,
      cross$pheno,
      kinship = kinship,
      addcovar = covar,
      Xcovar = Xcovar
    )
  }
  else {
    # perform using Haley Knott
    out <- scan1(genome_prob,
                 cross$pheno,
                 addcovar = NULL,
                 Xcovar = Xcovar)
  }
  return (out)
}

results <- perform_genome_scan(cross = dataset,
                               genome_prob = Pr,
                               method = "HMM")


results # this should probably return the method use here

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

lod_file_path <- generate_lod_plot(dataset, results, "HK")
lod_file_path

# work on 2 pair scan multiple pair scan # multiple pair scan

# Q  how do we perform geno scan with Genome scan with a single-QTL model ????

# perform  permutation tests for single-QTL method


perform_permutation_test <- function(cross,
                                     genome_prob,
                                     n_perm,
                                     method = "HKK",
                                     covar = NULL,
                                     Xcovar = NULL,
                                     perm_strata = NULL) {
  # todo add chr_lengths and perm_Xsp
  
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

# find function to perform the LOD peaks

find_lod_peaks <-function(scan_results, cross, threshold=4,  drop=1.5){
# can this take pmap??? which map should we use???
# TODO add more ags
print("Finding the lod peaks with thresholds n and drop n\n")
return (find_peaks(scan_results, cross$gmap, threshold= threshold, drop=drop))
}

# add the number of cores
lod_peaks <- find_lod_peaks(results, dataset)
print(load_peaks)

# how can we perform qtl effect computations ??? with input from user

# what data should we return to the user

# improve on this script