# Agri Assistant - WisHub

農地再編成アシスタント

### 1. 動作環境
python 3.10.16

### 2. セットアップ
・requirements.txtから必要なパッケージをインストールしてください。(パッケージ管理用仮想環境ツールの使用をお勧めします。)
```
pip install -r requirements.txt
```

・.envtemplateを開いてGOOGLE_API_KEYの値に自分のGeminiのAPIキーを入力してください。その後、ファイル名を.envに変更して保存してください。

・以下のコマンドを実行してください。
```
python src/for_setup.py
```
↑必要なセットアップを行います。
```
streamlit run src/app/app.py
```
実行後、webサイトが自動で開きます。

### 3. モックの説明



