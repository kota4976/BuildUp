# BuildUp デプロイガイド（デモ環境用）

このガイドでは、BuildUp を Cloudflare 経由で永続的に公開する手順を説明します。

## 前提条件

- Cloudflare アカウント（無料プランで利用可能）
- ドメインが Cloudflare で管理されていること
- Docker & Docker Compose がインストールされていること

## セットアップ手順

### 1. Cloudflare Tunnel の作成

1. [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/) にアクセス
2. 「Networks」→「Tunnels」を選択
3. 「Create a tunnel」をクリック
4. トンネル名を入力（例: `buildup-demo`）
5. 「Cloudflared」を選択して「Next」をクリック
6. **トークンをコピーして保存**（後で使用します）

### 2. 環境変数の設定

```bash
cd back/infra
cp .env.cloudflare.example .env.cloudflare
```

`.env.cloudflare`を編集して、取得したトークンを設定：

```env
CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token-here
```

### 3. Cloudflare Dashboard でルーティング設定

1. Cloudflare Zero Trust Dashboard → 「Networks」→「Tunnels」→ 作成したトンネルを選択
2. 「Public Hostnames」タブを選択
3. 「Add a public hostname」をクリック
4. 以下の設定を入力：
   - **Subdomain**: `@`（ルートドメインの場合）またはサブドメイン名
   - **Domain**: あなたのドメイン（例: `example.com`）
   - **Service**: `http://nginx:80`
   - **Path**: （空白のまま）
5. 「Save hostname」をクリック

### 4. API 環境変数の設定

`back/api/.env`を編集：

```env
# GitHub OAuth
GITHUB_REDIRECT_URI=https://yourdomain.com/api/v1/auth/github/callback

# CORS設定
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# アプリケーション環境
APP_ENV=production
```

### 5. GitHub OAuth 設定の更新

1. GitHub Settings > Developer settings > OAuth Apps
2. 既存のアプリを編集、または新しいアプリを作成
3. Authorization callback URL: `https://yourdomain.com/api/v1/auth/github/callback`

### 6. 起動

```bash
cd back/infra

# Cloudflare Tunnelを含めて起動
docker compose --profile cloudflare up -d

# ログを確認
docker compose logs -f cloudflared
docker compose logs -f nginx
docker compose logs -f api
```

### 7. 動作確認

ブラウザで `https://yourdomain.com` にアクセスして動作を確認してください。

## 日常的な操作

### 停止

```bash
docker compose --profile cloudflare down
```

### 再起動

```bash
docker compose --profile cloudflare restart
```

### ログ確認

```bash
# すべてのログ
docker compose --profile cloudflare logs -f

# 特定のサービスのログ
docker compose logs -f cloudflared
docker compose logs -f api
docker compose logs -f nginx
```

### データベースのバックアップ

```bash
# バックアップ
docker compose exec db pg_dump -U root buildup > backup_$(date +%Y%m%d).sql

# リストア
docker compose exec -T db psql -U root buildup < backup_YYYYMMDD.sql
```

## トラブルシューティング

### Cloudflare Tunnel が接続できない

- `.env.cloudflare`のトークンが正しいか確認
- `docker compose logs cloudflared`でエラーを確認
- Cloudflare Dashboard でトンネルのステータスを確認

### サイトにアクセスできない

- Cloudflare Dashboard でルーティング設定を確認
- `docker compose ps`でコンテナが起動しているか確認
- `docker compose logs nginx`で nginx のログを確認

### WebSocket が接続できない

- Cloudflare Dashboard → 「Network」→「WebSockets」が有効になっているか確認

### GitHub OAuth が動作しない

- Callback URL が正確に一致しているか確認
- `CORS_ORIGINS`に正しいドメインが設定されているか確認

## 自動起動設定（サーバー再起動時）

### systemd を使用する場合

`/etc/systemd/system/buildup.service`を作成：

```ini
[Unit]
Description=BuildUp Demo
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/BuildUp/back/infra
ExecStart=/usr/bin/docker compose --profile cloudflare up -d
ExecStop=/usr/bin/docker compose --profile cloudflare down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

有効化：

```bash
sudo systemctl enable buildup.service
sudo systemctl start buildup.service
```

## 参考

- [Cloudflare Tunnel ドキュメント](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
