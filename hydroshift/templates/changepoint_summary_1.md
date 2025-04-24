There is **{{ evidence_level }}** evidence that the annual maximum series data at USGS gage {{ gage_id }} are nonstationary in time. Four change
point detection tests were completed to assess changes in the mean, variance, and overall distribution of flood
peaks across the period of record. Significant change points were identified using a Type I error rate of 1 in
{{ arl0 }} and ignoring significant changes in the first {{ burn_in }} years of data. {{ cp_count }} statistically significant
{% if plural -%}
changepoints were
{%- else -%}
changepoint was
{%- endif %}
identified, indicating that
{% if nonstationary -%}
some form of nonstationarity (e.g., land use change, climate change, flow regulation, etc) may be influencing flow patterns at this site.
{%- else -%}
an assumption of nonstationary conditions is likely reasonable.
{%- endif %}
