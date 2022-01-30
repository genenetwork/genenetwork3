
library(ctl)
library(stringi);
library(rjson)

options(stringsAsFactors = FALSE);

# The genotypes.csv file containing the genotype matrix is stored individuals (rows) x genetic marker (columns):

args = commandArgs(trailingOnly=TRUE)

imgDir = Sys.getenv("GENERATED_IMAGE_DIR")

if (length(args)==0) {
  stop("Argument for the data file", call.=FALSE)
} else {
  # default output file
  json_file_path = args[1]
}

json_file_path
# add validation for the files
input <- fromJSON(file = json_file_path)

cat("The input data is \n")



genoData <- input$genoData
phenoData <- input$phenoData
# create the matixes

# genotypes Matrix of genotypes. (individuals x markers)
# phenotypes Matrix of phenotypes. (individuals x phenotypes)

geno_matrix = t(matrix(unlist(genoData$genotypes),
	nrow=length(genoData$markernames), ncol=length(genoData$individuals),
	dimnames=list(genoData$markernames, genoData$individuals), byrow=TRUE))


pheno_matrix = t(matrix(as.numeric(unlist(phenoData$traits)), nrow=length(phenoData$trait_db_list), ncol=length(
    phenoData$individuals), dimnames= list(phenoData$trait_db_list, phenoData$individuals), byrow=TRUE))

# # Use a data frame to store the objects


ctls <- CTLscan(geno_matrix,pheno_matrix,nperm=input$nperm,strategy=input$strategy,parametric=TRUE,nthreads=3,verbose=TRUE)



# # same function used in a different script:refactor
genImageRandStr <- function(prefix){

	randStr <- paste(prefix,stri_rand_strings(1, 9, pattern = "[A-Za-z0-9]"),sep="_")

	return(paste(randStr,".png",sep=""))
}


genRandomFileName <- function(prefix,file_ext=".png"){

	randStr = paste(prefix,stri_rand_strings(1, 9, pattern = "[A-Za-z0-9]"),sep="_")

	return(paste(randStr,file_ext,sep=""))
}


# #output matrix significant CTL interactions with 4 columns: trait, marker, trait, lod
ctl_significant <- CTLsignificant(ctls,significance = input$significance)
 
colnames(ctl_significant) = c("trait","marker","trait_2","LOD","dcor")


# # Create the lineplot


imageLoc = file.path(input$imgDir,genRandomFileName("CTLline"))

png(imageLoc,width=1000,height=600,type='cairo-png')

ctl.lineplot(ctls,significance = input$significance, gap = 50, 
col = "orange", bg.col = "lightgray", cex = 1, verbose = FALSE)

dev.off()


n = 2
ctl_plots = c()

for (trait in phenoData$trait_db_list)
{
	image_loc = file.path(input$imgDir,genRandomFileName(paste("CTL",n,sep="")))
	png(image_loc,width=1000, height=600, type='cairo-png')
  plot.CTLobject(ctls,n-1,significance= input$significance, main=paste("Phenotype",trait,sep=""))

  ctl_plots = append(ctl_plots,image_loc)

  dev.off()
  n = n + 1

}



network_file_name = paste("ctlnet",stri_rand_strings(1, 9, pattern = "[A-Za-z0-9]"),sep="_")
netfile =  file.path(input$imgDir,paste(network_file_name,".sif",sep=""))

nodefile = file.path(input$imgDir,paste(network_file_name,".nodes",sep=""))

# fn overrides ctlnetwork function to target gn2 use case

CTLnetworkGn<- function(CTLobject, mapinfo, significance = 0.05, LODdrop = 2, what = c("names","ids"), short = FALSE, add.qtls = FALSE,verbose = TRUE){
  if(missing(CTLobject) || is.null(CTLobject)) stop("argument 'CTLobject' is missing, with no default")
  if("CTLscan" %in% class(CTLobject)) CTLobject = list(CTLobject)
  if(length(what) > 1) what = what[1]

  results <- NULL
  significant <- CTLsignificant(CTLobject, significance, what = "ids")
  if(!is.null(significant)){
    all_m <- NULL; all_p <- NULL;


    cat("",file=netfile); cat("",file=nodefile);
    if(verbose) cat("NETWORK.SIF\n")
    edges <- NULL
    for(x in 1:nrow(significant)){
      data    <- as.numeric(significant[x,])
      CTLscan <- CTLobject[[data[1]]]
      markern <- rownames(CTLscan$dcor)
      traitsn <- colnames(CTLscan$dcor)
      name    <- ctl.name(CTLscan)
      if(what=="ids"){
        tid     <- which(traitsn %in% ctl.name(CTLobject[[data[1]]]))
        name    <- paste("P",tid,sep="")
        markern <- paste("M",1:nrow(CTLobject[[data[1]]]$dcor), sep="")
        traitsn <- paste("P", 1:ncol(CTLobject[[data[1]]]$dcor), sep="")
      }
      if(add.qtls){ # Add QTL to the output SIF
        bfc    <- length(CTLscan$qtl)
        above  <- which(CTLscan$qtl > -log10(significance))
        qtlnms <- names(above); qtlmid <- 1
        for(m in above){
          cat(name,"\tQTL\t",markern[m],"\tQTL\t",CTLscan$qtl[m],"\n",sep="",file=netfile,append=TRUE)
          all_m  <- CTLnetwork.addmarker(all_m, mapinfo, markern[data[2]], qtlnms[qtlmid])
          qtlmid <- qtlmid+1
        }
      }
      lod <- CTLscan$ctl[data[2],data[3]]
      qlod1    <- CTLscan$qtl[data[2]]
      qlod2    <- qlod1
      edgetype <- NA
      if(length(CTLobject) >= data[3]){  # Edge type based on QTL LOD scores
        qlod2 <- CTLobject[[data[3]]]$qtl[data[2]]
        if((qlod1-qlod2) > LODdrop){
          edgetype <- 1
        }else if((qlod1-qlod2) < -LODdrop){
          edgetype <- -1
        }else{ edgetype <- 0; }
      } else { 
        cat("Warning: Phenotype", data[3], "from", data[1], "no CTL/QTL information\n")
        qlod2 <- NA; 
      }
      #Store the results
      results <- rbind(results, c(data[1], data[2], data[3], lod, edgetype, qlod1, qlod2))

      if(nodefile == "" && !verbose){ }else{
        if(short){
          edge <- paste(name,traitsn[data[3]])
          edgeI <- paste(traitsn[data[3]],name)
          if(!edge %in% edges && !edgeI %in% edges){
            cat(name, "\t", markern[data[2]],"\t", traitsn[data[3]],"\n",file=netfile, append=TRUE,sep="")
            edges <- c(edges,edge)
          }
        }else{
          cat(name, "\t", "CTL_", data[1],"_",data[3], "\t", markern[data[2]],file=netfile, append=TRUE,sep="")
          cat("\tCTL\t", lod, "\n", file=netfile, append=TRUE,sep="")
          cat(markern[data[2]], "\t", "CTL_", data[1],"_",data[3], "\t",file=netfile, append=TRUE,sep="")
          cat(traitsn[data[3]],"\tCTL\t", lod, "\n", file=netfile,append=TRUE,sep="")
        }
      }
      all_m <- CTLnetwork.addmarker(all_m, mapinfo, markern[data[2]], rownames(CTLscan$dcor)[data[2]])
      all_p <- unique(c(all_p, name, traitsn[data[3]]))
    }
    colnames(results) <- c("TRAIT1","MARKER","TRAIT2","LOD_C","CAUSAL","LOD_T1","LOD_T2")
    if(verbose) cat("NODE.DESCRIPTION\n")
    if(nodefile == "" && !verbose){ }else{
      for(m in all_m){ cat(m,"\n",    sep="", file=nodefile, append=TRUE); }
      for(p in all_p){ cat(p,"\tPHENOTYPE\n", sep="", file=nodefile, append=TRUE); }
    }
  }
  if(!is.null(results)){
    class(results) <- c(class(results),"CTLnetwork")
  }
  invisible(results)
}

CTLnetwork.addmarker <- function(markers, mapinfo, name, realname){
  if(!missing(mapinfo)){
    id      <- which(rownames(mapinfo) %in% realname)
    fname   <- paste(name,"\tMARKER\t",mapinfo[id,1],"\t",mapinfo[id,2],sep="")
    markers <- unique(c(markers, fname))
  }
  return(markers)
}


# generating network


ctl_network = CTLnetworkGn(ctls, significance = input$significance, LODdrop = 2,short = FALSE, add.qtls = FALSE, verbose = TRUE)



json_data <- list(phenotypes = input$phenoData$trait_db_list,significance_data = ctl_significant,image_loc = imageLoc,ctl_plots=ctl_plots,network_file_name =  network_file_name)

json_data <- toJSON(json_data)

write(json_data,file= json_file_path)

