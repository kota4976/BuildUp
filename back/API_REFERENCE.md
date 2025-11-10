# BuildUp API リファレンス

## 基本情報

- **Base URL**: `http://localhost/api/v1`
- **認証**: Bearer Token (JWT)
- **Content-Type**: `application/json`

## 認証

すべての保護されたエンドポイントには、以下のヘッダーが必要です：

```
Authorization: Bearer <jwt_token>
```

### エンドポイント

#### GitHub OAuth ログイン開始

```
GET /auth/github/login
```

GitHubの認証ページにリダイレクトします。

**クエリパラメータ**:
- `state` (optional): CSRF保護用の状態パラメータ

**レスポンス**: 302 Redirect

---

#### GitHub OAuth コールバック

```
GET /auth/github/callback
```

GitHub認証後のコールバック。JWTトークンを発行します。

**クエリパラメータ**:
- `code` (required): GitHubの認証コード
- `state` (optional): 状態パラメータ

**レスポンス**: 200 OK

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "handle": "username",
    "email": "user@example.com",
    "avatar_url": "https://...",
    "bio": "User bio",
    "github_login": "username",
    "created_at": "2025-11-06T12:00:00Z",
    "updated_at": "2025-11-06T12:00:00Z"
  }
}
```

---

#### 現在のユーザー情報取得

```
GET /auth/me
```

🔒 **認証必要**

**レスポンス**: 200 OK

```json
{
  "id": "uuid",
  "handle": "username",
  "email": "user@example.com",
  "avatar_url": "https://...",
  "bio": "User bio",
  "github_login": "username",
  "created_at": "2025-11-06T12:00:00Z",
  "updated_at": "2025-11-06T12:00:00Z"
}
```

---

## ユーザー

#### ユーザー詳細取得

```
GET /users/{user_id}
```

**レスポンス**: 200 OK

```json
{
  "id": "uuid",
  "handle": "username",
  "email": "user@example.com",
  "avatar_url": "https://...",
  "bio": "User bio",
  "github_login": "username",
  "created_at": "2025-11-06T12:00:00Z",
  "updated_at": "2025-11-06T12:00:00Z",
  "skills": [
    {
      "skill_id": 1,
      "skill_name": "Python",
      "level": 5
    }
  ],
  "repos": [
    {
      "id": 1,
      "repo_full_name": "user/repo",
      "stars": 100,
      "language": "Python",
      "url": "https://github.com/user/repo",
      "last_pushed_at": "2025-11-06T12:00:00Z"
    }
  ]
}
```

---

#### プロフィール更新

```
PATCH /users/me
```

🔒 **認証必要**

**リクエストボディ**:

```json
{
  "bio": "Updated bio",
  "avatar_url": "https://new-avatar-url.com/avatar.jpg"
}
```

**レスポンス**: 200 OK（ユーザー情報）

---

#### スキル更新

```
PUT /users/me/skills
```

🔒 **認証必要**

**リクエストボディ**:

```json
[
  {
    "skill_id": 1,
    "level": 5
  },
  {
    "skill_id": 2,
    "level": 3
  }
]
```

**レスポンス**: 200 OK

```json
{
  "message": "Skills updated successfully"
}
```

---

#### GitHubリポジトリ同期

```
POST /users/me/repos/sync
```

🔒 **認証必要**

GitHubからリポジトリ情報を取得して同期します。

**レスポンス**: 200 OK

```json
{
  "message": "Successfully synced 10 repositories"
}
```

---

## スキル

#### スキル検索

```
GET /skills
```

**クエリパラメータ**:
- `query` (optional): 検索クエリ
- `limit` (optional, default: 20): 最大取得数

**レスポンス**: 200 OK

```json
{
  "skills": [
    {
      "id": 1,
      "name": "Python"
    },
    {
      "id": 2,
      "name": "JavaScript"
    }
  ]
}
```

---

## プロジェクト

#### プロジェクト作成

```
POST /projects
```

🔒 **認証必要**

**リクエストボディ**:

```json
{
  "title": "Project Title",
  "description": "Project description",
  "required_skills": [
    {
      "skill_id": 1,
      "required_level": 3
    }
  ]
}
```

**レスポンス**: 201 Created

```json
{
  "id": "uuid",
  "owner_id": "uuid",
  "title": "Project Title",
  "description": "Project description",
  "status": "open",
  "created_at": "2025-11-06T12:00:00Z",
  "updated_at": "2025-11-06T12:00:00Z"
}
```

---

#### プロジェクト一覧

```
GET /projects
```

**クエリパラメータ**:
- `query` (optional): 検索クエリ（タイトル・説明）
- `skill_id` (optional): スキルIDでフィルタ
- `owner_id` (optional): オーナーIDでフィルタ
- `status` (optional): ステータスでフィルタ
- `limit` (optional, default: 20): 最大取得数
- `offset` (optional, default: 0): オフセット

**レスポンス**: 200 OK

```json
{
  "projects": [
    {
      "id": "uuid",
      "owner_id": "uuid",
      "title": "Project Title",
      "description": "Project description",
      "status": "open",
      "created_at": "2025-11-06T12:00:00Z",
      "updated_at": "2025-11-06T12:00:00Z",
      "required_skills": [
        {
          "skill_id": 1,
          "skill_name": "Python",
          "required_level": 3
        }
      ],
      "is_favorited": false
    }
  ],
  "total": 100
}
```

---

#### プロジェクト詳細

```
GET /projects/{project_id}
```

**レスポンス**: 200 OK（プロジェクト詳細）

---

#### プロジェクト更新

```
PATCH /projects/{project_id}
```

🔒 **認証必要**（オーナーのみ）

**リクエストボディ**:

```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "status": "closed",
  "required_skills": [
    {
      "skill_id": 1,
      "required_level": 4
    }
  ]
}
```

**レスポンス**: 200 OK（更新されたプロジェクト）

---

#### お気に入り追加

```
POST /projects/{project_id}/favorite
```

🔒 **認証必要**

**レスポンス**: 200 OK

```json
{
  "message": "Project added to favorites"
}
```

---

#### お気に入り解除

```
DELETE /projects/{project_id}/favorite
```

🔒 **認証必要**

**レスポンス**: 200 OK

```json
{
  "message": "Project removed from favorites"
}
```

---

## 応募（Applications）

#### プロジェクトに応募

```
POST /projects/{project_id}/applications
```

🔒 **認証必要**

**リクエストボディ**:

```json
{
  "message": "I'm interested in this project!"
}
```

**レスポンス**: 201 Created

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "applicant_id": "uuid",
  "message": "I'm interested in this project!",
  "status": "pending",
  "created_at": "2025-11-06T12:00:00Z",
  "updated_at": "2025-11-06T12:00:00Z"
}
```

---

#### 自分の応募一覧

```
GET /me/applications
```

🔒 **認証必要**

**レスポンス**: 200 OK

```json
{
  "applications": [...]
}
```

---

#### 応募を承認

```
POST /applications/{application_id}/accept
```

🔒 **認証必要**（プロジェクトオーナーのみ）

**レスポンス**: 200 OK

```json
{
  "message": "Application accepted"
}
```

---

#### 応募を拒否

```
POST /applications/{application_id}/reject
```

🔒 **認証必要**（プロジェクトオーナーのみ）

**レスポンス**: 200 OK

```json
{
  "message": "Application rejected"
}
```

---

## オファー（Offers）

#### オファーを送信

```
POST /projects/{project_id}/offers
```

🔒 **認証必要**（プロジェクトオーナーのみ）

**リクエストボディ**:

```json
{
  "receiver_id": "uuid",
  "message": "We'd love to have you on our project!"
}
```

**レスポンス**: 201 Created

---

#### 送信したオファー一覧

```
GET /me/offers/sent
```

🔒 **認証必要**

**レスポンス**: 200 OK

```json
{
  "offers": [...]
}
```

---

#### 受信したオファー一覧

```
GET /me/offers/received
```

🔒 **認証必要**

**レスポンス**: 200 OK

```json
{
  "offers": [...]
}
```

---

#### オファーを承認

```
POST /offers/{offer_id}/accept
```

🔒 **認証必要**（受信者のみ）

**レスポンス**: 200 OK

```json
{
  "message": "Offer accepted"
}
```

---

#### オファーを拒否

```
POST /offers/{offer_id}/reject
```

🔒 **認証必要**（受信者のみ）

**レスポンス**: 200 OK

```json
{
  "message": "Offer rejected"
}
```

---

## マッチ

#### 自分のマッチ一覧

```
GET /matches/me/matches
```

🔒 **認証必要**

**レスポンス**: 200 OK

```json
{
  "matches": [
    {
      "id": "uuid",
      "project_id": "uuid",
      "user_a": "uuid",
      "user_b": "uuid",
      "created_at": "2025-11-06T12:00:00Z"
    }
  ]
}
```

---

#### 会話履歴取得

```
GET /matches/{match_id}/conversation
```

🔒 **認証必要**

**クエリパラメータ**:
- `limit` (optional, default: 50): 最大メッセージ数
- `before_id` (optional): このメッセージIDより前のメッセージを取得

**レスポンス**: 200 OK

```json
{
  "id": "uuid",
  "match_id": "uuid",
  "messages": [
    {
      "id": 1,
      "conversation_id": "uuid",
      "sender_id": "uuid",
      "body": "Hello!",
      "created_at": "2025-11-06T12:00:00Z"
    }
  ],
  "has_more": false
}
```

---

## WebSocket

#### チャット接続

```
WS /ws/chat?conversation_id={uuid}&token={jwt}
```

🔒 **認証必要**（クエリパラメータでJWT）

**送信メッセージ**:

```json
{
  "type": "message",
  "body": "Hello!"
}
```

**受信メッセージ**:

```json
{
  "type": "message",
  "id": 123,
  "sender_id": "uuid",
  "body": "Hello!",
  "created_at": "2025-11-06T12:00:00Z"
}
```

**Ping/Pong**:

送信:
```json
{
  "type": "ping"
}
```

受信:
```json
{
  "type": "pong"
}
```

---

## エラーレスポンス

すべてのエラーは以下の形式で返されます：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### HTTPステータスコード

- `200 OK`: 成功
- `201 Created`: リソース作成成功
- `400 Bad Request`: リクエストが不正
- `401 Unauthorized`: 認証が必要または認証失敗
- `403 Forbidden`: アクセス権限がない
- `404 Not Found`: リソースが見つからない
- `500 Internal Server Error`: サーバーエラー

---

## レート制限

現在、レート制限は実装されていません。本番環境では適切なレート制限を実装することを推奨します。

---

## API バージョニング

現在のAPIバージョン: `v1`

将来的に破壊的変更が必要な場合は、新しいバージョン（v2）を提供します。

