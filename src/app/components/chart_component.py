import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

class ChartComponent:
    def render(self):
        # ダミーデータの作成
        data = pd.DataFrame({
            'date': pd.date_range(start='2025-01-01', periods=100),
            'value': np.random.randn(100).cumsum()
        })

        # Altairを使ったチャートの作成
        chart = alt.Chart(data).mark_line().encode(
            x='date:T',
            y='value:Q'
        ).properties(
            width='container',
            height=400
        )

        # チャートの表示
        st.altair_chart(chart, use_container_width=True)
