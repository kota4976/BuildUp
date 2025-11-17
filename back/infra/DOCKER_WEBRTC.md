# Docker 環境での WebRTC 通話機能の使用方法

## 概要

WebRTC はセキュリティ上の理由から、以下の環境でのみ動作します：

- **HTTPS 接続**（推奨）
- **localhost** または **127.0.0.1** での HTTP 接続（開発環境のみ）

## セットアップ方法

### 方法 1: HTTPS を使用（推奨、本番環境に近い）

#### 1. SSL 証明書の生成

```bash
cd back/infra
./nginx/generate-ssl.sh
```

これにより、`nginx/ssl/` ディレクトリに自己署名証明書が生成されます。

#### 2. Docker Compose で起動

```bash
cd back/infra
docker-compose up -d
```

#### 3. ブラウザでアクセス

- **URL**: `https://localhost` または `https://127.0.0.1`
- **注意**: 自己署名証明書のため、ブラウザで警告が表示されます
  - Chrome/Edge: 「詳細設定」→「localhost にアクセスする（安全ではありません）」
  - Firefox: 「詳細情報」→「リスクを承知で続行」
  - Safari: 「詳細」→「この Web サイトにアクセス」

### 方法 2: HTTP を使用（開発環境のみ、localhost 限定）

#### 1. docker-compose.yml の修正

`docker-compose.yml`の nginx サービスの volumes セクションを以下のように変更：

```yaml
nginx:
  volumes:
    - ../../public:/usr/share/nginx/html:ro
    - ./nginx/default.conf.dev:/etc/nginx/conf.d/default.conf:ro # .devを使用
```

#### 2. Docker Compose で起動

```bash
cd back/infra
docker-compose up -d
```

#### 3. ブラウザでアクセス

- **URL**: `http://localhost` または `http://127.0.0.1`
- **重要**: IP アドレス（例：`http://192.168.x.x`）では動作しません

## トラブルシューティング

### WebRTC が動作しない場合

1. **HTTPS を使用しているか確認**

   - ブラウザのアドレスバーで `https://` になっているか確認
   - 自己署名証明書の警告を承認しているか確認

2. **localhost でアクセスしているか確認**

   - HTTP を使用する場合、`localhost` または `127.0.0.1` のみで動作します
   - IP アドレス経由のアクセスでは HTTPS が必要です

3. **ブラウザのコンソールを確認**

   - F12 キーで開発者ツールを開く
   - Console タブでエラーメッセージを確認
   - Network タブで WebSocket 接続を確認

4. **カメラ/マイクの許可**
   - ブラウザでカメラとマイクへのアクセスを許可してください
   - ブラウザの設定でサイトの権限を確認

### WebSocket 接続エラー

1. **nginx のログを確認**

   ```bash
   docker-compose logs nginx
   ```

2. **API のログを確認**

   ```bash
   docker-compose logs api
   ```

3. **WebSocket パスの確認**
   - ブラウザの開発者ツール → Network タブ → WS フィルタ
   - `/ws/chat` または `/ws/group-chat` への接続を確認

### 証明書エラー

自己署名証明書を使用している場合、ブラウザで警告が表示されます。これは正常な動作です。

**本番環境では**、Let's Encrypt などの正式な証明書を使用してください。

## 本番環境での設定

本番環境では、以下の設定を推奨します：

1. **正式な SSL 証明書の使用**

   - Let's Encrypt（無料）
   - 商用 SSL 証明書

2. **HTTPS の強制**

   - HTTP から HTTPS へのリダイレクト（既に実装済み）

3. **セキュリティヘッダーの追加**
   - HSTS（HTTP Strict Transport Security）
   - Content Security Policy

## 参考情報

- [WebRTC Security](https://webrtc.org/getting-started/overview)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Let's Encrypt](https://letsencrypt.org/)
