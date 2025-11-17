#!/bin/bash
# 開発環境用の自己署名SSL証明書を生成するスクリプト

SSL_DIR="./nginx/ssl"
mkdir -p "$SSL_DIR"

# 証明書を生成
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/key.pem" \
    -out "$SSL_DIR/cert.pem" \
    -subj "/C=JP/ST=Tokyo/L=Tokyo/O=BuildUp/OU=Development/CN=localhost"

echo "SSL証明書が生成されました:"
echo "  - Certificate: $SSL_DIR/cert.pem"
echo "  - Private Key: $SSL_DIR/key.pem"
echo ""
echo "⚠️  これは開発環境用の自己署名証明書です。"
echo "   ブラウザで警告が表示されますが、[詳細設定] → [続行] で進んでください。"

