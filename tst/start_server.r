library(plumber)


# Run the Plumber API
args <- commandArgs(trailingOnly = TRUE)
pr <- plumb(args[1])
pr$run(host  <-  "0.0.0.0", port  <-  as.numeric(args[2]))
