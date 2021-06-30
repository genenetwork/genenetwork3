# computing the pricipal complex analysiys


ComputePCA <- function(data_matrix){

    pca <- prcomp(correlation_matrix, scale=TRUE)
    # prcomp return x,sdev,rotations/loadings
    # x contains the pc components -> pca$x[,1],pca$x[,2]
    # getting loading scores

    loading_scores <-pca$rotation[,1] 
    # use for 1
    # use ggplot

    scores = abs(loading_scores)

    # ranks scores
    ranked_scores = sort(scores,decreasing=True)

}
