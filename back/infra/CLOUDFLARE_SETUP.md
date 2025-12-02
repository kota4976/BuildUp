# Cloudflare で BuildUp を公開する方法

このガイドでは、BuildUp システムを Cloudflare 経由で公開する方法を説明します。

## クイックスタート（Cloudflare Tunnel）

最も簡単でセキュアな方法：

1. [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/) でトンネルを作成
2. トークンを取得
3. `back/infra/.env.cloudflare` にトークンを設定
4. `docker compose --profile cloudflare up -d` で起動

**詳細な手順は `DEPLOY.md` を参照してください。**

---

## 方法 1: Cloudflare Tunnel（推奨）

Cloudflare Tunnel は、ポートを公開せずにアプリケーションを安全に公開できる方法です。最もセキュアで推奨される方法です。

### 前提条件

- Cloudflare アカウント（無料プランで利用可能）
- ドメインが Cloudflare で管理されていること
- Docker がインストールされていること

### セットアップ手順

#### 1. Cloudflare Zero Trust のセットアップ

1. [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/) にアクセス
2. 「Networks」→「Tunnels」を選択
3. 「Create a tunnel」をクリック
4. トンネル名を入力（例: `buildup-tunnel`）
5. 「Cloudflared」を選択して「Next」をクリック
6. トークンが表示されるので、コピーして保存（後で使用します）

#### 2. 環境変数ファイルの作成

```bash
cd back/infra
cp .env.cloudflare.example .env.cloudflare
```

`.env.cloudflare`を編集して、Cloudflare Zero Trust Dashboard で取得したトークンを設定：

```env
CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token-here
```

#### 3. ルーティング設定

Cloudflare Zero Trust Dashboard でルーティングを設定：

1. 「Networks」→「Tunnels」→ 作成したトンネルを選択
2. 「Public Hostnames」タブを選択
3. 「Add a public hostname」をクリック
4. 以下の設定を入力：
   - **Subdomain**: `@`（ルートドメインの場合）またはサブドメイン名
   - **Domain**: あなたのドメイン（例: `example.com`）
   - **Service**: `http://nginx:80`
   - **Path**: （空白のまま）
5. 「Save hostname」をクリック

複数のドメイン（例: `www`）を追加する場合は、同様の手順で追加してください。

#### 4. 環境変数の設定

`back/api/.env`を更新：

```env
# GitHub OAuth（本番環境用）
GITHUB_REDIRECT_URI=https://yourdomain.com/api/v1/auth/github/callback

# CORS設定（本番環境用）
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# アプリケーション環境
APP_ENV=production
```

#### 5. GitHub OAuth 設定の更新

1. GitHub Settings > Developer settings > OAuth Apps
2. 既存のアプリを編集、または新しいアプリを作成
3. Authorization callback URL: `https://yourdomain.com/api/v1/auth/github/callback`

#### 6. 起動

```bash
cd back/infra
# Cloudflare Tunnelを含めて起動
docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml up -d

# ログを確認
docker compose logs -f cloudflared
```

トンネルが正常に接続されると、Cloudflare Dashboard でトンネルのステータスが「Healthy」になります。

### メリット

- ポートを公開する必要がない（セキュリティ向上）
- DDoS 保護が自動で有効
- SSL 証明書が自動で管理される
- 無料プランで利用可能

---

## 方法 2: 通常の DNS 設定 + Cloudflare プロキシ

既存のサーバーに IP アドレスがある場合、Cloudflare の DNS プロキシ機能を使用できます。

### 前提条件

- サーバーのパブリック IP アドレス
- ドメインが Cloudflare で管理されていること
- サーバーでポート 80 と 443 が公開されていること

### セットアップ手順

#### 1. DNS 設定

1. Cloudflare Dashboard → ドメインを選択
2. 「DNS」→「Records」を選択
3. 以下の A レコードを追加：
   - **Type**: A
   - **Name**: `@`（またはサブドメイン）
   - **IPv4 address**: サーバーの IP アドレス
   - **Proxy status**: プロキシ済み（オレンジの雲アイコン）
   - **TTL**: Auto

#### 2. SSL/TLS 設定

1. Cloudflare Dashboard → 「SSL/TLS」を選択
2. 「Overview」で「Full (strict)」を選択
3. 「Edge Certificates」で「Always Use HTTPS」を有効化

#### 3. nginx 設定の更新

Cloudflare 経由でアクセスされる場合、実際のクライアント IP を取得するために nginx 設定を更新する必要があります。

`docker-compose.yml`で nginx 設定を変更：

```yaml
nginx:
  volumes:
    - ../../public:/usr/share/nginx/html:ro
    - ./nginx/default.conf.cloudflare:/etc/nginx/conf.d/default.conf:ro # 変更
    - ./nginx/ssl:/etc/nginx/ssl:ro
```

または、`default.conf`を直接編集して Cloudflare 用の設定を追加することもできます。

#### 4. 環境変数の設定

`back/api/.env`を更新：

```env
# GitHub OAuth（本番環境用）
GITHUB_REDIRECT_URI=https://yourdomain.com/api/v1/auth/github/callback

# CORS設定（本番環境用）
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# アプリケーション環境
APP_ENV=production
```

#### 5. GitHub OAuth 設定の更新

1. GitHub Settings > Developer settings > OAuth Apps
2. 既存のアプリを編集、または新しいアプリを作成
3. Authorization callback URL: `https://yourdomain.com/api/v1/auth/github/callback`

#### 6. ファイアウォール設定

サーバーのファイアウォールで以下のポートを開放：

- **ポート 80（HTTP）**: Cloudflare からのみアクセス可能にすることを推奨
- **ポート 443（HTTPS）**: Cloudflare からのみアクセス可能にすることを推奨

Cloudflare の IP レンジを許可する設定例（iptables）:

```bash
# CloudflareのIPv4レンジを許可
# 最新のIPレンジは https://www.cloudflare.com/ips/ を参照
```

#### 7. 起動

```bash
cd back/infra
docker compose up -d
```

### メリット

- 既存のサーバー設定をそのまま活用できる
- Cloudflare の CDN 機能を利用できる
- DDoS 保護が有効

### 注意事項

- サーバーの IP アドレスが公開される
- ファイアウォール設定が必要
- SSL 証明書の管理が必要（Let's Encrypt など）

---

## 共通の設定

### WebSocket 設定

Cloudflare 経由で WebSocket を使用する場合、追加設定が必要な場合があります。

1. Cloudflare Dashboard → 「Network」
2. 「WebSockets」を有効化

### キャッシュ設定

静的ファイルのキャッシュを最適化：

1. Cloudflare Dashboard → 「Caching」→「Configuration」
2. 「Browser Cache TTL」を設定
3. 「Page Rules」で静的ファイルのキャッシュルールを追加

### セキュリティ設定

1. Cloudflare Dashboard → 「Security」
2. 「WAF」でセキュリティルールを設定
3. 「Rate Limiting」でレート制限を設定（有料プラン）

---

## トラブルシューティング

### Cloudflare Tunnel が接続できない

- トークンが正しいか確認
- コンテナのログを確認: `docker compose logs cloudflared`
- Cloudflare Dashboard でトンネルのステータスを確認

### WebSocket が接続できない

- Cloudflare Dashboard で WebSocket が有効になっているか確認
- nginx 設定で WebSocket プロキシが正しく設定されているか確認

### CORS エラー

- `CORS_ORIGINS`に正しいドメインが設定されているか確認
- プロトコル（http/https）が一致しているか確認

### GitHub OAuth が動作しない

- Callback URL が正確に一致しているか確認
- GitHub OAuth アプリの設定を確認
- ブラウザのコンソールでエラーメッセージを確認

---

## 参考リンク

- [Cloudflare Tunnel ドキュメント](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflare DNS 設定](https://developers.cloudflare.com/dns/)
- [Cloudflare SSL/TLS 設定](https://developers.cloudflare.com/ssl/)
