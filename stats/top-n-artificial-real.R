# Script that compares existing mbfl and sbfl techniques according to the top-n
# metric, using artificial and real faults.
#
# usage: Rscript top-n-artificial-real.R <data_file_artificial_real_all_schemes> <out_dir>
#

# Read file name of the data file and the output directory
args <- commandArgs(trailingOnly = TRUE)
if (length(args)!=2) {
    stop("usage: Rscript top-n-artificial-real.R <data_file_artificial_real_all_schemes> <out_dir>")
}
data_file <- args[1]
out_dir <- args[2]

source("util.R")
library(ggplot2)

# Read data file and add two columns
df <- readCsv(data_file)
df$Real <- getReal(df)
df$FaultType <- ifelse(df$Real, "Real faults", "Artificial faults")

df$Scheme <- getScoringSchemes(df)
df$Type   <- getType(df$Technique)

printFLT <- function(df, flt, real, scheme) {
    cat(sprintf("%10s", unique(df[df$FLT==flt,]$TechniqueMacro)))
    for (scheme in c("first")) {
        num_bugs <- length(unique(df[df$Real==real,ID]))
        mask <- df$ScoringScheme==scheme & df$Real==real & df$FLT==flt
        top5   <- nrow(df[mask & df$ScoreAbs<=5,])/num_bugs*100
        top10  <- nrow(df[mask & df$ScoreAbs<=10,])/num_bugs*100
        top200 <- nrow(df[mask & df$ScoreAbs<=200,])/num_bugs*100
        cat(" & ")
        cat(round(top5, digits=0), "\\%", sep="")
        cat(" & ")
        cat(round(top10, digits=0), "\\%", sep="")
        cat(" & ")
        cat(round(top200, digits=0), "\\%", sep="")
    }
}

rank <- rankTopN(df)
real_sorted <- rank[rank$ScoringScheme=="first" & rank$Real==T,]$FLT
art_sorted  <- rank[rank$ScoringScheme=="first" & rank$Real==F,]$FLT
cat("FLTs sorted (real faults): ", real_sorted, "\n", file=stderr())
cat("FLTs sorted (artificial faults): ", art_sorted, "\n", file=stderr())

sink(paste(out_dir, "top-n-artificial-real.tex", sep="/"))
for (i in 1:length(real_sorted)) {
    for (scheme in c("first")) {
        printFLT(df, art_sorted[[i]], FALSE, scheme)
        cat(" & ")
        printFLT(df, real_sorted[[i]], TRUE, scheme)
    }
    cat("\\\\ \n")
}
sink()
