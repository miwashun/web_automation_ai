# 40. セキュリティ & シークレット管理

## 5.1 .env サンプル
```
EXAMPLE_USER=...
EXAMPLE_PASS=...
IMAP_HOST=...
IMAP_USER=...
IMAP_PASS=...
S3_ENDPOINT=...
S3_KEY=...
S3_SECRET=...
```

## 5.2 原則
- 機密はLLMに直接渡さない（エージェント→実行エンジンでトークン参照）
- 実行エンジン側で解決（secret provider abstraction）
- 最小権限（スコープ最小/TTL短命）

## 5.3 暗号化
- **at-rest**：成果物/ログ/Site Profileの機微情報は **SSE-KMSまたはAES-256**。ローカルはOS暗号化+ファイル鍵。
- **in-transit**：全通信 **TLS1.2+**（S3/DB/IMAP含む）。可能ならmTLS。
- **鍵ローテーション**：KMSキーは **90〜180日** ローテ。撤回時は即時失効。

## 10. 指示者確認とアクセス制御（抜粋）
1. **本人認証**：WebAuthnまたはTOTP必須。短寿命JWT（5〜10分）。
2. **実行権限**：ポリシーエンジン（OPA等）で最小スコープ付与。`scope: ["run:site:download"]`
3. **成果物/ログの分離**：ユーザー専用名前空間、署名URLは短寿命、PIIレダクション、**保存データは暗号化必須**。
4. **承認フロー**：新規サイト・初回DL・高感度カテゴリはワンタイム承認（再認証付き）。
5. **監査**：ハッシュチェーン署名、who/when/what/resultを記録。
