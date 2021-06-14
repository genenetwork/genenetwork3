
library(WGCNA)


myArgs <- commandArgs(trailingOnly = TRUE)
trait_vals <- as.numeric(unlist(strsplit(myArgs[1], split=" ")))
target_vals <- as.numeric(unlist(strsplit(myArgs[2], split=" ")))

BiweightMidCorrelation <- function(trait_val,target_val){
    results <- bicorAndPvalue(x,y)
    return (list(c(results$bicor)[1],c(results$p)[1]))
}
cat(BiweightMidCorrelation(trait_vals,target_vals))


