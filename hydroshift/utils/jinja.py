from pathlib import Path

import streamlit as st
from jinja2 import Environment, FileSystemLoader, meta, select_autoescape

from hydroshift import consts

template_dir = Path(__file__).resolve().parent.parent / "templates"

env = Environment(loader=FileSystemLoader(template_dir), autoescape=select_autoescape(["html", "xml"]))


def check_for_consts(template_name: str, context: dict) -> dict:
    """Check if any of the template vars are in consts.py."""
    vars = meta.find_undeclared_variables(env.parse(env.loader.get_source(env, template_name)[0]))
    for var in vars:
        if hasattr(consts, var):
            context[var] = getattr(consts, var)
    return context


@st.cache_data(max_entries=consts.MAX_CACHE_ENTRIES)
def render_template(template_name: str, context: dict = {}) -> str:
    """Load a template from the environment and format it."""
    context = check_for_consts(template_name, context)
    template = env.get_template(template_name)
    return template.render(context)


def write_template(template_name: str, context: dict = {}):
    """Format a template and then write it with st."""
    st.markdown(render_template(template_name, context), unsafe_allow_html=True)
    st.empty()
