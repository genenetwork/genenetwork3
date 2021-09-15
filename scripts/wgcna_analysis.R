

library(WGCNA);
library(stringi);

options(stringsAsFactors = FALSE);

imgDir = Sys.getenv("GENERATED_IMAGE_DIR")

# load expression data **assumes csv format row(traits)(columns info+samples)
# pass the file_path as arg

inputData <- read.csv(file = "wgcna_data.csv")

# transform expressionData

dataExpr <- as.data.frame(t(inputData));

## data cleaning

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

# pass user options
network <- blockwiseModules(dataExpr,
                  #similarity  matrix options
                  corType = "pearson",
                  #adjacency  matrix options

                  power = sft$powerEstimate,
                  networkType = "unsigned",
                  #TOM options
                  TOMtype =  "unsigned",

                  #module indentification

                  minmodulesSize = 30,
                  deepSplit = 5,
                  PamRespectsDendro = FALSE
                )



genImageRandStr <- function(prefix){

	randStr <- paste(prefix,stri_rand_strings(1, 9, pattern = "[A-Za-z0-9]"),sep="_")

	return(paste(randStr,".png",sep=""))
}

mergedColors <- labels2colors(net$colors)

imageLoc <- file.path(imgDir,genImageRandStr("WGCNAoutput"))


png(imageLoc,width=1000,height=600,type='cairo-png')

plotDendroAndColors(network$dendrograms[[1]],mergedColors[net$blockGenes[[1]]],
"Module colors",
dendroLabels = FALSE, hang = 0.03,
addGuide = TRUE, guideHang = 0.05)



