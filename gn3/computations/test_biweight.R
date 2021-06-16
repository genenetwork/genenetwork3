library(testthat)
source("./biweight.R", chdir = TRUE)

test_that("sum of vector", {
  results <- sum(c(1,2))
  expect_equal(results, 3)
})



test

test_that("biweight results"),{
	vec_1 = c(1,2,3,4)
	vec_2 = c(1,2,3,4)

	results = BiweightMidCorrelation(vec_1,vec_2)
	expect_equal(c(1.0,0.0),results)
}


test_that("parsing args "),{
	my_args = c("1 2 3 4","5 6 7 8")
	results <- ParseArgs(my_args)

	expect_equal(results[1],c(1,2,3,4))
	expect_equal(results[2],c(5,6,7,8))
}