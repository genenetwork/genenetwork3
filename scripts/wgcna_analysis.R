# initial workspace setup

library(WGCNA);
stringsAsFactors = FALSE

# load expression data **assumes csv format row(traits)(columns info+samples)

wgcnaRawData <- read.csv(file = "wgcna_data.csv")

# transform expressionData

dataExpr <- as.data.frame(t(wgcnaRawData));

# data cleaning

# adopted from docs
gsg = goodSamplesGenes(dataExpr, verbose = 3);



if (!gsg$allOK)
{
# Optionally, print the gene and sample names that were removed:
if (sum(!gsg$goodGenes)>0)
printFlush(paste("Removing genes:", paste(names(datExpr0)[!gsg$goodGenes], collapse = ", ")));
if (sum(!gsg$goodSamples)>0)
printFlush(paste("Removing samples:", paste(rownames(datExpr0)[!gsg$goodSamples], collapse = ", ")));
# Remove the offending genes and samples from the data:
dataExpr <- dataExpr[gsg$goodSamples, gsg$goodGenes]
}

# network constructions and modules

# choose softthreshhold (Calculate soft threshold if the user specified the)

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









