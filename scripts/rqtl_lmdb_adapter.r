                                        # rqtl2 lmdb adapter (to read cross data from lmdb -> light memory mapped database)
                                        # for implementation reference see:  https://kbroman.org/qtl2/assets/vignettes/developer_guide.html

                                        # how to run Rscript rqtl_lmdb_adapter.R  LMDB_PATH
                                        # dependencies with guix:  env GUIX_PACKAGE_PATH="/home/kabui/guix-bioinformatics" guix shell   r r-thor r-rjson r-qtl2 r-data-table
                                        # rscript ./rqtl2_wrapper.R [LMDB_PATH]


library("rjson")
library("thor")
library(qtl2)
library("data.table")

read_lmdb_cross <- function(lmdb_file_path) {
env <- thor::mdb_env(lmdb_file_path, maxdbs = 2, readonly = FALSE) 
txn <- env$begin(write = FALSE)
metadata <- fromJSON(txn$get("metadata"), simplify = TRUE) 
nrows <- metadata$nrows
ncols <- metadata$ncols
cross_metadata_bytes = txn$get("cross_metadata")
cross_metadata <- fromJSON(cross_metadata_bytes, simplify=TRUE)

matrix_bytes   <- txn$get("matrix")



matrix_values  <- readBin(matrix_bytes,
                          what = integer(),
                          size = 1,
                          n = nrows * ncols,
                          signed = FALSE,
                          endian = "little")
geno <- genotype_matrix <- matrix(matrix_values,
                          nrow = nrows,
                          ncol = ncols,
                          byrow = TRUE)



pheno_bytes <- txn$get("pheno_matrix")
pheno_metadata_bytes  <- txn$get("pheno_metadata")
pheno_metadata <- fromJSON(pheno_metadata_bytes, simplify=TRUE)
pheno_rows  <- pheno_metadata$rows
pheno_columns <- pheno_metadata$columns


pheno_matrix_values  <- readBin(pheno_bytes,
                          what = double(),
                          #size = 1,
                          n = pheno_rows * pheno_columns, 
                          signed = TRUE,
                          endian = "little")

pheno_matrix <- matrix(pheno_matrix_values,
                      nrow=pheno_rows,
                      ncol=pheno_columns,
                      byrow=TRUE
                      )


pheno_matrix <- t(pheno_matrix)
print(dim(pheno_matrix))
pheno_dataframe <- as.data.frame(pheno_matrix) 

colnames(pheno_dataframe) <- as.list(pheno_metadata$traits)   # TODO to rigid change to something else generic
rownames(pheno_dataframe) <- as.list(pheno_metadata$strains ) #TODO:  to rigid change to something else generic like rowname               

txn$commit()
env$close()
# get the individuals from the metadata 
individuals  = metadata$individuals
if (!is.null(individuals) &&  length(individuals) == ncols) {
    colnames(genotype_matrix) <- individuals
    colnames(geno) <- individuals
} else {
    warning("Cannot assign col names for  matrix sience no of individuals  ", individuals, "Does not match no of  columns ", ncols, "\n")
}

# 3. Collect metadata columns (Chr, Locus, Mb, cM) if they match nrows
meta_list <- list()
for (col in c("Chr", "Locus", "Mb", "cM")) {
  vec <- metadata[[col]]
  if (!is.null(vec)) {
    if (length(vec) == nrows) {
      meta_list[[col]] <- vec
    } else {
      warning(sprintf("Metadata '%s' length %d != nrows %d; skipping",
                      col, length(vec), nrows))
    }
  }
}
meta_df <- as.data.frame(meta_list, stringsAsFactors = FALSE)
geno_df <- as.data.frame(genotype_matrix, check.names = FALSE)

# 4. Combine metadata with genotype matrix into a data frame
if (ncol(meta_df) > 0) {
  result_df <- cbind(meta_df, geno_df)
} else {
  result_df <- geno_df
}

if (!("Locus" %in% colnames(result_df))){
    stop("Data missing the Markers columns")
    
}
if (!("Chr" %in% colnames(result_df))){
    stop("Data missing the Chromosomes columns")
    
}

# create the geno_data matrix                               
geno_matrix <- result_df[, !(colnames(result_df) %in% c("cM", "Mb"))]
if ("cM" %in% colnames(result_df)) {
     
    gmap_matrix <- result_df[, c("Locus", "Chr", "cM")]
    colnames(gmap_matrix) <- c("marker", "chr", "pos")
    
    gmap_matrix$pos <- formatC(as.numeric(gmap_matrix$pos), format = "f",digit=1)
} else {
    warning("Can create the gmap_file since no  cM Column in matrix")
}
if ("Mb" %in% colnames(result_df)) {
    pmap_matrix <- result_df[, c("Locus", "Chr", "Mb")]
    colnames(pmap_matrix) <- c("marker", "chr", "pos")
    pmap_matrix$pos <- formatC(as.numeric(pmap_matrix$pos), format = "f",digit=1)  # rethink about precision
} else {
    warning("Can create the pmap file since no Mb column in matrix")
}


if (!is.null(gmap_matrix)) {
    map <- gmap_matrix
   
} else if (!is.null(pmap_matrix)) {
    map <- pmap_matrix
} else {
    stop("Either a pmap or gmap dataset is required!")
}

# TODO ! implement omit markers for not in common  among geno, gmap,pmap,founder_geno
split_map <- function(map, chr_names = NULL) {
  # Reorder map by chromosome if chr_names is provided
  if (!is.null(chr_names)) {
    map <- map[map$chr %in% chr_names, ]
    map$chr <- factor(map$chr, levels = chr_names)
    map <- map[order(map$chr, map$pos), ]
  }

  # Extract chromosome and position
  chr <- map$chr
  pos <- as.numeric(map$pos)

  # Use 'marker' column if it exists, otherwise fallback to rownames
  if ("marker" %in% colnames(map)) {
    names(pos) <- map$marker
  } else {
    names(pos) <- rownames(map)
  }

  # Split by chromosome and sort positions within each
  split_maps <- lapply(split(pos, chr), sort)
  return(split_maps)
}


gmap <- split_map(gmap_matrix,  unique(gmap_matrix$chr))
pmap <- split_map(pmap_matrix,  unique(pmap_matrix$chr))

map <- as.data.frame(map, stringsAsFactors = FALSE)
colnames(map) <- c("marker", "chr", "pos")
rownames(geno) <- map$marker #fix me later 

split_geno <- function(geno, map, individuals) {
  if (!all(c("marker", "chr", "pos") %in% colnames(map))){
    stop("map must contain columns marker, chr, pos")
  }

  # Keep only markers present in both geno and map
  common_markers <- intersect(rownames(geno), map$marker)
  if (length(common_markers) == 0) {
    stop("No overlapping markers between geno and map.")
  }
  geno <- geno[common_markers, , drop = FALSE]
  map  <- map[map$marker %in% common_markers, , drop = FALSE]
  rownames(map) <- map$marker

  # Ensure pos is numeric
  if (!is.numeric(map$pos)) {
    map$pos <- as.numeric(map$pos)
  }

  # ---- Build natural (numeric) chromosome order: 1..19, X, Y, M/MT, others ----
  chr_raw   <- as.character(map$chr)
  chr_clean <- sub("^chr", "", chr_raw, ignore.case = TRUE)
  chr_num   <- suppressWarnings(as.integer(chr_clean))
  chr_up    <- toupper(chr_clean)

  # group: 1 = autosomes (numeric); 2 = X/Y/M; 3 = everything else
  grp <- ifelse(!is.na(chr_num), 1L,
                ifelse(chr_up %in% c("X","Y","M","MT"), 2L, 3L))

  # within-group rank: autosomes by number; sex/mito as 23/24/25; others alphabetical
  rank2 <- ifelse(!is.na(chr_num), chr_num,
           ifelse(chr_up == "X", 23L,
           ifelse(chr_up == "Y", 24L,
           ifelse(chr_up %in% c("M","MT"), 25L, 999L))))

  # Natural chromosome level order
  lvl_order <- order(grp, rank2, chr_up)
  chr_levels <- unique(chr_raw[lvl_order])

  # Make chr an ordered factor with natural levels and sort by (chr, pos)
  map$chr <- factor(map$chr, levels = chr_levels, ordered = TRUE)
  map <- map[order(map$chr, map$pos), ]
  geno <- geno[map$marker, , drop = FALSE]

  # Optional sanity check: individuals vector length
  if (length(individuals) != ncol(geno)) {
    stop("Length of 'individuals' (", length(individuals),
         ") must equal number of columns in 'geno' (", ncol(geno), ").")
  }

  # Split by the ordered factor (names will follow chr_levels order)
  split_idx <- split(seq_len(nrow(map)), map$chr, drop = TRUE)

  result <- lapply(split_idx, function(idx) {
    mat <- t(as.matrix(geno[idx, , drop = FALSE]))  # individuals x markers
    colnames(mat) <- map$marker[idx]
    rownames(mat) <- individuals
    mat
  })

  return(result)
}

geno_split <- split_geno(geno, map, metadata$individuals)
pheno <- pheno_dataframe


if (!all(colnames(geno) %in% rownames(pheno))) {
  warning("Some individuals in genotype matrix are missing from phenotype file")
}


parse_founder_geno <- function(marker_chr_map,  founder_matrix){
                                        # refactor for cases where they are stored as integers
                                        #assumes the matrix is in this format
##     marker	A	B	C	D	E	F	G	H
## backupUNC020000070	B	B	A	B	A	A	B	B
## JAX00090716	B	A	B	B	A	B	B	A
                                        # ENsures marker names are rownames
    if (is.null(rownames(founder_matrix))) {
        stop("founder_matrix must have marker names as row names")
    }
                                        # define alleles to integer mapping -  "-" missing values
    alleles <- sort(unique(unlist(founder_matrix)))
    alleles <- alleles[alleles != "-"]
    allele_map <- setNames(seq_along(alleles), alleles)  # e.g., A=1, B=2, ...     
     encode_row <- function(row) {
     sapply(row, function(allele) {
      if (allele == "-" || is.na(allele)) return(0L)
      as.integer(allele_map[[allele]])
    })
     }
    encoded_matrix <- t(apply(founder_matrix, 1, encode_row))  # transpose: now markers x founders
    rownames(encoded_matrix) <- rownames(founder_matrix)       # marker names
    colnames(encoded_matrix) <- colnames(founder_matrix)       # founder IDs
                                        # 3. Split markers by chromosome
    # dont like this make it simpler
    marker_chr_split <- split(rownames(encoded_matrix), marker_chr_map[rownames(encoded_matrix)])
      # 4. For each chromosome, subset and transpose to get founders x markers
  founder_geno_list <- lapply(marker_chr_split, function(marker_subset) {
    chr_matrix <- encoded_matrix[marker_subset, , drop = FALSE]
    t(chr_matrix)  # transpose to: founders x markers
  })
   return(founder_geno_list)
}


pheno <- as.matrix(pheno[colnames(geno), , drop = FALSE]) # required as matrix ??? big question
geno <- geno_split

if (!is.null(metadata$founder_geno) && !is.null(metadata$marker_chr_map)) {
    founder_geno <-  parse_founder_geno(metadata$marker_chr_map,  metadata$founder_geno)
} else {
     founder_geno <- NULL 
}
    
is_x_chr <- unlist(lapply(names(gmap), function(chr) chr == "X"))
# : is_female check    
is_female <- NULL #  missing assume all TRUE 
if (is.null(is_female)) {
    warning("No sex information; assuming all female")
    is_female <- rep(TRUE, nrow(geno[[1]]))
    names(is_female) <- rownames(geno[[1]])
}

phenocovar <- NULL
covar <- NULL
if (!is.null(cross_metadata$phenocovar)) {
    # as.data.frame too slow switching to this at the expense of extra dependene
    phenocovar <- rbindlist(cross_metadata$phenocovar, use.names = TRUE, fill = TRUE)
    #phenocovar <- as.data.frame(cross_metadata$phenocovar)
}
if (!is.null(cross_metadata$covar)) {
    covar <- rbindlist(cross_metadata$covar, use.names = TRUE, fill = TRUE)
    #covar  <- as.data.frame(cross_metadata$covar)
}


parse_cross_info <- function(cross_info_list, cross_vals) {
  crossinfo_dt <- rbindlist(cross_info_list, fill = TRUE)
  crossinfo_dt[, id := as.character(id)]
  crossinfo_dt[, cross_direction := as.character(cross_direction)]
  # vectorized mapping:
  repr <- cross_vals[[1]]
  val <- as.integer(cross_vals[[2]])
  alt <- as.integer(ifelse(val == 1, 0, 1))
  crossinfo_dt[, cross_direction := ifelse(cross_direction == repr, val, alt)]
  cross_info <- as.matrix(crossinfo_dt[, .(cross_direction)])
  rownames(cross_info) <- crossinfo_dt$id
  colnames(cross_info) <- "cross_direction"
  return(cross_info)
}

cross_info <- parse_cross_info(cross_metadata$cross_info_metadata$cross_direction,
                               cross_metadata$cross_info_metadata$cross_val
                               ) #bad naming just make it cross_info

metadata[["alleles"]] = cross_metadata$alleles
metadata[["crosstype"]] = cross_metadata$crosstype
cross <- list(
    crosstype=metadata$crosstype,
    is_female=is_female,
    geno = geno_split,
    gmap = gmap,
    pmap = if (length(pmap) > 0) pmap else NULL,
    is_x_chr = is_x_chr,
    alleles = metadata$alleles, 
    founder_geno = founder_geno,
    cross_info = cross_info, 
    pheno = pheno,
    phenocovar=phenocovar,
    covar=covar
)
    class(cross) <- c("cross2", "list") # assign class cross2 for this;;: rqtl2 requirement
    return(cross)
}



run_benchmark <- function(lmdb_path, cross_file, times=100){
    # function to benchmark against default read_cross from rqtl2
    library(microbenchmark)
    library(qtl2)
   microbenchmark(
     read_lmdb_cross(lmdb_path),
     read_cross2(cross_file, quiet = TRUE),
     times=times 
)    
}

run_profiler <- function(lmdb_path){
    # Profiler for debug purposes
    library(profvis)
    p <- profvis({
    expr=read_lmdb_cross(lmdb_path)
   })

 htmlwidgets::saveWidget(p, "./profiler/profile.html")
 browseURL("./profiler/profile.html", browser="brave")

}

test_run <-function(){
# function to test run reading from lmdb the performing rqtl2 computation
args = commandArgs(trailingOnly=TRUE)
if (length(args)==0) {
    stop("At least one argument for the db path is required")
}  else {
    LMDB_DB_PATH = args[1]
}
cross <- read_lmdb_cross(LMDB_DB_PATH)
summary(cross)
cat("Is this cross okay", check_cross2(cross), "\n")
warnings() #  enable warnings for the debug purposes  only!
pr <- calc_genoprob(cross)
out <- scan1(pr, cross$pheno, cores=4)
par(mar=c(5.1, 4.1, 1.1, 1.1))
ymx <- maxlod(out) 
plot(out, cross$gmap, lodcolumn=1, col="slateblue") # test generating of qtl plots 
}

