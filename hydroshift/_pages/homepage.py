import streamlit as st

from hydroshift._pages import summary
from hydroshift.consts import DEFAULT_GAGE
from hydroshift.utils.jinja import write_template

PAGE_CSS = """
        <style>
        .stAppDeployButton {display:none;}
        .stAppHeader {display:none;}
        .block-container {
            text-align: center;
        }
        div.stButton > button {
            border-radius: 12px;
            font-weight: 600;
            background: linear-gradient(135deg, #00c6ff, #4287f5);
            border: none;
            color: white;
            transition: 0.2s ease-in-out;
        }
        div.stButton > button:hover {
            background: linear-gradient(135deg, #ff7e33, #f5a742);
            transform: translateY(-2px);
            box-shadow: 0px 4px 12px rgba(0,0,0,0.25);
            color: black;
        }
        .stApp {
            background: linear-gradient(
                #f5f5f5 0%,
                #f5f5f5 45%,
                #b3c7e8 100%
            ) !important;
        }

        @media (prefers-color-scheme: dark) {
            .stApp {
                background: linear-gradient(
                    #05051c 0%,
                    #05051c 45%,
                    #17428a 100%
                ) !important;
            }
            a {
                color: #d4d4d4 !important;
                text-decoration: none;
            }
            a:hover {
                color: #808080 !important;
                text-decoration: underline;
            }
            p {
                color: #d4d4d4 !important;
            }
        }
        </style>
        """


def homepage():
    """Landing page for app."""
    st.set_page_config(layout="centered", initial_sidebar_state="collapsed")

    st.markdown(
        PAGE_CSS,
        unsafe_allow_html=True,
    )

    with st.container(horizontal_alignment="center"):
        st.title("HydroShift")

        with st.container(horizontal=True, horizontal_alignment="center"):
            st.image("hydroshift/images/logo_base.png", width=400)

        st.subheader("USGS Streamflow Change Detection Tool")
        write_template("app_description.md")

        gage_input = st.text_input("Enter a USGS Gage Number:", placeholder="e.g., 01646500")

        with st.container(horizontal=True, horizontal_alignment="center"):
            submit = st.button("Submit")
            demo = st.button("Use Demo Data")

    st.container(border=False, height=50)

    if submit and gage_input:
        st.session_state["gage_id"] = gage_input
    if demo:
        st.session_state["gage_id"] = DEFAULT_GAGE
    if st.session_state.get("gage_id") is not None:
        st.switch_page(st.Page(summary, title="Gage Summary"))

    write_template("footer.html")


def reset_homepage():
    st.session_state["gage_id"] = None
    st.rerun()
