# BuildUp DB 接続切替仕様

## 1. ドキュメント配置

- **場所**: `/Users/kitayamashuuma/SystemDevelopment/BuildUp/back/infra/DB_DATABASE_SWITCHING.md`
- `back/infra` 配下に置いているため、Docker/インフラ関連の設定と一緒に閲覧できます。

## 2. 目的

ローカル Docker 上の PostgreSQL（`db` サービス）と、SSH トンネル経由で利用する開発用 PostgreSQL（dev DB）を共存させ、開発者が任意で切り替えられるようにする。

## 3. 環境変数と役割

- `DATABASE_TARGET`

  - 受け入れる値: `dev` または `docker`
  - 目的: 接続先 DB を選択
  - 使い分け: `dev` は SSH トンネル経由のリモート DB、`docker` は `docker-compose` の `db` サービス

- `RUNTIME_CONTEXT`

  - 受け入れる値: `local` または `docker`
  - 目的: 実行場所を区別
  - `local`: macOS 上で FastAPI / Alembic / pytest を直接実行するケース
  - `docker`: `buildup-api` コンテナ内で FastAPI が動作するとき（`docker-compose.yml` で自動指定）

- `DATABASE_URL`

  - 任意設定
  - 指定した場合はこの値が常に最優先で使用される
  - ステージング DB など別環境へ一時的につなぐときに利用

- `DATABASE_URL_DOCKER`

  - 例: `postgresql://root:root@db:5432/buildup`
  - `DATABASE_TARGET=docker` の場合に参照されるプリセット

- `DATABASE_URL_DEV_LOCAL`

  - 例: `postgresql://myuser:devsystem@localhost:15432/mydb`
  - `DATABASE_TARGET=dev` かつ `RUNTIME_CONTEXT=local` のときに取得されるプリセット

- `DATABASE_URL_DEV_DOCKER`
  - 例: `postgresql://myuser:devsystem@host.docker.internal:15432/mydb`
  - `DATABASE_TARGET=dev` かつ `RUNTIME_CONTEXT=docker` のときに使用するプリセット

> `.env` に上記すべてを記載済み。必要に応じて値を上書きする。

## 4. 解決ロジック概要

1. `DATABASE_URL` が空でなければ、その値を常に使用。
2. `DATABASE_TARGET` と `RUNTIME_CONTEXT` の組み合わせで、対応するプリセット（上記 URL）を取得。
3. 該当するプリセットが未定義の場合は起動時に例外を投げて知らせる。

FastAPI（`app/database.py`）と Alembic（`alembic/env.py`）は共通で `settings.database_url_resolved` を参照するため、どちらの実行でも同じルールで接続先が決まる。

## 5. よく使う構成と手順

### 5.1 dev DB をローカルから直接利用（FastAPI をホストで起動）

1. ターミナル A で SSH トンネルを張る  
   `ssh -f -N -L 15432:localhost:5432 ubuntu@163.43.218.174`
2. `.env` の `DATABASE_TARGET=dev`、`RUNTIME_CONTEXT=local` を確認（デフォルト）。
3. ターミナル B で `cd back/api && source venv/bin/activate && uvicorn main:app --reload` を実行。

### 5.2 dev DB を Docker から利用（`buildup-api` コンテナ）

1. ホストで SSH トンネルを張る（上記と同じ）。
2. `DATABASE_TARGET` は `dev` のまま、`docker-compose.yml` 側で `RUNTIME_CONTEXT=docker` が自動指定される。
3. `cd back/infra && docker compose up -d api nginx` を実行。  
   `api` コンテナ内では `host.docker.internal:15432` を経由して dev DB に接続できる。

### 5.3 ローカル Docker DB を利用（テストやオフライン開発）

1. `export DATABASE_TARGET=docker`（ホストで FastAPI を動かす場合）  
   または `docker compose up -d` を実行する前に `DATABASE_TARGET=docker docker compose up ...` のように指定。
2. `docker compose up -d db api` で `db` サービスを起動。  
   SSH トンネルは不要。
3. 元に戻すときは `unset DATABASE_TARGET` で `.env` の `dev` に復帰。

### 5.4 一時的に別 DB を使用したい場合

- 例: ステージング DB を触りたいときは `export DATABASE_URL=postgresql://...` を設定して FastAPI/Alembic を実行。
- 終了後は `unset DATABASE_URL` で元の自動切替に戻す。

## 6. トラブルシューティング

- **`psycopg2.OperationalError` で `localhost:15432` に接続できない**  
  SSH トンネルが落ちていないか確認。`lsof -iTCP:15432` でポート使用状況を調べ、不要なプロセスを終了してから再接続する。

- **Docker から dev DB へ接続できず `host.docker.internal` を解決できない**  
  macOS 以外の OS ではホスト名が異なる場合がある。利用している OS に合わせて `DATABASE_URL_DEV_DOCKER` のホスト部を書き換える。

- **Docker DB ↔ dev DB の切替が反映されない**  
  手動で `DATABASE_URL` を設定したままになっていないか確認。`env | grep DATABASE_URL` で値を確認し、不要であれば `unset DATABASE_URL` を実行する。

## 7. 運用のポイント

- `docker compose` で dev DB を使う際にも、ホストで SSH トンネルを張る必要がある点に注意。
- `DATABASE_TARGET` を切り替えるたびにサービス再起動（FastAPI / docker compose / Alembic コマンド）を行い、設定を読み直す。
- CI や自動テストでは `.env` のデフォルト値を前提にするか、ジョブ定義で明示的に `DATABASE_TARGET` を export する。

以上で、ローカル Docker DB と dev 用リモート DB を用途に応じて切り替える手順を統一的に管理できる。
