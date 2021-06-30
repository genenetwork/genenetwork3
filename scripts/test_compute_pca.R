# source :https://github.com/StatQuest/pca_demo/blob/master/pca_demo.R

library("testthat")





test_that("test sum",{
  results <- sum(1:5)
  expect_equal(results,15)
})

test_that("test_pca",{
  data.matrix <- matrix(nrow=100, ncol=10)

})