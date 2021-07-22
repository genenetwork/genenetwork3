library(optparse)
library(qtl)
library(stringi)
library(stringr)

tmp_dir = Sys.getenv("TMPDIR")

option_list = list(
  make_option(c("-g", "--geno"), type="character", help=".geno file containing a dataset's genotypes"),
  make_option(c("-p", "--pheno"), type="character", help="File containing two columns - sample names and values"),
  make_option(c("-c", "--addcovar"), action="store_true", default=NULL, help="Use covariates (included as extra columns in the phenotype input file)"),
  make_option(c("--model"), type="character", default="normal", help="Mapping Model - Normal or Non-Parametric"),
  make_option(c("--method"), type="character", default="hk", help="Mapping Method - hk (Haley Knott), ehk (Extended Haley Knott), mr (Marker Regression), em (Expectation-Maximization), imp (Imputation)"),
  make_option(c("--pairscan"), action="store_true", default=NULL, help="Run Pair Scan - the R/qtl function scantwo"),
  make_option(c("-i", "--interval"), action="store_true", default=NULL, help="Use interval mapping"),
  make_option(c("--nperm"), type="integer", default=0, help="Number of permutations"),
  make_option(c("--pstrata"), action="store_true", default=NULL, help="Use permutation strata (stored as final column/vector in phenotype input file)"),
  make_option(c("-s", "--scale"), type="character", default="mb", help="Mapping scale - Megabases (Mb) or Centimorgans (cM)"),
  make_option(c("--control"), type="character", default=NULL, help="Name of marker (contained in genotype file) to be used as a control"),
  make_option(c("-o", "--outdir"), type="character", default=file.path(tmp_dir, "output"), help="Directory in which to write result file"),
  make_option(c("-f", "--filename"), type="character", default=NULL, help="Name to use for result file"),
  make_option(c("-v", "--verbose"), action="store_true", default=NULL, help="Show extra information")
);

opt_parser = OptionParser(option_list=option_list);
opt = parse_args(opt_parser);

verbose_print <- function(...){
  if (!is.null(opt$verbose)) {
    for(item in list(...)){
      cat(item)
    }
    cat("\n")
  }
}

if (is.null(opt$geno) || is.null(opt$pheno)){
  print_help(opt_parser)
  stop("Both a genotype and phenotype file must be provided.", call.=FALSE)
}

geno_file = opt$geno
pheno_file = opt$pheno

# Generate randomized filename for cross object
cross_file = file.path(tmp_dir, "cross", paste(stri_rand_strings(1, 8), ".cross", sep = ""))

trim <- function( x ) { gsub("(^[[:space:]]+|[[:space:]]+$)", "", x) }

get_geno_code <- function(header, name = 'unk'){
  mat = which(unlist(lapply(header,function(x){ length(grep(paste('@',name,sep=''), x)) })) == 1)
  return(trim(strsplit(header[mat],':')[[1]][2]))
}

geno_to_csvr <- function(genotypes, trait_names, trait_vals, out, sex = NULL,
                         mapping_scale = "Mb", verbose = FALSE){
  # Assume a geno header is not longer than 40 lines
  header = readLines(genotypes, 40)

  # Major hack to skip the geno headers
  toskip = which(unlist(lapply(header, function(x){ length(grep("Chr\t", x)) })) == 1) - 1

  type <- get_geno_code(header, 'type')

  # Get the genotype codes
  if(type == '4-way'){
    genocodes <- NULL
  } else {
    genocodes <- c(get_geno_code(header, 'mat'), get_geno_code(header, 'het'),
                   get_geno_code(header, 'pat'))
  }
  genodata <- read.csv(genotypes, sep='\t', skip=toskip, header=TRUE,
                       na.strings=get_geno_code(header,'unk'),
                       colClasses='character', comment.char = '#')

  verbose_print('Genodata:', toskip, " ", dim(genodata), genocodes, '\n')

  # If there isn't a sex phenotype, treat all as males
  if(is.null(sex)) sex <- rep('m', (ncol(genodata)-4))

  cross_items = list()

  # Add trait and covar phenotypes
  for (i in 1:length(trait_names)){
    cross_items[[i]] <- c(trait_names[i], '', '', unlist(trait_vals[[i]]))
  }

  # Sex phenotype for the mice
  cross_items[[length(trait_names) + 1]] <- c('sex', '', '', sex)
  # Genotypes
  cross_items[[length(trait_names) + 2]] <- cbind(genodata[,c('Locus','Chr', mapping_scale)],
                                                  genodata[, 5:ncol(genodata)])

  out_csvr <- do.call(rbind, cross_items)

  # Save it to a file
  write.table(out_csvr, file=out, row.names=FALSE, col.names=FALSE, quote=FALSE, sep=',')

  # Load the created cross file using R/qtl read.cross
  if (type == '4-way') {
    verbose_print('Loading in as 4-WAY\n')
    cross = read.cross(file=out, 'csvr', genotypes=NULL, crosstype="4way")
  } else if(type == 'f2') {
    verbose_print('Loading in as F2\n')
    cross = read.cross(file=out, 'csvr', genotypes=genocodes, crosstype="f2")
  } else {
    verbose_print('Loading in as normal\n')
    cross = read.cross(file=out, 'csvr', genotypes=genocodes)
  }
  if (type == 'riset') {
    # If its a RIL, convert to a RIL in R/qtl
    verbose_print('Converting to RISELF\n')
    cross <- convert2riself(cross)
  }

  return(cross)
}

create_marker_covars <- function(the_cross, control_marker){
  #' Given a string of one or more marker names (comma separated), fetch
  #' the markers' values from the genotypes and return them as vectors/a vector
  #' of values

  # In case spaces are added in the string of marker names
  covariate_names <- strsplit(str_replace(control_marker, " ", ""), ",")

  genotypes <- pull.geno(the_cross)
  covariates_in_geno <- which(covariate_names %in% colnames(genotypes))
  covariate_names <- covariate_names[covariates_in_geno]
  marker_covars <- genotypes[, unlist(covariate_names)]

  return(marker_covars)
}

# Get phenotype vector from input file
df <- read.table(pheno_file, na.strings = "x", header=TRUE, check.names=FALSE)
sample_names <- df$Sample
trait_names <- colnames(df)[2:length(colnames(df))]

# Since there will always only be one non-covar phenotype, its name will be in the first column
pheno_name = unlist(trait_names)[1]

trait_vals <- vector(mode = "list", length = length(trait_names))
for (i in 1:length(trait_names)) {
  this_trait <- trait_names[i]
  this_vals <- df[this_trait]
  trait_vals[[i]] <- this_vals

  trait_names[i] = paste("T_", this_trait, sep = "")
}

verbose_print('Generating cross object\n')
cross_object = geno_to_csvr(geno_file, trait_names, trait_vals, cross_file)

# Calculate genotype probabilities
if (!is.null(opt$interval)) {
  verbose_print('Calculating genotype probabilities with interval mapping\n')
  cross_object <- calc.genoprob(cross_object, step=5, stepwidth="max")
} else {
  verbose_print('Calculating genotype probabilities\n')
  cross_object <- calc.genoprob(cross_object)
}

# Pull covariates out of cross object, if they exist
covars = vector(mode = "list", length = length(trait_names) - 1)
if (!is.null(opt$addcovar)) {
  #If perm strata are being used, it'll be included as the final column in the phenotype file
  if (!is.null(opt$pstrata)) {
    covar_names = trait_names[3:length(trait_names) - 1]
  } else {
    covar_names = trait_names[2:length(trait_names)]
  }
  covars <- pull.pheno(cross_object, covar_names)
}

# Pull permutation strata out of cross object, if it is being used
perm_strata = vector()
if (!is.null(opt$pstrata)) {
  strata_col = trait_names[length(trait_names)]
  perm_strata <- pull.pheno(cross_object, strata_col)
}

# If a marker name is supplied as covariate, get its vector of values and add them as a covariate
if (!is.null(opt$control)) {
  marker_covars = create_marker_covars(cross_object, opt$control)
  covars <- cbind(covars, marker_covars)
}

# Calculate permutations
if (opt$nperm > 0) {
  if (!is.null(opt$filename)){
    perm_out_file = file.path(opt$outdir, paste("PERM_", opt$filename, sep = "" ))
  } else {
    perm_out_file = file.path(opt$outdir, paste(pheno_name, "_PERM_", stri_rand_strings(1, 8), sep = ""))
  }

  if (!is.null(opt$addcovar) || !is.null(opt$control)){
    if (!is.null(opt$pstrata)) {
      verbose_print('Running ', opt$nperm, ' permutations with cofactors and strata\n')
      perm_results = scanone(cross_object, pheno.col=1, addcovar=covars, n.perm=opt$nperm, perm.strata=perm_strata, model=opt$model, method=opt$method)
    } else {
      verbose_print('Running ', opt$nperm, ' permutations with cofactors\n')
      perm_results = scanone(cross_object, pheno.col=1, addcovar=covars, n.perm=opt$nperm, model=opt$model, method=opt$method)
    }
  } else {
    if (!is.null(opt$pstrata)) {
      verbose_print('Running ', opt$nperm, ' permutations with strata\n')
      perm_results = scanone(cross_object, pheno.col=1, n.perm=opt$nperm, perm.strata=perm_strata, model=opt$model, method=opt$method)
    } else {
      verbose_print('Running ', opt$nperm, ' permutations\n')
      perm_results = scanone(cross_object, pheno.col=1, n.perm=opt$nperm, model=opt$model, method=opt$method)
    }
  }
  write.csv(perm_results, perm_out_file)
}

if (!is.null(opt$filename)){
  out_file = file.path(opt$outdir, opt$filename)
} else {
  out_file = file.path(opt$outdir, paste(pheno_name, "_", stri_rand_strings(1, 8), sep = ""))
}

if (!is.null(opt$addcovar) || !is.null(opt$control)){
  verbose_print('Running scanone with cofactors\n')
  qtl_results = scanone(cross_object, pheno.col=1, addcovar=covars, model=opt$model, method=opt$method)
} else {
  verbose_print('Running scanone\n')
  qtl_results = scanone(cross_object, pheno.col=1, model=opt$model, method=opt$method)
}
write.csv(qtl_results, out_file)
