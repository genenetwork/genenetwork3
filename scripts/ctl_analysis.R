
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

cat("The input data is \n")



genoData <- input$genoData
phenoData <- input$phenoData

# formData <- input$form
# create the matixes

# genotypes Matrix of genotypes. (individuals x markers)
# phenotypes Matrix of phenotypes. (individuals x phenotypes)

geno_matrix = t(matrix(unlist(genoData$genotypes),
	nrow=length(genoData$markernames), ncol=length(genoData$individuals),
	dimnames=list(genoData$markernames, genoData$individuals), byrow=TRUE))


pheno_matrix = t(matrix(as.numeric(unlist(phenoData$traits)), nrow=length(phenoData$trait_db_list), ncol=length(
    phenoData$individuals), dimnames= list(phenoData$trait_db_list, phenoData$individuals), byrow=TRUE))

# # Use a data frame to store the objects


ctls <- CTLscan(geno_matrix,pheno_matrix,nperm=input$nperm,strategy=input$strategy,parametric=TRUE,nthreads=3,verbose=TRUE)



# # same function used in a different script:refactor
genImageRandStr <- function(prefix){

	randStr <- paste(prefix,stri_rand_strings(1, 9, pattern = "[A-Za-z0-9]"),sep="_")

	return(paste(randStr,".png",sep=""))
}



# #output matrix significant CTL interactions with 4 columns: trait, marker, trait, lod
ctl_significant <- CTLsignificant(ctls,significance = 0.05)
 
# # Create the lineplot
# imageLoc = file.path(imgDir,genImageRandStr("CTLline"))

# png(imageLoc,width=1000,height=600,type='cairo-png')

# ctl.lineplot(ctls, significance=formData$significance)


# rename coz of duplicate key names 
colnames(sign) = c("trait","marker","trait_2","LOD","dcor")

json_data <- list(significance_table = ctl_significant)


json_data <- toJSON(json_data)

write(json_data,file= json_file_path)