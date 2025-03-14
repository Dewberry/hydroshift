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
#* @param ARL0 The type of CPM which is used.
#* @param startup The type of CPM which is used.
function(x, cpm_type, ARL0, startup) {
  x <- as.numeric(x)
  ARL0 <- as.numeric(ARL0)
  startup <- as.numeric(startup)
  return (processStream(x, cpm_type, ARL0, startup))
}

#* @get /detect_change_point_batch
#* @param x A vector containing the univariate data stream to be processed.
#* @param cpm_type The type of CPM which is used.
function(x, cpm_type) {
  x <- as.numeric(x)
  return (detectChangePointBatch(x, cpm_type))
}

#* @get /get_batch_threshold
#* @param cpm_type The type of CPM which is used.
#* @param alpha The target p value.
#* @param n The length of the batch sequence.
function(cpm_type, alpha, n) {
  alpha <- as.numeric(alpha)
  n <- as.numeric(n)
  return (getBatchThreshold(cpm_type, alpha, n))
}
