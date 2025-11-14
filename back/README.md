# BuildUp Backend

BuildUp APIは開発者とプロジェクトをマッチングするためのバックエンドシステムです。

## 技術スタック

- **FastAPI**: 高速なPython Webフレームワーク
- **PostgreSQL**: リレーショナルデータベース
- **SQLAlchemy**: ORMライブラリ
- **Alembic**: データベースマイグレーションツール
- **OAuth2**: GitHub OAuth認証
- **WebSocket**: リアルタイムチャット機能
- **Docker**: コンテナ化
- **Nginx**: リバースプロキシとSPA配信

## プロジェクト構造

```
back/
├── api/                    # FastAPIアプリケーション
│   ├── app/
│   │   ├── api/           # APIエンドポイント
│   │   │   ├── v1/        # API v1
│   │   │   └── websocket.py
│   │   ├── core/          # コアモジュール（認証、セキュリティ）
│   │   ├── models/        # SQLAlchemyモデル
│   │   ├── schemas/       # Pydanticスキーマ
│   │   ├── services/      # ビジネスロジック
│   │   ├── config.py      # 設定
│   │   └── database.py    # データベース接続
│   ├── alembic/           # マイグレーション
│   ├── main.py            # エントリーポイント
│   ├── requirements.txt   # 依存関係
│   ├── Dockerfile
│   └── .env.example       # 環境変数テンプレート
├── infra/                 # インフラ設定
│   ├── docker-compose.yml
│   └── nginx/
│       └── default.conf
└── db/
    └── migrations/
```

## セットアップ

### 1. 環境変数の設定

```bash
cd api
cp .env.example .env
```

`.env`ファイルを編集して以下の値を設定してください：

```env
DATABASE_URL=postgresql://user:password@localhost:5432/buildup
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost/api/v1/auth/github/callback
JWT_SECRET=your-secret-key-change-this-in-production
```

### 2. GitHub OAuthアプリケーションの作成

1. GitHub Settings > Developer settings > OAuth Apps で新しいアプリを作成
2. Authorization callback URL: `http://localhost/api/v1/auth/github/callback`
3. Client IDとClient Secretを`.env`に設定

### 3. 依存関係のインストール

```bash
cd api
pip install -r requirements.txt
```

### 4. データベースのセットアップ

#### Cloud SQL for PostgreSQLの場合

1. GCPでCloud SQL for PostgreSQLインスタンスを作成
2. Private IPを有効化
3. データベースとユーザーを作成
4. DATABASE_URLを更新

#### ローカル開発の場合

```bash
# PostgreSQLをインストール（macOS）
brew install postgresql@15
brew services start postgresql@15

# データベースを作成
createdb buildup
```

### 5. マイグレーションの実行

```bash
cd api
alembic upgrade head
```

### 6. 初期スキルデータの投入（オプション）

```python
# Python shellで実行
from app.database import SessionLocal
from app.models.skill import Skill

db = SessionLocal()

skills = [
    "Python", "JavaScript", "TypeScript", "Go", "Rust",
    "React", "Vue.js", "Angular", "FastAPI", "Django",
    "PostgreSQL", "MySQL", "MongoDB", "Docker", "Kubernetes",
    "AWS", "GCP", "Azure", "Git", "CI/CD"
]

for skill_name in skills:
    skill = Skill(name=skill_name)
    db.add(skill)

db.commit()
db.close()
```

## 開発モードでの起動

### ローカル起動

```bash
cd api
uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

APIドキュメント: http://localhost:8080/docs

### Docker Composeで起動

```bash
cd infra
docker-compose up -d
```

- Nginx: http://localhost
- API: http://localhost/api/v1
- WebSocket: ws://localhost/ws/chat

## API仕様

### 認証

- `GET /api/v1/auth/github/login` - GitHub OAuth開始
- `GET /api/v1/auth/github/callback` - OAuthコールバック
- `GET /api/v1/auth/me` - 現在のユーザー情報

### ユーザー

- `GET /api/v1/users/{id}` - ユーザー詳細
- `PATCH /api/v1/users/me` - プロフィール更新
- `PUT /api/v1/users/me/skills` - スキル更新
- `POST /api/v1/users/me/repos/sync` - GitHubリポジトリ同期

### スキル

- `GET /api/v1/skills?query=` - スキル検索

### プロジェクト

- `POST /api/v1/projects` - プロジェクト作成
- `GET /api/v1/projects` - プロジェクト一覧
- `GET /api/v1/projects/{id}` - プロジェクト詳細
- `PATCH /api/v1/projects/{id}` - プロジェクト更新
- `POST /api/v1/projects/{id}/favorite` - お気に入り追加
- `DELETE /api/v1/projects/{id}/favorite` - お気に入り解除

### 応募

- `POST /api/v1/projects/{id}/applications` - プロジェクトへ応募
- `GET /api/v1/me/applications` - 自分の応募一覧
- `POST /api/v1/applications/{id}/accept` - 応募承認
- `POST /api/v1/applications/{id}/reject` - 応募拒否

### オファー

- `POST /api/v1/projects/{id}/offers` - オファー送信
- `GET /api/v1/me/offers/sent` - 送信オファー一覧
- `GET /api/v1/me/offers/received` - 受信オファー一覧
- `POST /api/v1/offers/{id}/accept` - オファー承認
- `POST /api/v1/offers/{id}/reject` - オファー拒否

### マッチ

- `GET /api/v1/matches/me/matches` - マッチ一覧
- `GET /api/v1/matches/{id}/conversation` - 会話履歴

### グループチャット

- `POST /api/v1/group-chats` - グループチャット作成（プロジェクトオーナーのみ）
- `GET /api/v1/group-chats` - 自分のグループチャット一覧
- `GET /api/v1/group-chats/{id}` - グループチャット詳細・メッセージ取得
- `PATCH /api/v1/group-chats/{id}` - グループチャット更新
- `POST /api/v1/group-chats/{id}/members` - メンバー追加
- `DELETE /api/v1/group-chats/{id}/members/{user_id}` - メンバー削除
- `GET /api/v1/group-chats/projects/{project_id}/group-conversation` - プロジェクトのグループチャット取得

### WebSocket

- `WS /ws/chat?conversation_id={id}&token={jwt}` - 1対1チャット
- `WS /ws/group-chat?group_conversation_id={id}&token={jwt}` - グループチャット

#### メッセージフォーマット

送信:
```json
{
  "type": "message",
  "body": "メッセージ本文"
}
```

受信:
```json
{
  "type": "message",
  "id": 123,
  "sender_id": "uuid",
  "body": "メッセージ本文",
  "created_at": "2025-11-06T12:00:00Z"
}
```

## デプロイ

### GCE + Cloud SQLでのデプロイ

1. GCEインスタンスを作成
2. Docker と Docker Compose をインストール
3. Cloud SQLへのPrivate IP接続を設定
4. リポジトリをクローン
5. `.env`を設定
6. `docker-compose up -d`で起動

### ファイアウォール設定

- 受信: 0.0.0.0/0 → TCP:80（Nginx）
- 送信: VM → Cloud SQL Private IP:5432

## 監視とログ

### ログの確認

```bash
# Docker logs
docker-compose logs -f api
docker-compose logs -f nginx

# アプリケーションログ
tail -f api/logs/app.log
```

### ヘルスチェック

```bash
curl http://localhost/healthz
```

## トラブルシューティング

### データベース接続エラー

- DATABASE_URLが正しいか確認
- PostgreSQLが起動しているか確認
- Cloud SQLの場合、Private IP接続が有効か確認

### OAuth認証エラー

- GitHub OAuth設定を確認
- Callback URLが正しいか確認
- Client IDとClient Secretが正しいか確認

### WebSocket接続エラー

- JWTトークンが有効か確認
- Conversation IDが存在するか確認
- ユーザーがConversationへのアクセス権を持つか確認

## ライセンス

MIT

