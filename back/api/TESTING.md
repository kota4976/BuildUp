# API テスト実行ガイド

BuildUp APIのテストを実行するためのガイドです。

## クイックスタート

### 1. 依存関係のインストール

```bash
cd api
pip install -r requirements.txt
```

### 2. テスト用データベースの作成

```bash
createdb buildup_test
```

または、フルパスを使用：

```bash
/opt/homebrew/opt/postgresql@15/bin/createdb buildup_test
```

### 3. テストの実行

```bash
# すべてのテストを実行
pytest

# 詳細な出力で実行
pytest -v

# 特定のテストファイルを実行
pytest tests/test_auth.py

# 特定のテスト関数を実行
pytest tests/test_auth.py::test_get_current_user_authorized
```

### 4. テストスクリプトを使用（推奨）

```bash
./run_tests.sh
```

このスクリプトは以下を自動的に実行します：
- テストデータベースの存在確認・作成
- マイグレーションの実行
- テストの実行

## テスト構成

### テストファイル

- `tests/test_health.py` - ヘルスチェックエンドポイント
- `tests/test_auth.py` - 認証エンドポイント
- `tests/test_users.py` - ユーザー管理エンドポイント
- `tests/test_skills.py` - スキル検索エンドポイント
- `tests/test_projects.py` - プロジェクト管理エンドポイント
- `tests/test_applications.py` - 応募エンドポイント
- `tests/test_offers.py` - オファーエンドポイント
- `tests/test_matches.py` - マッチエンドポイント

### テストフィクスチャ

`tests/conftest.py`で定義されている主要なフィクスチャ：

- `client` - FastAPI TestClient
- `db_session` - テスト用データベースセッション
- `test_user` - テスト用ユーザー
- `test_user2` - 2つ目のテスト用ユーザー
- `test_skill` - テスト用スキル
- `test_skill2` - 2つ目のテスト用スキル
- `test_project` - テスト用プロジェクト
- `auth_token` - JWT認証トークン
- `auth_headers` - 認証ヘッダー

## テストの実行方法

### すべてのテストを実行

```bash
pytest
```

### カバレッジレポート付きで実行

```bash
# カバレッジレポートをインストール（初回のみ）
pip install pytest-cov

# カバレッジ付きでテスト実行
pytest --cov=app --cov-report=term-missing

# HTMLレポートを生成
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### 特定のテストのみ実行

```bash
# 認証関連のテストのみ
pytest tests/test_auth.py

# プロジェクト関連のテストのみ
pytest tests/test_projects.py

# 特定のテスト関数のみ
pytest tests/test_auth.py::test_get_current_user_authorized
```

### 並列実行（高速化）

```bash
# pytest-xdistをインストール（初回のみ）
pip install pytest-xdist

# 並列実行
pytest -n auto
```

### 失敗したテストのみ再実行

```bash
pytest --lf  # Last failed
```

## トラブルシューティング

### テストデータベースが存在しない

```bash
createdb buildup_test
```

### PostgreSQLが起動していない

```bash
brew services start postgresql@15
```

### インポートエラー

プロジェクトのルートディレクトリ（`api/`）から実行していることを確認：

```bash
cd api
pytest
```

### テストが遅い

- 並列実行を使用：`pytest -n auto`
- 必要のないテストをスキップ：`pytest -k "not slow"`

### テストデータの競合

各テストは独立して実行されるように設計されていますが、問題が発生する場合は：

```bash
# 順次実行（並列実行を無効化）
pytest -n 0
```

## CI/CD統合

### GitHub Actionsの例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: buildup_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/buildup_test
        run: |
          pytest --cov=app --cov-report=xml
```

## テストの追加

新しいテストを追加する場合は、以下のパターンに従ってください：

```python
def test_new_feature(client: TestClient, auth_headers: dict):
    """Test description"""
    response = client.get("/api/v1/endpoint", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

## ベストプラクティス

1. **テストは独立させる**: 各テストは他のテストに依存しないようにする
2. **明確な名前付け**: テスト関数名は何をテストしているか明確にする
3. **適切なアサーション**: 期待される結果を明確に検証する
4. **フィクスチャの活用**: 共通のテストデータはフィクスチャを使用
5. **エッジケースのテスト**: 正常系だけでなく異常系もテストする

## 参考資料

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine)

