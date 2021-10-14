library(ctl)
library(stringi);
library(rjson)

options(stringsAsFactors = FALSE);

# The genotypes.csv file containing the genotype matrix is stored individuals (rows) x genetic marker (columns):

args = commandArgs(trailingOnly=TRUE)

imgDir = Sys.getenv("GENERATED_IMAGE_DIR")

if (length(args)==0) {
  stop("Argument for the data file", call.=FALSE)
} else {
  # default output file
  json_file_path = args[1]
}

json_file_path
# add validation for the files
input <- fromJSON(file = json_file_path)

genoData <- input$geno
phenoData <- input$pheno

formData <- input$form
# create the matixes
genoData
geno_matrix = t(matrix(unlist(genoData$genotypes),
	nrow=length(genoData$markernames), ncol=length(genoData$individuals),
	dimnames=list(genoData$markernames, genoData$individuals), byrow=TRUE))

pheno_matrix = t(matrix(as.numeric(unlist(phenoData$traits)), nrow=length(phenoData$trait_db_list), ncol=length(
    phenoData$individuals), dimnames= list(phenoData$trait_db_list, phenoData$individuals), byrow=TRUE))

# Use a data frame to store the objects
pheno = data.frame(pheno_matrix, check.names=FALSE)
geno = data.frame(geno_matrix, check.names=FALSE)




ctls <- CTLscan(geno,pheno,verbose=TRUE)

# same function used in a different script:refactor
genImageRandStr <- function(prefix){

	randStr <- paste(prefix,stri_rand_strings(1, 9, pattern = "[A-Za-z0-9]"),sep="_")

	return(paste(randStr,".png",sep=""))
}


#output matrix significant CTL interactions with 4 columns: trait, marker, trait, lod
sign <- CTLsignificant(ctls,significance = formData$significance)
 
# Create the lineplot
imageLoc = file.path(imgDir,genImageRandStr("CTLline"))

png(imageLoc,width=1000,height=600,type='cairo-png')

ctl.lineplot(ctls, significance=formData$significance)

json_data <- list(significance=sign,
	images=list("image_1"=imageLoc),
	network_figure_location="/location")