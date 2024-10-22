# Safety chat system

## 概要
ECDH（楕円曲線ディフィー・ヘルマン鍵共有）とAES暗号化を使用した、Client-Server型の暗号化簡易チャットシステムです。
安全なWebSocketは使わず、カスタムソケットで安全なメッセージ共有システムを実装しています。
Backendの鍵生成や暗号化通信の教材用に作成したので、not実務&実用向き。

Client-Serverですがやっていることは1対1の鍵交換なので、カスタムソケットからブロードキャスト系コードをConnectionManagerに移植するとP2Pにもなります。

接続画面：
<img width="1341" alt="スクリーンショット 2024-10-22 14 36 50" src="https://github.com/user-attachments/assets/c1d59a6d-8eb6-4074-9943-6d88caf2abe7">
チャット画面：
<img width="1352" alt="スクリーンショット 2024-10-22 16 14 44" src="https://github.com/user-attachments/assets/6a6a4fbc-af27-41d5-b475-f8a3e8dbed8f">

## 特徴
- エンドツーエンドの暗号化通信（ECDH + AES）
- リアルタイムのユーザーステータス表示
- カスタムソケットサーバーによる拡張性の高い通信
- 自動的な鍵生成と管理

## 必要要件
- Python 3.8以上
- Django 4.2以上
- 対応ブラウザ（Chrome, Firefox, Safari, Edge最新版）

## セットアップ手順

### 1. リポジトリのクローン
```bash
git clone git@github.com:yuki12tn/safety_chat_system.git
cd secure-chat-system
```

### 2. 仮想環境の作成と有効化
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows
```

### 3. 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定
`.env.example`を`.env`にコピーして必要な値を設定：
```bash
cp .env.example .env
```

```env
# サーバー設定
CHAT_SERVER_HOST=127.0.0.1(好きなIP値でOK)
CHAT_SERVER_PORT=12345(好きなPORT値でOK)
```

### 5. サーバーの起動
別々のターミナルで以下のコマンドを実行：
```bash
# ソケットサーバーの起動
python manage.py run_socket_server

# Djangoサーバーの起動
python manage.py runserver 127.0.0.1:8000
```
一台のパソコンでチャットを試すときはターミナルを複数表示して、`python manage.py runserver 127.0.0.1:8001`や`python manage.py runserver 127.0.0.1:8002`を実行する。

## 使用方法

1. Webブラウザで設定したクライアントサーバーにアクセス

2. 接続画面で以下の情報を入力：
   - ニックネーム：チャットでの表示名
   - パスフレーズ：鍵生成時のシークレットキー。
   - IPアドレス：接続先のサーバーIP（デフォルト: 127.0.0.1）
   - ポート：接続先のポート（デフォルト: 12345）

3. 「Connect」ボタンをクリックして接続

4. チャット画面でメッセージの送受信が可能

## セキュリティ機能

### 暗号化プロトコル
- secp256k1曲線による鍵生成（確認のためbackend/key_storageに鍵出力しています）
- ECDH（secp256k1曲線）による鍵共有
- AES-CTRモードによるメッセージ暗号化
- SHA-256によるハッシュ化

