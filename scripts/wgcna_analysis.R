

library(WGCNA);
library(stringi);
library(rjson)

options(stringsAsFactors = FALSE);

imgDir = Sys.getenv("GENERATED_IMAGE_DIR")
# load expression data **assumes from json files row(traits)(columns info+samples)
# pass the file_path as arg
# pass the file path to read json data

args = commandArgs(trailingOnly=TRUE)

if (length(args)==0) {
  stop("Argument for the file location is required", call.=FALSE)
} else {
  # default output file
  json_file_path  = args[1]
}

inputData <- fromJSON(file = json_file_path)


# parse the json data input

minModuleSize <-inputData$minModuleSize

TOMtype <-inputData$TOMtype

corType <-inputData$corType
# 

trait_sample_data <- do.call(rbind, inputData$trait_sample_data)

dataExpr <- data.frame(apply(trait_sample_data, 2, function(x) as.numeric(as.character(x))))
# transform expressionData

dataExpr <- data.frame(t(dataExpr))
gsg = goodSamplesGenes(dataExpr, verbose = 3);

# https://horvath.genetics.ucla.edu/html/CoexpressionNetwork/Rpackages/
if (!gsg$allOK)
{
if (sum(!gsg$goodGenes)>0)
printFlush(paste("Removing genes:", paste(names(dataExpr)[!gsg$goodGenes], collapse = ", ")));
if (sum(!gsg$goodSamples)>0)
printFlush(paste("Removing samples:", paste(rownames(dataExpr)[!gsg$goodSamples], collapse = ", ")));
# Remove the offending genes and samples from the data:
dataExpr <- dataExpr[gsg$goodSamples, gsg$goodGenes]
}

## network constructions and modules

# Allow multi-threading within WGCNA
enableWGCNAThreads()

# choose softthreshhold (Calculate soft threshold)
# xtodo allow users to pass args

powers <- c(c(1:10), seq(from = 12, to=20, by=2)) 
sft <- pickSoftThreshold(dataExpr, powerVector = powers, verbose = 5)

# check the power estimate

if (is.na(sft$powerEstimate)){
  powerEst = 1
}else{
  powerEst = sft$powerEstimate
}

# pass user options
network <- blockwiseModules(dataExpr,
                  #similarity  matrix options
                  corType = corType,
                  #adjacency  matrix options

                  power = powerEst,
                  networkType = "unsigned",
                  #TOM options
                  TOMtype =  TOMtype,

                  #module indentification

                  minmodulesSize = minModuleSize,
                  deepSplit = 3,
                  PamRespectsDendro = FALSE
                )



genImageRandStr <- function(prefix){

	randStr <- paste(prefix,stri_rand_strings(1, 9, pattern = "[A-Za-z0-9]"),sep="_")

	return(paste(randStr,".png",sep=""))
}

mergedColors <- labels2colors(network$colors)

imageLoc <- file.path(imgDir,genImageRandStr("WGCNAoutput"))
png(imageLoc,width=1000,height=600,type='cairo-png')

plotDendroAndColors(network$dendrograms[[1]],mergedColors[network$blockGenes[[1]]],
"Module colors",
dendroLabels = FALSE, hang = 0.03,
addGuide = TRUE, guideHang = 0.05)




json_data <- list(input = inputData,output = list(ModEigens=network$MEs,soft_threshold=sft$fitIndices,
  blockGenes =network$blockGenes[[1]],
  net_colors =network$colors,
  net_unmerged=network$unmergedColors,
  imageLoc=imageLoc))

json_data <- toJSON(json_data)

write(json_data,file= json_file_path)