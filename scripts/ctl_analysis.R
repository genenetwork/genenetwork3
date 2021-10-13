library(ctl)

# The genotypes.csv file containing the genotype matrix is stored individuals (rows) x genetic marker (columns):
genotypes <- read.csv("genotypes.csv",row.names=1, header=FALSE, sep="\t")
# The phenotypes.csv file containing individuals (rows) x traits (columns) measurements:
traits <- read.csv("phenotypes.csv",row.names=1, header=FALSE, sep="\t")
