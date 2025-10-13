# 20. システム構成と実装方針

## 2. システム構成（MVP〜SaaS）
- **LLMエージェント層**：自然言語→操作計画（DSL/JSON）変換
- **実行エンジン**：Playwright or Puppeteer（ヘッドレス/有）
- **ツール群**：Captcha対策、OTP取得、S3クライアント、解凍、ハッシュ計算
- **ジョブ/キュー**：Celery/Temporal/BullMQ
- **記録**：OpenTelemetry + 構造化ログ（JSONL）
- **保管**：S3/MinIO + バージョニング
- **鍵管理**：環境変数 + Vault/KMS

### 最小構成（個人〜小規模向け）
- Python + Playwright
- SQLite/JSONL ログ
- .env + 1Password/Vault
- Cron/CLI 実行

## 11. 運用形態と実装方針（段階導入）
### Phase A：CLI（ローカル）
- 対象：個人利用。UI不要で最短到達。
- 認証：TOTP → 短寿命JWT（5〜10分、scope=run:<site>:download）
- 成果物：`~/WebAuto/<user_id>/...` または `s3://bucket/users/<user_id>/...`
- 監査：JSONL + ハッシュチェーン（PIIレダクション後保存、**暗号化必須**）

### Phase B：軽量Web UI
- WebAuthn/Passkey + OIDC、承認は再認証付き
- FastAPI/Flask + HTMX or Next.js、OPA/Casbinでポリシー

### Phase C：API Gateway（SaaS土台）
- OIDC + API Gateway（Kong/Envoy/APISIX）、mTLS可
- ジョブキュー（Celery/Temporal）+ テナント分離（DB/RLS、S3名前空間）

## 11.2 最低限の技術選定（CLI版）
- Python 3.11+ / Playwright（ヘッドレス、accept_downloads=True）
- `dotenv`（→ 後に Vault/KMS へ差し替え可能）
- `pyotp` + `python-jose|authlib`（短寿命JWT）
- `structlog`（JSONL）+ ハッシュチェーン + **保存時暗号化**
- ローカルFS / S3（boto3、KMS暗号化）
- ポリシー：最初はYAML（allow/deny）→将来OPA/Casbin

## 11.3 Walking Skeleton（骨格）
1. login：TOTP検証 → run_token発行（exp=600、aud=automation-run、scope適用）
2. run：run_token検証 → DSL `steps` を最小実行
3. ダウンロード：ファイル名マッチ & ハッシュ → 保存 → 監査ログ
4. 失敗時：スクショ/HTML保存（レダクション）+ 構造化エラー

## 11.4 ガードレール
- I/O・秘密・ポリシー・ブラウザ実行を**インターフェース越し**に呼ぶ（DI）
- `.env` アクセスは1箇所へ集約（将来Vault差し替え）
- DSLは **jsonschema** で検証（CI）。Breaking changeはバージョンアップ。
- 監査ログは**常に**出力（成功/失敗/閲覧）。TTL削除。**暗号化は強制**。

## 11.5 ミニADRテンプレ
- **Context**：背景・制約
- **Decision**：採用/不採用・理由
- **Consequences**：トレードオフ・見直し条件

## 12. デザインパターン方針
設計の一貫性と拡張容易性を確保するため、主要レイヤごとの設計パターンを整理しています。
詳細は次を参照してください：

➡️ [Design Patterns Policy for `web_automation_ai` (v0.1)](./design-patterns-policy.md)
