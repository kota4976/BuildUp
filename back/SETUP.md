# BuildUp バックエンド セットアップガイド

このガイドでは、BuildUpバックエンドのセットアップ手順を詳しく説明します。

## 前提条件

- Python 3.10以上
- PostgreSQL 15以上
- Git
- （オプション）Docker & Docker Compose

## ステップ1: リポジトリのクローン

```bash
git clone <repository-url>
cd BuildUp/back
```

## ステップ2: Python仮想環境のセットアップ

```bash
cd api

# 仮想環境を作成
python3.10 -m venv venv

# 仮想環境を有効化
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 依存関係をインストール
pip install --upgrade pip
pip install -r requirements.txt
```

## ステップ3: データベースのセットアップ

### ローカル開発の場合

```bash
# PostgreSQLをインストール（macOS）
brew install postgresql@15
brew services start postgresql@15

# データベースを作成
createdb buildup

# ユーザーとパスワードを設定（必要に応じて）
psql buildup
```

PostgreSQL内で:
```sql
CREATE USER buildup_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE buildup TO buildup_user;
\q
```

### Cloud SQL for PostgreSQLの場合

1. GCPコンソールでCloud SQLインスタンスを作成
2. PostgreSQL 15を選択
3. Private IPを有効化
4. データベース名: `buildup`
5. ユーザー名とパスワードを作成

## ステップ4: 環境変数の設定

```bash
cd api
cp .env.example .env
```

`.env`ファイルを編集:

```env
# Database（ローカル開発）
DATABASE_URL=postgresql://buildup_user:your_password@localhost:5432/buildup

# Database（Cloud SQL - Private IP）
# DATABASE_URL=postgresql://buildup_user:password@<private-ip>:5432/buildup

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost/api/v1/auth/github/callback

# JWT
JWT_SECRET=your-super-secret-key-change-this-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=43200

# Application
APP_NAME=BuildUp
APP_ENV=development
CORS_ORIGINS=http://localhost,http://localhost:80,http://localhost:3000

# Server
API_HOST=127.0.0.1
API_PORT=8080
```

## ステップ5: GitHub OAuthアプリケーションの作成

1. GitHubにログイン
2. Settings > Developer settings > OAuth Apps
3. "New OAuth App"をクリック
4. 以下の情報を入力:
   - Application name: `BuildUp Local`
   - Homepage URL: `http://localhost`
   - Authorization callback URL: `http://localhost/api/v1/auth/github/callback`
5. "Register application"をクリック
6. Client IDをコピーして`.env`の`GITHUB_CLIENT_ID`に設定
7. "Generate a new client secret"をクリック
8. Client Secretをコピーして`.env`の`GITHUB_CLIENT_SECRET`に設定

## ステップ6: データベースマイグレーション

```bash
cd api

# マイグレーションを実行
alembic upgrade head
```

成功すると、すべてのテーブルが作成されます。

確認:
```bash
psql buildup -c "\dt"
```

## ステップ7: 初期データの投入

```bash
cd api

# スキルデータを投入
python scripts/seed_skills.py

# （オプション）テストユーザーを作成
python scripts/create_test_user.py
```

## ステップ8: アプリケーションの起動

### 方法1: 直接起動（開発モード）

```bash
cd api

# 開発サーバーを起動
uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

APIドキュメント: http://localhost:8080/docs

### 方法2: Docker Composeで起動

```bash
cd infra

# コンテナをビルドして起動
docker-compose up -d

# ログを確認
docker-compose logs -f
```

- API: http://localhost/api/v1
- ヘルスチェック: http://localhost/healthz
- APIドキュメント: http://localhost/api/v1/docs

## ステップ9: 動作確認

### ヘルスチェック

```bash
curl http://localhost:8080/healthz
# または Docker Composeの場合
curl http://localhost/healthz
```

期待される応答:
```json
{
  "status": "ok",
  "app": "BuildUp"
}
```

### APIドキュメントの確認

ブラウザで以下にアクセス:
- http://localhost:8080/docs（直接起動）
- http://localhost/api/v1/docs（Docker Compose）

Swagger UIでAPIの仕様を確認できます。

### スキル一覧の取得

```bash
curl http://localhost:8080/api/v1/skills
# または
curl http://localhost/api/v1/skills?query=Python
```

### GitHub OAuth認証のテスト

1. ブラウザで http://localhost:8080/api/v1/auth/github/login にアクセス
2. GitHubの認証ページにリダイレクトされる
3. 認証を許可
4. JWTトークンとユーザー情報が返される

## トラブルシューティング

### データベース接続エラー

エラー: `could not connect to server`

解決策:
1. PostgreSQLが起動しているか確認: `brew services list`
2. DATABASE_URLが正しいか確認
3. データベースが存在するか確認: `psql -l`

### マイグレーションエラー

エラー: `Can't locate revision identified by 'xxx'`

解決策:
```bash
cd api
alembic stamp head
alembic upgrade head
```

### ポート競合エラー

エラー: `Address already in use`

解決策:
```bash
# ポート8080を使用しているプロセスを確認
lsof -i :8080

# プロセスを終了
kill -9 <PID>
```

### GitHub OAuth エラー

エラー: `Failed to get access token from GitHub`

解決策:
1. GitHub OAuth設定を確認
2. Callback URLが完全に一致しているか確認
3. Client IDとClient Secretが正しいか確認

## 次のステップ

1. フロントエンドのセットアップ（別途ドキュメント参照）
2. プロジェクトの作成とテスト
3. WebSocketチャット機能のテスト

## 参考資料

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [SQLAlchemy公式ドキュメント](https://docs.sqlalchemy.org/)
- [Alembic公式ドキュメント](https://alembic.sqlalchemy.org/)
- [PostgreSQL公式ドキュメント](https://www.postgresql.org/docs/)

## サポート

問題が発生した場合は、以下を確認してください:
1. エラーログ
2. データベース接続
3. 環境変数の設定
4. GitHub OAuth設定

