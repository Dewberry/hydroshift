library(plumber)
library(cpm)
library(optparse)


#* @get /ping
function() {
  return ("Server is running")
}

#* @post /echo
#* @param data
function(data) {
  return (data)
}

#* @post /sum_test
#* @param data
function(data) {
  data <- as.numeric(data)
  return (sum(data))
}

#* @get /cpm
#* @param data A list of floats
#* @param method A list of floats
function(data, method) {
    data <- as.numeric(data)
    return (detectChangePoint(data, method))
}

#* @get /process_stream
#* @param x A vector containing the univariate data stream to be processed.
#* @param cpm_type The type of CPM which is used.
function(x, cpm_type) {
  x <- as.numeric(x)
  return (processStream(x, cpm_type))
}

