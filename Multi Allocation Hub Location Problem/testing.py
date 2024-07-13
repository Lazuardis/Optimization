import streamlit as st
import pandas as pd

df = pd.read_excel('cost_matrix_multi_hub.xlsx')

st.write("Cost Matrix:")
