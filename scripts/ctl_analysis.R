library(ctl)
library(rjson)

options(stringsAsFactors = FALSE);

# The genotypes.csv file containing the genotype matrix is stored individuals (rows) x genetic marker (columns):

args = commandArgs(trailingOnly=TRUE)

if (length(args)==0) {
  stop("Argument for the data file", call.=FALSE)
} else {
  # default output file
  json_file_path = args[1]
}

# add validation for the files
input <- fromJSON(file = json_file_path)


genotypes <- read.csv(input$geno_file,row.names=1, header=FALSE, sep="\t")
# The phenotypes.csv file containing individuals (rows) x traits (columns) measurements:
traits <- read.csv(input$pheno_file,row.names=1, header=FALSE, sep="\t")


ctls <- CTLscan(geno,traits,strategy=input$strategy,
	nperm=input$nperms,parametric =input$parametric,
	nthreads=6,verbose=TRUE)


# same function used in a different script:refactor
genImageRandStr <- function(prefix){

	randStr <- paste(prefix,stri_rand_strings(1, 9, pattern = "[A-Za-z0-9]"),sep="_")

	return(paste(randStr,".png",sep=""))
}


#output matrix significant CTL interactions with 4 columns: trait, marker, trait, lod
sign <- CTLsignificant(ctls,significance = input$significance)
 
# Create the lineplot
imageLoc = file.path(imgDir,genImageRandStr("CTLline"))

png(imageLoc,width=1000,height=600,type='cairo-png')

lineplot(res, significance=input$significance)


json_data <- list(significance=signs,
	images=lists("image_1"=imageLoc),
	network_figure_location="/location")