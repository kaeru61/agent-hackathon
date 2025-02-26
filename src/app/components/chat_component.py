import streamlit as st
import markdown

class ChatComponent:
    def __init__(self):
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "processing" not in st.session_state:
            st.session_state.processing = False

    def render(self, callback_fn):
        st.markdown("""
            <style>
                .chat-container {
                    height: calc(100vh - 200px);
                    flex-direction: column;
                    background: #f8f9fa;
                    border-radius: 8px;
                    overflow: hidden;
                }

                /* 入力エリアのコンテナ */
                .input-container {
                    background: #ffffff;
                    padding: 15px;
                    border-bottom: 1px solid #eee;
                    position: sticky;
                    top: 0;
                    z-index: 1000;
                    height: 60px;
                }

                /* メッセージ表示エリア */
                .messages-container {
                    flex: 1;
                    overflow-y: auto;
                    display: flex;
                    flex-direction: column-reverse;
                }

                .user-message {
                    color: black;
                    padding: 12px 10px;
                    font-size: 0.9em;
                    border-color: #dddddd;
                    border-width: 1px;
                    border-style: solid;
                    border-radius: 6px;
                    margin: 4px 0;
                }

                /* マークダウンテキストのベーススタイル */
                .assistant-message {
                    font-size: 0.9em;  /* 全体的なフォントサイズを小さく */
                    line-height: 1.4;  /* 行間も適度に調整 */
                }

                /* 見出しのサイズ調整 */
                .assistant-message h1 { 
                    font-size: 1.4em;
                    margin: 4px 0;
                }
                
                .assistant-message h2 { 
                    font-size: 1.2em;
                    margin: 3px 0;
                }
                
                .assistant-message h3 { 
                    font-size: 1.1em;
                    margin: 2px 0;
                }

                /* リストとパラグラフの調整 */
                .assistant-message p,
                .assistant-message ul,
                .assistant-message ol {
                    font-size: 0.9em;
                    margin: 4px 0;
                    padding-left: 4px;
                }

                /* コードブロックの調整 */
                .assistant-message pre {
                    font-size: 0.85em;
                    padding: 12px;
                }

                .assistant-message code {
                    font-size: 0.85em;
                    padding: 1px 4px;
                }
                    
                /* テキストエリアのスタイル調整 */
                .stTextArea textarea {
                    min-height: 100px;  /* 最小の高さ */
                    font-size: 0.9em;
                    line-height: 1.5;
                    padding: 10px;
                    border-radius: 4px;
                    resize: vertical;  /* 垂直方向のリサイズのみ許可 */
                }
            </style>
        """, unsafe_allow_html=True)

        # 入力エリア（最上部に固定）
        with st.container():
            prompt = st.text_area(
                "質問を入力してください",
                key=f"chat_input_{len(st.session_state.messages)}",
                height=100,  # 初期の高さ（ピクセル）
                max_chars=None,  # 文字数制限なし
                placeholder="ここに質問を入力してください...",  # プレースホルダーテキスト
            )

        # メッセージ表示エリア（新しいメッセージから表示）
        with st.container():
            # メッセージを逆順に処理
            for i in range(len(st.session_state.messages)-1, -1, -2):
                st.markdown('<div class="message-group">', unsafe_allow_html=True)
                # ユーザーのメッセージ
                st.markdown(
                    f'<div class="user-message">{st.session_state.messages[i-1]["content"]}</div>',
                    unsafe_allow_html=True
                )
                # アシスタントの回答
                if i > 0:
                    st.markdown(
                        f'<div class="assistant-message">{st.session_state.messages[i]["content"]}</div>',
                        unsafe_allow_html=True
                    )
                st.markdown('</div>', unsafe_allow_html=True)

        # メッセージ処理（変更なし）
        if prompt and not st.session_state.processing:
            st.session_state.processing = True
            st.session_state.messages.append({"role": "user", "content": prompt})
            response = callback_fn(prompt)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.processing = False
            st.rerun()