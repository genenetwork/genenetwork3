
library(testthat)
library(WGCNA)

arg_values <- commandArgs(trailingOnly = TRUE)
ParseArgs <- function(args){

    trait_vals <- as.numeric(unlist(strsplit(args[1], split=" ")))
    target_vals <- as.numeric(unlist(strsplit(args[2], split=" ")))

    return(list(trait_vals= c(trait_vals),target_vals = c(target_vals)))

}
BiweightMidCorrelation <- function(trait_val,target_val){

    results <-bicorAndPvalue(as.numeric(unlist(trait_val)),as.numeric(unlist(target_val)))
    return ((c(c(results$bicor)[1],c(results$p)[1])))

}



test_that("biweight results"),{
    vec_1 <- c(1,2,3,4)
    vec_2 <- c(1,2,3,4)

    results <- BiweightMidCorrelation(vec_1,vec_2)
    expect_equal(c(1.0,0.0),results)
}


test_that("parsing args "),{
    my_args <- c("1 2 3 4","5 6 7 8")
    results <- ParseArgs(my_args)

    expect_equal(results[1],c(1,2,3,4))
    expect_equal(results[2],c(5,6,7,8))
}

parsed_values <- ParseArgs(arg_values)


cat(BiweightMidCorrelation(parsed_values[1],parsed_values[2]))