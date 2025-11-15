# API テストガイド

このディレクトリには、BuildUp API のテストが含まれています。

## セットアップ（Docker 使用）

### 前提条件

- Docker Desktop がインストールされ、起動していること
- Python 3.10 以上がインストールされていること

### 依存関係のインストール

```bash
cd back/api
pip install -r requirements.txt
```

## テストの実行

### 推奨：統合テストスクリプト（Docker）

Docker 上でテストデータベースを自動起動してテストを実行します：

```bash
cd back/api
./run_tests.sh
```

このスクリプトは以下を自動で行います：

1. Docker でテスト用 PostgreSQL コンテナを起動（ポート 5433）
2. データベーススキーマをクリーンアップ
3. マイグレーションを実行
4. テストを実行
5. テストデータベースコンテナを停止・削除

### すべてのテストを実行

```bash
cd back/api
pytest
```

### 特定のテストファイルを実行

```bash
pytest tests/test_auth.py
pytest tests/test_users.py
```

### 特定のテスト関数を実行

```bash
pytest tests/test_auth.py::test_get_current_user_authorized
```

### 詳細な出力で実行

```bash
pytest -v
```

### カバレッジレポート付きで実行

```bash
pytest --cov=app --cov-report=html
```

## テストの構造

- `conftest.py`: テスト用のフィクスチャ（テストデータ、クライアントなど）
- `test_health.py`: ヘルスチェックエンドポイントのテスト
- `test_auth.py`: 認証エンドポイントのテスト
- `test_users.py`: ユーザー管理エンドポイントのテスト
- `test_skills.py`: スキル検索エンドポイントのテスト
- `test_projects.py`: プロジェクト管理エンドポイントのテスト
- `test_applications.py`: 応募エンドポイントのテスト
- `test_offers.py`: オファーエンドポイントのテスト
- `test_matches.py`: マッチエンドポイントのテスト

## テストフィクスチャ

`conftest.py`で提供される主要なフィクスチャ：

- `client`: FastAPI TestClient インスタンス
- `db_session`: テスト用データベースセッション
- `test_user`: テスト用ユーザー
- `test_user2`: 2 つ目のテスト用ユーザー
- `test_skill`: テスト用スキル
- `test_skill2`: 2 つ目のテスト用スキル
- `test_project`: テスト用プロジェクト
- `auth_token`: JWT 認証トークン
- `auth_headers`: 認証ヘッダー

## トラブルシューティング

### データベース接続エラー

テストデータベースが存在しない、または PostgreSQL が起動していない可能性があります：

```bash
# データベースを作成
createdb buildup_test

# PostgreSQLが起動しているか確認
brew services list | grep postgresql
```

### インポートエラー

プロジェクトのルートディレクトリから実行していることを確認してください：

```bash
cd api
pytest
```

### テストデータの競合

各テストは独立して実行されるように設計されていますが、問題が発生する場合は：

```bash
# テストを順次実行（並列実行を無効化）
pytest -n 0
```

## カバレッジ

テストカバレッジを確認するには：

```bash
pytest --cov=app --cov-report=term-missing
```

HTML レポートを生成：

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## CI/CD 統合

GitHub Actions などの CI/CD パイプラインでテストを実行する場合：

```yaml
- name: Run tests
  run: |
    createdb buildup_test
    pytest --cov=app --cov-report=xml
```
