library(qtl2)
library(rjson)
library(stringi)
library(optparse)

# Define command-line options
option_list <- list(
  make_option(c("-d", "--directory"), action = "store", default = NULL, type = "character", 
              help = "Temporary working directory: should also host the input file."),
  make_option(c("-i", "--input_file"), action = "store", default = NULL, type = 'character', 
              help = "A YAML or JSON file with required data to create the cross file."),
  make_option(c("-o", "--output_file"), action = "store", default = NULL, type = 'character', 
              help = "A file path of where to write the output JSON results."),
  make_option(c("-c", "--cores"), type = "integer", default = 1, 
              help = "Number of cores to use while making computation."),
  make_option(c("-p", "--nperm"), type = "integer", default = 0, 
              help = "Number of permutations."),
  make_option(c("-m", "--method"), action = "store", default = "HK", type = "character", 
              help = "Scan Mapping Method - HK (Haley Knott), LMM (Linear Mixed Model), LOCO (Leave One Chromosome Out)."),
  make_option(c("--pstrata"), action = "store_true", default = NULL, 
              help = "Use permutation strata."),
  make_option(c("-t", "--threshold"), type = "integer", default = 1, 
              help = "Minimum LOD score for a Peak.")
)

# Parse command-line arguments
opt_parser <- OptionParser(option_list = option_list)
opt <- parse_args(opt_parser)

# Assign parsed arguments to variables
NO_OF_CORES <- opt$cores
SCAN_METHOD <- opt$method
NO_OF_PERMUTATION <- opt$nperm

NO_OF_CORES <- 20

# Validate input and output file paths
validate_file_paths <- function(opt) {
  if (is.null(opt$directory) || !dir.exists(opt$directory)) {
    print_help(opt_parser)
    stop("The working directory does not exist or is NULL.\n")
  }
  
  INPUT_FILE_PATH <- opt$input_file
  OUTPUT_FILE_PATH <- opt$output_file
  
  if (!file.exists(INPUT_FILE_PATH)) {
    print_help(opt_parser)
    stop("The input file ", INPUT_FILE_PATH, " you provided does not exist.\n")
  } else {
    cat("Input file exists. Reading the input file...\n")
  }
  
  if (!file.exists(OUTPUT_FILE_PATH)) {
    print_help(opt_parser)
    stop("The output file ", OUTPUT_FILE_PATH, " you provided does not exist.\n")
  } else {
    cat("Output file exists...", OUTPUT_FILE_PATH, "\n")
  }
  
  return(list(input = INPUT_FILE_PATH, output = OUTPUT_FILE_PATH))
}

file_paths <- validate_file_paths(opt)
INPUT_FILE_PATH <- file_paths$input
OUTPUT_FILE_PATH <- file_paths$output

# Utility function to generate random file names
genRandomFileName <- function(prefix, string_size = 9, file_ext = ".txt") {
  randStr <- paste(prefix, stri_rand_strings(1, string_size, pattern = "[A-Za-z0-9]"), sep = "_")
  return(paste(randStr, file_ext, sep = ""))
}

# Generate control file path
control_file_path <- file.path(opt$directory, genRandomFileName(prefix = "control", file_ext = ".json"))

cat("Generated the control file path at", control_file_path, "\n")
# Read and parse the input file
cat("Reading and parsing the input file.\n")
json_data <- fromJSON(file = INPUT_FILE_PATH)

# Set default values for JSON data
set_default_values <- function(json_data) {
  if (is.null(json_data$sep)) {
    cat("Using ',' as a default separator for cross file.\n")
    json_data$sep <- ","
  }
  if (is.null(json_data$na.strings)) {
    cat("Using '-' and 'NA' as the default na.strings.\n")
    json_data$na.strings <- c("-", "NA")
  }
  
  default_keys <- c("geno_transposed", "founder_geno_transposed", "pheno_transposed", 
                    "covar_transposed", "phenocovar_transposed")
  
  for (item in default_keys) {
    if (!(item %in% names(json_data))) {
      cat("Using FALSE as default parameter for", item, "\n")
      json_data[item] <- FALSE
    }
  }
  
  return(json_data)
}

json_data <- set_default_values(json_data)

# Function to generate the cross object
generate_cross_object <- function(control_file_path, json_data) {
  write_control_file(
    control_file_path,
    crosstype = json_data$crosstype,
    geno_file = json_data$geno_file,
    pheno_file = json_data$pheno_file,
    gmap_file = json_data$geno_map_file,
    pmap_file = json_data$physical_map_file,
    phenocovar_file = json_data$phenocovar_file,
    geno_codes = json_data$geno_codes,
    alleles = json_data$alleles,
    na.strings = json_data$na.strings,
    sex_file = json_data$sex_file,
    founder_geno_file = json_data$founder_geno_file,
    covar_file = json_data$covar_file,
    sex_covar = json_data$sex_covar,
    sex_codes = json_data$sex_codes,
    crossinfo_file = json_data$crossinfo_file,
    crossinfo_covar = json_data$crossinfo_covar,
    crossinfo_codes = json_data$crossinfo_codes,
    xchr = json_data$xchr,
    overwrite = TRUE,
    founder_geno_transposed = json_data$founder_geno_transposed,
    geno_transposed = json_data$geno_transposed
  )
}

# Generate the cross object
cat("Generating the cross object at", control_file_path, "\n")
generate_cross_object(control_file_path, json_data)

# Read the cross object
cat("Reading the cross object from", control_file_path, "\n")

cross <- read_cross2(control_file_path, quiet = FALSE)

# Check the integrity of the cross object
cat("Checking the integrity of the cross object.\n")
if (check_cross2(cross)) {
  cat("Cross meets required specifications for a cross.\n")
} else {
  cat("Cross does not meet required specifications.\n")
}

# Print cross summary
cat("A summary about the cross you provided:\n")
summary(cross)

# Function to compute genetic probabilities
perform_genetic_pr <- function(cross, cores = NO_OF_CORES, step = 1, map = NULL, 
                               map_function = c("haldane", "kosambi", "c-f", "morgan"), 
                               error_prob = 0.002) {
  calc_genoprob(cross, map = map, error_prob = error_prob, map_function = map_function, 
                quiet = FALSE, cores = cores)
}

# Insert pseudomarkers to the genetic map
cat("Inserting pseudomarkers to the genetic map with step 1 and stepwidth fixed.\n")

MAP <- insert_pseudomarkers(cross$gmap, step = 1, stepwidth = "fixed", cores = NO_OF_CORES)

# Calculate genetic probabilities
cat("Calculating the genetic probabilities.\n")
Pr <- perform_genetic_pr(cross, cores=0)

# Calculate allele probabilities for 4-way cross
if (cross$crosstype == "4way") {
  cat("Calculating allele genetic probability for 4-way cross.\n")
  aPr <- genoprob_to_alleleprob(Pr)
}

# Calculate genotyping error LOD scores
cat("Calculating the genotype error LOD scores.\n")
error_lod <- calc_errorlod(cross, Pr, quiet = FALSE, cores = NO_OF_CORES)
error_lod <- do.call("cbind", error_lod)

# Get phenotypes and covariates
cat("Getting the phenotypes and covariates.\n")
pheno <- cross$pheno
# covar <- match(cross$covar$sex, c("f", "m")) # make numeric
# TODO rework on this
covar <- NULL
if (!is.null(covar)) {
  names(covar) <- rownames(cross$covar)
}

Xcovar <- get_x_covar(cross)
cat("The covariates are:\n")
print(covar)
cat("The Xcovar are:\n")
print(Xcovar)

# Function to calculate kinship
get_kinship <- function(probability, method = "LMM") {
  if (method == "LMM") {
    kinship <- calc_kinship(probability)
  } else if (method == "LOCO") {
    kinship <- calc_kinship(probability, "loco")
  } else {
    kinship <- NULL
  }
  return(kinship)
}

# Calculate kinship for the genetic probability
cat("Calculating the kinship for the genetic probability.\n")
if (cross$crosstype == "4way") {
  kinship <- get_kinship(aPr, opt$method)
} else {
  kinship <- get_kinship(Pr, "loco")
}

# Function to perform genome scan
perform_genome_scan <- function(cross, genome_prob, method, addcovar = NULL, intcovar = NULL, 
                                kinship = NULL, model = c("normal", "binary"), Xcovar = NULL) {
  if (method == "LMM") {
    cat("Performing scan1 using Linear Mixed Model.\n")
    out <- scan1(genome_prob, cross$pheno, kinship = kinship, model = model, cores = NO_OF_CORES)
  } else if (method == "LOCO") {
    cat("Performing scan1 using Leave One Chromosome Out.\n")
    out <- scan1(genome_prob, cross$pheno, kinship = kinship, model = model, cores = NO_OF_CORES)
  } else if (method == "HK") {
    cat("Performing scan1 using Haley Knott.\n")
    out <- scan1(genome_prob, cross$pheno, addcovar = addcovar, intcovar = intcovar, 
                 model = model, Xcovar = Xcovar, cores = NO_OF_CORES)
  }
  return(out)
}

# Perform the genome scan for the cross object
if (cross$crosstype == "4way") {
  sex <- setNames((cross$covar$Sex == "male") * 1, rownames(cross$covar))
  scan_results <- perform_genome_scan(aPr, cross, kinship = kinship, method = "LOCO", addcovar = sex)
} else {
  scan_results <- perform_genome_scan(cross = cross, genome_prob = Pr, kinship = kinship, 
                                     method = SCAN_METHOD)
}

# Save scan results
scan_file <- file.path(opt$directory, "scan_results.csv")
write.csv(scan_results, scan_file)

# Function to perform permutation tests
perform_permutation_test <- function(cross, genome_prob, n_perm, method = opt$method, 
                                     covar = NULL, Xcovar = NULL, addcovar = NULL, 
                                     intcovar = NULL, perm_Xsp = FALSE, kinship = NULL, 
                                     model = c("normal", "binary"), chr_lengths = NULL, 
                                     perm_strata = NULL) {
  scan1perm(genome_prob, cross$pheno, kinship = kinship, Xcovar = Xcovar, intcovar = intcovar, 
            addcovar = addcovar, n_perm = n_perm, perm_Xsp = perm_Xsp, model = model, 
            chr_lengths = chr_lengths, cores = NO_OF_CORES)
}

# Check if permutation strata is needed
if (!is.null(opt$pstrata) && !is.null(Xcovar)) {
  perm_strata <- mat2strata(Xcovar)
} else {
  perm_strata <- NULL
}

# Perform permutation test if requested
permutation_results_file <- file.path(opt$directory, "permutation.csv")
significance_results_file <- file.path(opt$directory, "significance.csv")

if (NO_OF_PERMUTATION > 0) {
  cat("Performing permutation test for the cross object with", NO_OF_PERMUTATION, "permutations.\n")
  perm <- perform_permutation_test(cross, Pr, n_perm = NO_OF_PERMUTATION, perm_strata = perm_strata, 
                                   method = opt$method)
  
  # Function to get LOD significance thresholds
  get_lod_significance <- function(perm, thresholds = c(0.01, 0.05, 0.63)) {
    cat("Getting the permutation summary with significance thresholds:", thresholds, "\n")
    summary(perm, alpha = thresholds)
  }
  
  # Compute LOD significance
  lod_significance <- get_lod_significance(perm)
  
  # Save results
  write.csv(lod_significance, significance_results_file)
  write.csv(perm, permutation_results_file)
}



# Function to get QTL effects
get_qtl_effect <- function(chromosome, geno_prob, pheno, covar = NULL, LOCO = NULL) {
  cat("Finding the QTL effect for chromosome", chromosome, "\n")
  chr_Pr <- geno_prob[, chromosome]
  if (!is.null(chr_Pr)) {
    if (!is.null(LOCO)) {
      cat("Finding QTL effect for chromosome", chromosome, "with LOCO.\n")
      kinship <- calc_kinship(chr_Pr, "loco")[[chromosome]]
      return(scan1coef(chr_Pr, pheno, kinship, addcovar = covar))
    } else {
      return(scan1coef(chr_Pr, pheno, addcovar = covar))
    }
  }
  return(NULL)
}

# Get QTL effects for each chromosome
# TODO

# Prepare output data
gmap_file <- file.path(opt$directory, json_data$geno_map_file)
pmap_file <- file.path(opt$directory, json_data$physical_map_file)





# Construct the Map object from cross with columns (Marker, chr, cM, Mb)
gmap <- cross$gmap  # Genetic map in cM
pmap <- cross$pmap  # Physical map in Mb
# Convert lists to data frames
gmap_df <- data.frame(
  marker = unlist(lapply(gmap, names)), 
  chr = rep(names(gmap), sapply(gmap, length)),  # Add chromosome info
  CM = unlist(gmap), 
  stringsAsFactors = FALSE
)

pmap_df <- data.frame(
  marker = unlist(lapply(pmap, names)), 
  chr = rep(names(pmap), sapply(pmap, length)),  # Add chromosome info
  MB = unlist(pmap), 
  stringsAsFactors = FALSE
)
# Merge using full outer join (by marker and chromosome)
merged_map <- merge(gmap_df, pmap_df, by = c("marker", "chr"), all = TRUE)
map_file <- file.path(opt$directory, "map.csv")
write.csv(merged_map, map_file, row.names = FALSE)

output <- list(
  permutation_file = permutation_results_file,
  significance_file = significance_results_file,
  scan_file = scan_file,
  gmap_file = gmap_file,
  pmap_file = pmap_file,
  map_file  = map_file,
  permutations = NO_OF_PERMUTATION,
  scan_method = SCAN_METHOD
)

# Write output to JSON file
output_json_data <- toJSON(output)
cat("The output file path generated is", OUTPUT_FILE_PATH, "\n")
cat("Writing to the output file.\n")
write(output_json_data, file = OUTPUT_FILE_PATH)