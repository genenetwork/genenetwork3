
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
 
colnames(ctl_significant) = c("trait","marker","trait_2","LOD","dcor")


# # Create the lineplot


imageLoc = file.path(input$imgDir,genImageRandStr("CTLline"))

png(imageLoc,width=1000,height=600,type='cairo-png')

ctl.lineplot(ctls,significance = 0.05, gap = 50, 
col = "orange", bg.col = "lightgray", cex = 1, verbose = FALSE)

dev.off()


n = 2
ctl_plots = c()

for (trait in phenoData$trait_db_list)
{
	image_loc = file.path(input$imgDir,genImageRandStr(paste("CTL",n,sep="")))
	png(image_loc,width=1000, height=600, type='cairo-png')
  plot.CTLobject(ctls,n-1,significance= 0.05, main=paste("Phenotype",trait,sep=""))

  ctl_plots = append(ctl_plots,image_loc)

  dev.off()
  n = n + 1

}
# rename coz of duplicate key names 


network_file_path  = file.path(input$imgDir,paste("ctlnet","random",".sif",sep=""))


file.create(network_file_path)

ctl_network = CTLnetwork(ctls, significance = 0.05, LODdrop = 2,short = FALSE, add.qtls = FALSE, file = network_file_path, verbose = TRUE)



json_data <- list(significance_table = ctl_significant,image_loc = imageLoc,ctl_plots=ctl_plots)


json_data <- toJSON(json_data)

write(json_data,file= json_file_path)