import streamlit as st
from components.map_component import MapComponent, create_map_container
from components.chat_component import ChatComponent
from components.chart_component import ChartComponent

def generate_answer(prompt):
    response = """
    # 農地データの更新完了

    ## 編集内容
    農地ID: `AG-2024-0123`の境界データを更新しました。

    ### 位置情報
    ```json
    {
        "center": [36.3418, 140.4468],
        "bounds": {
            "north": 36.3428,
            "south": 36.3408,
            "east": 140.4478,
            "west": 140.4458
        }
    }
    ```

    ### 更新された農地情報
    | 項目 | 値 |
    |------|-----|
    | 面積 | 2,500㎡ |
    | 周長 | 200m |
    | 区画形状 | 不整形 |

    ## 変更の詳細
    ✅ 北西角の座標を修正（ドローンデータに基づく補正）
    ✅ 境界線の精度を向上（誤差: 0.5m以内）

    ## 注意事項
    ⚠️ 以下の点に注意が必要です：
    - 北側に隣接する農地（ID: `AG-2024-0124`）と微小な重複（2㎡）があります
    - 南東の境界線が若干不明瞭です（植生による遮蔽）

    ## 推奨アクション
    1. 隣接農地との境界確認
    2. 春季に南東部の再測量を推奨
    3. 灌漑設備の配置図の更新が必要

    ---
    🔄 **更新履歴**
    - 最終更新: 2024-02-21 14:30
    - 更新者: AgriBot
    - 変更理由: ドローン測量データとの整合性確保
    """
    return response

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