# initial workspace setup

library(WGCNA);
stringsAsFactors = FALSE

# load expression data **assumes csv format row(traits)(columns info+samples)


wgcnaRawData <- read.csv(file = "wgcna_data.csv")

# transform expressionData

datExpr <- as.data.frame(t(wgcnaRawData));








