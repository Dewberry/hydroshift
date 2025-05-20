The static changepoint test showed {{ evidence }} evidence of a changepoint in the timeseries.
{% if min_p < 1 -%}
A minimum p-value of {{ min_p }} was obtained at {{ p_count }} contiguous time period{{ 's' if plural else '' }}.
{%- else -%}
There were no time-periods where a p-value less than 0.05 was observed in all tests.
{%- endif %}
The p-value reflects the probability that the distribution of
flood peaks before that date has the **same** distribution as the flood peaks after the date.

{% if len_cp < 1 -%}
The streaming analysis identified one statistically significant changepoint. This changepoint was identified by {{ test_count }} distinct tests: {{ test_list }}.
{%- else -%}
The streaming analysis identified {{ len_cp_str }} statistically significant changepoints. These changepoints broadly fell
into {{ grp_count }} window{{ 's' if plural_2 else '' }} where tests identified changepoints not more than 10 years apart. For a full summary of which
tests identified changes at which dates, see table 2.
{%- endif %}
