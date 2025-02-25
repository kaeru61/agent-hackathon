import sys
import os

# srcディレクトリをPythonのパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

import streamlit as st
from dotenv import load_dotenv
from components.map_component import MapComponent
from components.colored_component import ColorMapComponent
from components.colored_map_reorg_component import ColorReorgMapComponent
from components.chat_component import ChatComponent
from components.map_reorg_component import MapReorgComponent
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
        "messages": [],
        "execute_tasks": False
    }
    thread_config = {
        "configurable": {
            "thread_id": "1",  # 一意のスレッドID
            "checkpoint_ns": "chat",  # チェックポイントの名前空間
            "checkpoint_id": "1"  # チェックポイントID
        }
    }
    response = agent.graph.invoke(initial_input, thread_config, stream_mode="values")
    print(response)
    if response["current_role"] == 1 and response["current_task"] == 2 and response["execute_tasks"]:
        print("色分けマップを表示")
        st.session_state["show_color_map"] = True
    elif response["current_role"] == 1 and response["current_task"] == 2:
        st.session_state["show_color_map"] = False

    if response["current_role"] == 1 and response["current_task"] == 3:
        st.session_state["show_reorg_map"] = True
    
    return response["messages"][-1]["content"]

def _add_message_with_scroll(role: str, content: str):
    """メッセージを追加し、必要に応じてスクロールを実行"""
    st.session_state.messages.append({"role": role, "content": content})


class MainLayout:
    def __init__(self):
        st.set_page_config(layout="wide")
        if "show_color_map" not in st.session_state:
            st.session_state["show_color_map"] = False
        if "show_reorg_map" not in st.session_state:
            st.session_state["show_reorg_map"] = False
    
    def create_layout_reorg(self):
        """メインレイアウトの作成"""
        st.title('Agri Assistant')
        return st.columns([5, 5])
    
    def create_layout(self):
        """メインレイアウトの作成"""
        st.title('Agri Assistant')

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
    if st.session_state["show_reorg_map"]:
        map_col, chart_col = layout.create_layout_reorg()
        
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
            map_color_component = ColorMapComponent()
            st.markdown("### 再編成地図表示")
            if not st.session_state.show_color_map:
                map_component.render_map()
            else:
                map_color_component.render_map()

        # チャートコンポーネントの描画（右カラム）
        with chart_col:
            map_reorg_component = MapReorgComponent()
            map_color_reorg_component = ColorReorgMapComponent()
            st.markdown("### 再編成後地図表示")
            if not st.session_state.show_color_map:
                map_reorg_component.render_map()
            else:
                map_color_reorg_component.render_map()
    else:
        layout.create_layout()

        # チャットコンポーネントの描画（サイドバー）
        with st.sidebar:
            st.markdown("### チャット", help="農地情報の確認・編集")
            chat_component = ChatComponent()
            chat_component.render(generate_answer)
        # 地図コンポーネントの描画（中央カラム）
        map_component = MapComponent()
        map_color_component = ColorMapComponent()
        st.markdown("### 地図表示エリア")
        if not st.session_state.show_color_map:
            map_component.render_map()
        else:
            map_color_component.render_map()


if __name__ == "__main__":
    main()