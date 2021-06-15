
# library(WGCNA)


myArgs <- commandArgs(trailingOnly = TRUE)
trait_vals <- as.numeric(unlist(strsplit(myArgs[1], split=" ")))
target_vals <- as.numeric(unlist(strsplit(myArgs[2], split=" ")))

BiweightMidCorrelation <- function(trait_val,target_val){
    results <- bicorAndPvalue(trait_val,target_val)
    return (list(c(results$bicor)[1],c(results$p)[1]))
}






# the idea is that you get the entire dataset in any format 
# and then do ther correlation

ComputeAll <-function(trait_val,target_dataset) {
	for target_val in target_dataset {
      results = BiweightMidCorrelation(trait_val,target_val)
      cat(BiweightMidCorrelation(trait_vals,target_vals))
	}
}

