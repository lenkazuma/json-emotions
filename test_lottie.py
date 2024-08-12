
import streamlit as st
from streamlit_lottie import st_lottie
import json
with open("./animation/characterIntro.json", "r",errors='ignore') as f:
    data = json.load(f)
st_lottie(data)
