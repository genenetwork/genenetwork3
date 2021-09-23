

library(WGCNA);
library(stringi);
library(rjson)

options(stringsAsFactors = FALSE);

imgDir = Sys.getenv("GENERATED_IMAGE_DIR")

# load expression data **assumes from json files row(traits)(columns info+samples)
# pass the file_path as arg

results <- fromJSON(file = "file_path.json")

# trait_sample_data <- results$trait_sample_data
trait_sample_data <- do.call(rbind, results$trait_sample_data)


dataExpr <- data.frame(apply(trait_sample_data, 2, function(x) as.numeric(as.character(x))))
# trait_sample_data <- as.data.frame(t(results$trait_sample_data))
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

# pass user options
network <- blockwiseModules(dataExpr,
                  #similarity  matrix options
                  corType = "pearson",
                  #adjacency  matrix options

                  power = 5,
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

mergedColors <- labels2colors(network$colors)

imageLoc <- file.path(imgDir,genImageRandStr("WGCNAoutput"))

png(imageLoc,width=1000,height=600,type='cairo-png')

plotDendroAndColors(network$dendrograms[[1]],mergedColors[network$blockGenes[[1]]],
"Module colors",
dendroLabels = FALSE, hang = 0.03,
addGuide = TRUE, guideHang = 0.05)



