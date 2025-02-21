import sys
import os

# srcディレクトリをPythonのパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

import streamlit as st
from dotenv import load_dotenv
from components.map_component import MapComponent, create_map_container
from components.chat_component import ChatComponent
from components.chart_component import ChartComponent
from agent.llm.llm import get_llm_model
from agent.agent import Agent

import getpass

load_dotenv()

def generate_answer(prompt):
    """質問に対する回答を生成"""
    agent = Agent()
    initial_input = {
        "prompt": prompt,
        "model": get_llm_model(),
        "messages": []
    }
    thread_config = {
        "configurable": {
            "thread_id": "1",  # 一意のスレッドID
            "checkpoint_ns": "chat",  # チェックポイントの名前空間
            "checkpoint_id": "1"  # チェックポイントID
        }
    }
    response = agent.graph.invoke(initial_input, thread_config, stream_mode="values")
    
    return response["messages"][-1]["content"]

def _add_message_with_scroll(role: str, content: str):
    """メッセージを追加し、必要に応じてスクロールを実行"""
    st.session_state.messages.append({"role": role, "content": content})


class MainLayout:
    def __init__(self):
        st.set_page_config(layout="wide")
    
    def create_layout(self):
        """メインレイアウトの作成"""
        st.title('Agri Assistant')
        return st.columns([5, 5])  # 左、中、右のカラムを返す

def auto_scroll():
    """シンプルな自動スクロール処理"""
    js = """
    <script>
        // Streamlitのメインコンテンツ読み込み完了を待ってスクロール
        window.addEventListener('load', function() {
            window.scrollTo(0, document.body.scrollHeight);
        });

        // 新しいコンテンツが追加されたらスクロール
        new MutationObserver(() => {
            window.scrollTo(0, document.body.scrollHeight);
        }).observe(
            document.querySelector('.main'), 
            { childList: true, subtree: true }
        );
    </script>
    """
    st.components.v1.html(js, height=0)

def main():
    # レイアウトの初期化
    layout = MainLayout()
    map_col, chart_col = layout.create_layout()
    
    # スタイルの追加
    st.markdown("""
        <style>
        body {
            overflow: hidden;  /* 画面全体のスクロールを無効にする */
        }
        [data-testid="stAppViewContainer"] {
            height: 100vh;  /* メインコンテンツの高さを固定 */
            display: flex;
        }
        [data-testid="stVerticalBlock"] {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        [data-testid="column"] {
            height: 100vh;  /* カラムの高さを固定 */
            display: flex;
            flex-direction: column;
            overflow-y: hidden;  /* 縦方向のスクロールを有効にする */
        }
        </style>
    """, unsafe_allow_html=True)

    # チャットコンポーネントの描画（サイドバー）
    with st.sidebar:
        st.markdown("### チャット", help="農地情報の確認・編集")
        chat_component = ChatComponent()
        chat_component.render(generate_answer)

    # 地図コンポーネントの描画（中央カラム）
    with map_col:
        map_component = MapComponent()
        st.markdown("### 地図表示エリア")
        map_data = map_component.render_map()

    # チャートコンポーネントの描画（右カラム）
    with chart_col:
        st.markdown("### チャート表示エリア")
        chart_component = ChartComponent()
        chart_component.render()

if __name__ == "__main__":
    main()