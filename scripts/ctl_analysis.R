library(ctl)

# The genotypes.csv file containing the genotype matrix is stored individuals (rows) x genetic marker (columns):

args = commandArgs(trailingOnly=TRUE)

if (length(args)==0) {
  stop("Argument for the geno and pheno file location is required", call.=FALSE)
} else {
  # default output file
  geno_file  = args[1]
  pheno_file = args[2]
}




genotypes <- read.csv(geno_file,row.names=1, header=FALSE, sep="\t")
# The phenotypes.csv file containing individuals (rows) x traits (columns) measurements:
traits <- read.csv(pheno_file,row.names=1, header=FALSE, sep="\t")


ctls <- CTLscan(geno,traits,strategy=input$strategy,
	nperm=input$nperms,parametric =input$parametric,
	nthreads=6,verbose=TRUE)



#output matrix significant CTL interactions with 4 columns: trait, marker, trait, lod
sign <- CTLsignificant(ctls,significance = input$significance)

# add plots 


json_data <- list(significance=signs,
	images=lists("image_1":"image_location"),
	network_figure_location="/location")