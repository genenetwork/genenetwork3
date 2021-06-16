
library(WGCNA)

FetchArgs <- function(){
	myArgs <- commandArgs(trailingOnly = TRUE)
	trait_vals <- as.numeric(unlist(strsplit(myArgs[1], split=" ")))
	target_vals <- as.numeric(unlist(strsplit(myArgs[2], split=" ")))

	return(list(trait_vals= c(trait_vals),target_vals = c(target_vals)))

}
BiweightMidCorrelation <- function(trait_val,target_val){

	results <- bicorAndPvalue(c(trait_val),c(target_val))
    return ((c(c(results$bicor)[1],c(results$p)[1])))
}


results <- (BiweightMidCorrelation(FetchArgs()[1],FetchArgs()[2]))

cat(results)