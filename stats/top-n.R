# Script that computes the ratio of defects that the best mbfl, sbfl, and hybrid
# techniques localize in the top-5, top-10, and top-200 of the suspiciousness ranking.
#
# usage: Rscript top-n.R <data_file_real_exploration> <out_dir>
#

# Read file name of the data file and the output directory
args <- commandArgs(trailingOnly = TRUE)
if (length(args)!=2) {
    stop("usage: Rscript top-n.R <data_file_real_exploration> <out_dir>")
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

# New (hybrid) techniques:
#
# "MCBFL", "MCBFL-hybrid-failover", "MCBFL-hybrid-avg", "MCBFL-hybrid-max"
# "MRSBFL", "MRSBFL-hybrid-failover", "MRSBFL-hybrid-avg", "MRSBFL-hybrid-max", "MCBFL-hybrid-avg"

# Show top-n rankings for two hybrid and all existing techniques
flts <- c("MCBFL-hybrid-avg", "MRSBFL-hybrid-avg",
          "DStar", "Ochiai", "Jaccard", "Barinel", "Tarantula", "Op2",
          "Metallaxis", "MUSE")
df <- df[df$FLT %in% flts,]

rank <- rankTopN(df)
for (scheme in c("first", "last", "median")) {
    sorted <- rank[rank$ScoringScheme==scheme & rank$Real==T,]$FLT
    cat("FLTs sorted (", scheme, "): ", sorted, "\n", file=stderr())
}

num_real_bugs <- length(unique(df[df$Real,ID]))

################################################################################
sorted_first <- rank[rank$ScoringScheme=="first" & rank$Real==T,]$FLT
sink(paste(out_dir, "top-n.tex", sep="/"))
for (flt in sorted_first) {
    cat(sprintf("%20s", unique(df[df$FLT==flt,]$TechniqueMacro)))
    for (scheme in c("first", "last", "median")) {
        mask <- df$ScoringScheme==scheme & df$Real & df$FLT==flt
        top5   <- nrow(df[mask & df$ScoreAbs<=5,])/num_real_bugs*100
        top10  <- nrow(df[mask & df$ScoreAbs<=10,])/num_real_bugs*100
        top200 <- nrow(df[mask & df$ScoreAbs<=200,])/num_real_bugs*100
        cat(" & ")
        cat(round(top5, digits=0), "\\%", sep="")
        cat(" & ")
        cat(round(top10, digits=0), "\\%", sep="")
        cat(" & ")
        cat(round(top200, digits=0), "\\%", sep="")
    }
    cat("\\\\ \n")
}
sink()

################################################################################
for (scheme in c("first", "last", "median")) {
    sink(paste(out_dir, "/", "top-n", initialCap(scheme), ".tex", sep=""))
    sorted <- rank[rank$ScoringScheme==scheme & rank$Real==T,]$FLT
    for (flt in sorted) {
        cat(sprintf("%20s", unique(df[df$FLT==flt,]$TechniqueMacro)))
        mask <- df$ScoringScheme==scheme & df$Real & df$FLT==flt
        top5   <- nrow(df[mask & df$ScoreAbs<=5,])/num_real_bugs*100
        top10  <- nrow(df[mask & df$ScoreAbs<=10,])/num_real_bugs*100
        top200 <- nrow(df[mask & df$ScoreAbs<=200,])/num_real_bugs*100
        cat(" & ")
        cat(round(top5, digits=0), "\\%", sep="")
        cat(" & ")
        cat(round(top10, digits=0), "\\%", sep="")
        cat(" & ")
        cat(round(top200, digits=0), "\\%", sep="")
        cat("\\\\ \n")
    }
    sink()
}
