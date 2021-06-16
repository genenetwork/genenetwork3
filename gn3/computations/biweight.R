
library(WGCNA)

arg_values <- commandArgs(trailingOnly = TRUE)
ParseArgs <- function(args){

	trait_vals <- as.numeric(unlist(strsplit(args[1], split=" ")))
	target_vals <- as.numeric(unlist(strsplit(args[2], split=" ")))

	return(list(trait_vals= c(trait_vals),target_vals = c(target_vals)))

}
BiweightMidCorrelation <- function(trait_val,target_val){

	results <- bicorAndPvalue(c(trait_val),c(target_val))
    return ((c(c(results$bicor)[1],c(results$p)[1])))

}


parsed_values <- ParseArgs(arg_values)

cat((BiweightMidCorrelation(parsed_values[1],parsed_values[2])))