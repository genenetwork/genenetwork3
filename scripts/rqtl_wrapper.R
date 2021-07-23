library(optparse)
library(qtl)
library(stringi)
library(stringr)

tmp_dir = Sys.getenv("TMPDIR")

option_list = list(
  make_option(c("-g", "--geno"), type="character", help=".geno file containing a dataset's genotypes"),
  make_option(c("-p", "--pheno"), type="character", help="File containing two columns - sample names and values"),
  make_option(c("-c", "--addcovar"), action="store_true", default=NULL, help="Use covariates (included as extra columns in the phenotype input file)"),
  make_option(c("--covarstruct"), type="character", help="File detailing which covariates are categorical or numerical"),
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

adjustXprobs <- function(cross){
  sex <- getsex(cross)$sex
  pr <- cross$geno[["X"]]$prob
  stopifnot(!is.null(pr), !is.null(sex))

  for(i in 1:ncol(pr)) {
      pr[sex==0,i,3:4] <- 0
      pr[sex==1,i,1:2] <- 0
      pr[,i,] <- pr[,i,]/rowSums(pr[,i,])
  }
  cross$geno[["X"]]$prob <- pr
  invisible(cross)
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

geno_to_csvr <- function(genotypes, trait_names, trait_vals, out, type, sex = NULL,
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

# Get type of genotypes, since it needs to be checked before calc.genoprob
header = readLines(geno_file, 40)
type <- get_geno_code(header, 'type')

verbose_print('Generating cross object\n')
cross_object = geno_to_csvr(geno_file, trait_names, trait_vals, cross_file, type)

# Calculate genotype probabilities
if (!is.null(opt$interval)) {
  verbose_print('Calculating genotype probabilities with interval mapping\n')
  cross_object <- calc.genoprob(cross_object, step=5, stepwidth="max")
} else if (!is.null(opt$pairscan)) {
  verbose_print('Calculating genotype probabilities with interval mapping\n')
  cross_object <- calc.genoprob(cross_object, step=20)
} else {
  verbose_print('Calculating genotype probabilities\n')
  cross_object <- calc.genoprob(cross_object)
}

# If 4way, adjust X chromosome genotype probabilities
if (type == "4-way") {
  verbose_print('Adjusting genotype probabilities for 4way cross')
  cross_object <- adjustXprobs(cross_object)
}

# Pull covariates out of cross object, if they exist
covars <- c() # Holds the covariates which should be passed to R/qtl
if (!is.null(opt$addcovar)) {
  verbose_print('Pulling covariates out of cross object\n')
  # If perm strata are being used, it'll be included as the final column in the phenotype file
  if (!is.null(opt$pstrata)) {
    covar_names = trait_names[2:(length(trait_names)-1)]
  } else {
    covar_names = trait_names[2:length(trait_names)]
  }
  covars <- pull.pheno(cross_object, covar_names)
  # Read in the covar description file
  covarDescr <- read.table(opt$covarstruct, sep="\t", header=FALSE)
  for(x in 1:nrow(covarDescr)){
    cat(covarDescr[x, 1])
    name <- paste0("T_", covarDescr[x, 1]) # The covar description file doesn't have T_ in trait names (the cross object does)
    type <- covarDescr[x, 2]
    if(type == "categorical"){
      verbose_print('Binding covars to covars\n')
      if (nrow(covarDescr) < 2){
        this_covar = covars
      } else {
        this_covar = covars[,name]
      }
      if(length(table(this_covar)) > 2){ # More then 2 levels create the model matrix for the factor
        mdata <- data.frame(toExpand = as.factor(this_covar))
        options(na.action='na.pass')
        modelmatrix <- model.matrix(~ toExpand + 0, mdata)[,-1]
        covars <- cbind(covars, modelmatrix)
      }else{ # 2 levels? just bind the trait as covar
        covars <- cbind(covars, this_covar)
      }
    }
  }
}

# Pull permutation strata out of cross object, if it is being used
perm_strata = vector()
if (!is.null(opt$pstrata)) {
  verbose_print('Pulling permutation strata out of cross object\n')
  strata_col = trait_names[length(trait_names)]
  perm_strata <- pull.pheno(cross_object, strata_col)
}

# If a marker name is supplied as covariate, get its vector of values and add them as a covariate
if (!is.null(opt$control)) {
  verbose_print('Creating marker covariates and binding them to covariates vector\n')
  marker_covars = create_marker_covars(cross_object, opt$control)
  covars <- cbind(covars, marker_covars)
}

if (!is.null(opt$pairscan)) {
  scan_func <- function(...){
    scantwo(...)
  }
} else {
  scan_func <- function(...){
    scanone(...)
  }
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
      verbose_print('Running permutations with cofactors and strata\n')
      perm_results = scan_func(cross_object, pheno.col=1, addcovar=covars, n.perm=opt$nperm, perm.strata=perm_strata, model=opt$model, method=opt$method)
    } else {
      verbose_print('Running permutations with cofactors\n')
      perm_results = scan_func(cross_object, pheno.col=1, addcovar=covars, n.perm=opt$nperm, model=opt$model, method=opt$method)
    }
  } else {
    if (!is.null(opt$pstrata)) {
      verbose_print('Running permutations with strata\n')
      perm_results = scan_func(cross_object, pheno.col=1, n.perm=opt$nperm, perm.strata=perm_strata, model=opt$model, method=opt$method)
    } else {
      verbose_print('Running permutations\n')
      perm_results = scan_func(cross_object, pheno.col=1, n.perm=opt$nperm, model=opt$model, method=opt$method)
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
  verbose_print('Running scan with cofactors\n')
  qtl_results = scan_func(cross_object, pheno.col=1, addcovar=covars, model=opt$model, method=opt$method)
} else {
  verbose_print('Running scan\n')
  qtl_results = scan_func(cross_object, pheno.col=1, model=opt$model, method=opt$method)
}

#QTL main effects on adjusted longevity
getEffects <- function(sdata, gtsprob, marker = "1_24042124", model = "longevity ~ sex + site + cohort + treatment", trait = "longevity"){
  rownames(sdata) <- 1:nrow(sdata)
  rownames(gtsprob) <- 1:nrow(gtsprob)
  mp <- gtsprob[, grep(marker, colnames(gtsprob))]
  gts <- unlist(lapply(lapply(lapply(apply(mp,1,function(x){which(x > 0.85)}),names), strsplit, ":"), function(x){
    if(length(x) > 0){ return(x[[1]][2]); }else{ return(NA) }
  }))

  ismissing <- which(apply(sdata, 1, function(x){any(is.na(x))}))
  if(length(ismissing) > 0){
    sdata <- sdata[-ismissing, ]
    gts <- gts[-ismissing]
  }

  mlm <- lm(as.formula(model), data = sdata)
  pheAdj <- rep(NA, nrow(sdata))
  adj <- residuals(mlm) + mean(sdata[, trait])
  pheAdj[as.numeric(names(adj))] <- adj
  means <- c(mean(pheAdj[which(gts == "AC")],na.rm=TRUE),mean(pheAdj[which(gts == "AD")],na.rm=TRUE),mean(pheAdj[which(gts == "BC")],na.rm=TRUE),mean(pheAdj[which(gts == "BD")],na.rm=TRUE))
  std <- function(x) sd(x,na.rm=TRUE)/sqrt(length(x))
  stderrs <- c(std(pheAdj[which(gts == "AC")]),std(pheAdj[which(gts == "AD")]),std(pheAdj[which(gts == "BC")]),std(pheAdj[which(gts == "BD")]))
  paste0(round(means,0), " ± ", round(stderrs,2))
}

if (type == "4-way") {
  verbose_print("Get phenotype name + genoprob + all phenotypes + models for 4-way crosses")
  traitname <- colnames(pull.pheno(cross_object))[1]
  gtsp <- pull.genoprob(cross_object)
  allpheno <- pull.pheno(cross_object)
  if (!is.null(opt$addcovar)) {
    model <- paste0(traitname, " ~ ", paste0(covar_names, sep="", collapse=" + "))
  } else {
    model <- paste0(traitname, " ~ 1 ")
  }

  meffects <- c()
  verbose_print("Getting QTL main effects for 4-way crosses")
  for(marker in  rownames(qtl_results)){
    meff <- getEffects(allpheno, gtsp, marker = marker, model, trait = traitname)
    meffects <- rbind(meffects, meff)
  }
  qtl_results <- cbind(data.frame(qtl_results[,1:3]), meffects)
  colnames(qtl_results)[4:7] <- c("AC", "AD", "BC", "BD")
}

write.csv(qtl_results, out_file)
