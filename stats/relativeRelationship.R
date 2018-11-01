# Script that computes the Spearman's rho correlation coefficient and associated
# p-value for the following ranking metrics between artificial and real faults:
# - EXAM score
# - Tournament ranking (EXAM score)
# - FLT rank
# - Top-n rank
#
# The script computes the correlation for all faults and for the following
# types of faults:
# * multi line faults
#   - multi line with omission
#   - multi line without omission
# * single line faults
#   - single line with omission
#   - single line without omission
#
# usage: Rscript relativeRelationship.R
#                    <data_file_artificial_real>
#                    <data_file_multiline_with_omission>
#                    <data_file_multiline_without_omission>
#                    <data_file_singleline_with_omission>
#                    <data_file_singleline_without_omission>
#                    <out_dir>
#

# Read file names of the data files and the output directory
args <- commandArgs(trailingOnly = TRUE)
if (length(args)!=6) {
    stop("usage: Rscript relativeRelationship.R
            <data_file_artificial_real>
            <data_file_multiline_with_omission>
            <data_file_multiline_without_omission>
            <data_file_singleline_with_omission>
            <data_file_singleline_without_omission>
            <out_dir>")
}

# Output directory for all generated files
out_dir <- args[6]

source("util.R")

tournamentPointsMean <- function(wide, techniques, metric) {
  result <- rep(0, length(techniques))
  for (i in 1:(length(techniques)-1)) {
    for (j in (i+1):length(techniques)) {
      flt1_col <- paste(metric, techniques[i], sep="_")
      flt2_col <- paste(metric, techniques[j], sep="_")
      # No need to run the t-test if the samples are identical
      if (identical(wide[[flt1_col]], wide[[flt2_col]])) {
        p   <- 1;
        est <- 0;
      } else {
        t_test <- t.test(wide[[flt1_col]], wide[[flt2_col]], paired=TRUE)
        p      <- t_test$p.value
        est    <- t_test$estimate
      }
      # TODO: Check whether we need a correction for multiple comparisons here
      if (p < 0.05) {
        winner = if (est < 0) i else j
        result[winner] = result[winner]+1
      }
    }
  }
  return(result)
}

generateTable <- function(name, header, techniques, valuesReal, valuesArtf, suffix = "", decreasing = FALSE, digits = 4, integer=FALSE) {
    if(nchar(suffix) > 0) {
        name = paste(name, suffix, sep="_")
    }
    print(name)
    TABLE = paste(out_dir, "/table_", name, ".tex", sep="")
    unlink(TABLE)
    sink(TABLE, append=TRUE, split=FALSE)
    cat("\\begin{tabular}{lC{20mm}@{\\hspace{2em}}lC{20mm}}\\toprule", "\n")
    cat("\\multicolumn{2}{c}{\\textbf{Artificial Faults}} & \\multicolumn{2}{c}{\\textbf{Real Faults}} \\\\", "\n")
    cat("\\cmidrule(r){1-2} \n")
    cat("\\cmidrule{3-4} \n")
    cat("Technique & ", header, " & Technique & ", header, "\\\\ \n")
    cat("\\midrule","\n")
    realSorted = sort.int(valuesReal, index.return=TRUE, decreasing=decreasing)$ix
    artfSorted = sort.int(valuesArtf, index.return=TRUE, decreasing=decreasing)$ix
    format_char = ifelse(integer, "d", "f")
    for (i in 1:length(techniques)) {
        indexReal = realSorted[i]
        indexArtf = artfSorted[i]
        cat(
            prettifyTechniqueName(techniques[indexArtf]), " & ",
            formatC(valuesArtf[indexArtf], digits=digits, format=format_char), " & ",
            prettifyTechniqueName(techniques[indexReal]), " & ",
            formatC(valuesReal[indexReal], digits=digits, format=format_char),
            "\\\\ \n")
    }
    cat("\\bottomrule","\n")
    cat("\\end{tabular}","\n")
    sink()

    REAL_ROW = paste(out_dir, "/table_", name, "_RealRow.tex", sep="")
    unlink(REAL_ROW)
    sink(REAL_ROW, append=TRUE, split=FALSE)
    cat(sapply(techniques[realSorted], prettifyTechniqueName), sep=" & ")
    sink()
    ARTF_ROW = paste(out_dir, "/table_", name, "_ArtfRow.tex", sep="")
    unlink(ARTF_ROW)
    sink(ARTF_ROW, append=TRUE, split=FALSE)
    cat(sapply(techniques[artfSorted], prettifyTechniqueName), sep=" & ")
    sink()
}

# The fault categories -- suffix for file names
fault_type_suffix <- c("all_faults",
                       "multiline",
                       "multiline_with_omission",
                       "multiline_without_omission",
                       "singleline",
                       "single_line_with_omission",
                       "single_line_without_omission")
# The fault categories -- macros for LaTex tables
fault_type_macros <- c("\\allFaults",
                       "\\multiline",
                       "\\multilineWithOmission",
                       "\\multilineWithoutOmission",
                       "\\singleline",
                       "\\singlelineWithOmission",
                       "\\singlelineWithoutOmission")

# Summary data and number of bugs for all fault types
data_all_types <- list()
data_num_bugs <- list()

for(data_index in 1:length(fault_type_suffix)) {
    data_name = fault_type_suffix[data_index]
    # TODO: We currently shoehorn all multi-line and single-line results into
    # the tables with the rbind hack below. Make sure that the args indices are
    # correct.
    if (data_name=="multiline") {
        df <- rbind(readCsv(args[2]), readCsv(args[3]))
    } else if (data_name=="singleline") {
        df <- rbind(readCsv(args[4]), readCsv(args[5]))
    } else {
        data_file = args[ifelse(data_index>4, data_index-2,
                         ifelse(data_index>1, data_index-1,
                         data_index))]
        df <- readCsv(data_file)
    }
    df$Real <- getReal(df)
    df$Technique <- getTechniques(df)
    # Cast data to wide format
    wide <- dcast(setDT(df), "ID + Real ~ Technique", value.var=scoring_metrics)

    real_points_mean = tournamentPointsMean(wide[wide$Real,], techniques, "ScoreWRTLoadedClasses")
    artificial_points_mean = tournamentPointsMean(wide[!wide$Real,], techniques, "ScoreWRTLoadedClasses")

    real_points_rank = tournamentPointsMean(wide[wide$Real,], techniques, "RANK")
    artificial_points_rank = tournamentPointsMean(wide[!wide$Real,], techniques, "RANK")

    # Compute all relevant rankings
    technique_summaries <- data.frame(
        Technique=techniques,
        RealPoints=real_points_mean,
        ArtfPoints=artificial_points_mean,
        RealMean=rep(0, length(techniques)),
        ArtfMean=rep(0, length(techniques)),
        RealRankMean=rep(0, length(techniques)),
        ArtfRankMean=rep(0, length(techniques)),
        RealTopN=rep(0, length(techniques)),
        ArtfTopN=rep(0, length(techniques)))

    for (i in 1:length(techniques)) {
        real <- df[df$Real & (df$Technique==techniques[i]),]
        artf <- df[(!df$Real) & (df$Technique==techniques[i]),]
        technique_summaries$RealMean[i] = mean(real$ScoreWRTLoadedClasses)
        technique_summaries$ArtfMean[i] = mean(artf$ScoreWRTLoadedClasses)
        technique_summaries$RealRankMean[i] = mean(real$RANK)
        technique_summaries$ArtfRankMean[i] = mean(artf$RANK)
        num_real <- length(unique(real$ID))
        num_artf <- length(unique(artf$ID))
        technique_summaries$RealTopN[i] <- nrow(real[real$RANK<=5,])/num_real
        technique_summaries$ArtfTopN[i] <- nrow(artf[artf$RANK<=5,])/num_artf
    }

    data_all_types[[data_index]] <- technique_summaries

    num_bugs <- nrow(wide[wide$Real,])
    data_num_bugs[[data_index]] <- num_bugs

    generateTable("TournamentScore", "\\# Sig. worse",  techniques, real_points_mean, artificial_points_mean, suffix = data_name, decreasing = TRUE, integer = TRUE)
    generateTable("TournamentRank", "\\# Sig. worse",  techniques, real_points_rank, artificial_points_rank, suffix = data_name, decreasing = TRUE, integer = TRUE)
    generateTable("ScoreMean", "\\exam Score",  techniques, technique_summaries$RealMean, technique_summaries$ArtfMean, suffix = data_name, decreasing = FALSE)
    generateTable("RankMean", "\\fltRank",  techniques, technique_summaries$RealRankMean, technique_summaries$ArtfRankMean, digits=2, suffix = data_name, decreasing = FALSE)
}

# Print a summary table, indicting which scores show a significant correlation
# for which fault types -- one row per fault type
file_name <- paste(out_dir, "table_correlation_rankings_by_score_and_fault_type_row.tex", sep="/")
sink(file_name)
# Print header as comment
cat("%% fault_type")
for(score in c("Mean", "Points", "RankMean", "TopN")) {
    cat(paste(" & ", score, sep=""))
}
cat("\\\\ \n")

for(data_index in 1:length(fault_type_macros)) {
    fault_type <- fault_type_macros[[data_index]]
    num_bugs <- data_num_bugs[[data_index]]
    cat(fault_type, "&", num_bugs)
    for(score in c("Mean", "Points", "RankMean", "TopN")) {
        technique_summaries <- data_all_types[[data_index]]
        col_real <- paste("Real", score, sep="")
        col_artf <- paste("Artf", score, sep="")

        cor <- cor.test(technique_summaries[[col_artf]], technique_summaries[[col_real]], method="spearman", exact=FALSE)
        est <- round(cor$estimate, digits=2)
        if (cor$p.value<0.05) {
            cat(" & ", est, sep="")
        } else {
            cat(" & \\correlationInsig")
        }
    }
    cat("\\\\ \n")
}
sink()
