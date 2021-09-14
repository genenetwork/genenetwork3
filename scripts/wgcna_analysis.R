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






