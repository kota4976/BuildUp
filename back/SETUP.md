# BuildUp バックエンド セットアップガイド

BuildUp バックエンドをローカル環境または Docker Compose で動かすための最新手順です。

## 前提条件

- Python 3.10 以上
- PostgreSQL 15 以上（ローカル開発で直接接続する場合）
- Git
- （推奨）`pyenv` などの Python バージョン管理ツール
- （オプション）Docker & Docker Compose

## 1. リポジトリのクローン

```bash
git clone <repository-url>
cd BuildUp/back
```

## 2. ローカル開発環境のセットアップ

```bash
cd api

# 仮想環境の作成と有効化
python3.10 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 仮想環境を有効化
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 依存関係をインストール
pip install --upgrade pip
pip install -r requirements.txt
```

> 既存の仮想環境を使う場合は、適宜読み替えてください。

## 3. データベースの準備（Docker Compose）

ローカルマシンに PostgreSQL を直接インストールする代わりに、Docker Compose でデータベースコンテナを起動します。

### 3-1. 環境ファイルの準備

```bash
cd ../infra
cp .env.example .env
```

`.env` には次の値を設定します：

```env
POSTGRES_DB=buildup
POSTGRES_USER=buildup_user
POSTGRES_PASSWORD=your_password
```

> 既存のコンテナとデータをリセットしたい場合は、`docker compose down -v` を実行してから再度 `docker compose up` をしてください。

### 3-2. データベースコンテナの起動

```bash
docker compose up -d db
docker compose ps db
```

`State` が `healthy` になるまで待ちます。初回起動時やログを確認したい場合は以下を利用してください。

```bash
docker compose logs -f db
```

API 側の設定を続ける場合は `cd ../api` で戻ります。

## 4. 環境変数の設定

以降の手順は `back/api` ディレクトリで実行します。

```bash
cp .env.example .env
```

主要パラメータ：

```env
# Database（Docker Compose の PostgreSQL コンテナを使用）
DATABASE_URL=postgresql://buildup_user:your_password@localhost:5432/buildup

# Docker Compose 内で API も動かす場合は以下のように `db` ホストを指定します
# DATABASE_URL=postgresql://buildup_user:your_password@db:5432/buildup

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

- `JWT_SECRET` は 32 文字以上のランダムな値を推奨します。
- フロントエンドを別ポートで動かす場合は `CORS_ORIGINS` に追加してください。

## 5. Docker Compose 補足

- `infra/.env` は Step 3 で作成した内容をそのまま利用します。
- `docker compose up -d db` でデータベースのみを起動し、API やスクリプトはホスト側の仮想環境から実行できます。
- API も Docker コンテナで動かしたい場合は、Step 4 のコメントにある `DATABASE_URL`（ホスト名 `db`）を使用し、後述の Docker Compose 起動手順を参照してください。

## 6. GitHub OAuth アプリケーション登録

1. GitHub > Settings > Developer settings > OAuth Apps
2. 「New OAuth App」
3. 入力例
   - Application name: `BuildUp Local`
   - Homepage URL: `http://localhost`
   - Authorization callback URL: `http://localhost/api/v1/auth/github/callback`
4. 登録後、Client ID / Client Secret を `.env` に設定

## 7. データベースマイグレーション

```bash
alembic upgrade head  # DBコンテナが起動済みであることを確認してください
```

> API を Docker コンテナで起動している場合は `docker compose exec api alembic upgrade head` を使用します。

成功すると必要なテーブルが作成されます。確認例：

```bash
psql buildup -c "\dt"
```

## 8. 初期データ投入

```bash
# スキルマスタ投入（既存データがある場合はスキップされます）
python scripts/seed_skills.py

# テストユーザーの作成（任意）
python scripts/create_test_user.py
```

## 9. アプリケーションの起動

### 9-1. 直接起動（開発モード）

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

- OpenAPI: http://localhost:8080/docs
- Redoc: http://localhost:8080/redoc

### 9-2. Docker Compose

```bash
cd ../infra
docker compose up -d
docker compose logs -f api
```

- API: http://localhost/api/v1
- ヘルスチェック: http://localhost/healthz
- API ドキュメント: http://localhost/api/v1/docs

> `../web/dist` がマウントされるため、フロントエンドを使用する場合は別途ビルドしておいてください。

## 10. 動作確認

```bash
# ローカル起動時
curl http://localhost:8080/healthz

# Docker Compose利用時
curl http://localhost/healthz
```

期待されるレスポンス：

```json
{ "status": "ok", "app": "BuildUp" }
```

その他の確認例：

- スキル一覧: `curl http://localhost:8080/api/v1/skills`
- GitHub OAuth フロー: `http://localhost:8080/api/v1/auth/github/login`

## 11. テストの実行

```bash
cd api

# 推奨: テスト用DB作成～テスト実行を自動化
./run_tests.sh

# 手動で行う場合
createdb buildup_test
alembic upgrade head
pytest
```

- `scripts/setup_test_db.py` を使うと `createdb` の実行を自動化できます。
- 詳細は `api/TESTING.md` を参照してください。

## 12. トラブルシューティング

### データベース接続エラー (`could not connect to server`)

- PostgreSQL サービスが起動しているか確認：`brew services list`
- `DATABASE_URL` が正しいか確認
- `psql -l` でデータベース存在を確認

### マイグレーションエラー (`Can't locate revision identified by 'xxx'`)

```bash
cd api
alembic stamp head
alembic upgrade head
```

### ポート競合 (`Address already in use`)

```bash
lsof -i :8080
kill -9 <PID>
```

### GitHub OAuth エラー

- GitHub OAuth アプリの Callback URL が一致しているか確認
- Client ID / Client Secret が正しいか再確認
- ローカル環境でプロキシ・VPN を使用していないか確認

## 13. 次のステップ

- フロントエンドのセットアップ（別途ドキュメント参照）
- プロジェクト・マッチング機能の確認
- WebSocket チャット機能の検証（`/ws/chat`）

## 参考資料

- [FastAPI 公式ドキュメント](https://fastapi.tiangolo.com/)
- [SQLAlchemy 公式ドキュメント](https://docs.sqlalchemy.org/)
- [Alembic 公式ドキュメント](https://alembic.sqlalchemy.org/)
- [PostgreSQL 公式ドキュメント](https://www.postgresql.org/docs/)

## サポート

問題が発生した場合は、以下を確認してください：

1. アプリケーション/コンテナのログ
2. データベース接続設定
3. `.env` の値
4. GitHub OAuth 設定
