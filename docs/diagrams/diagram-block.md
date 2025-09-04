# ブロック図（Block Diagram）


本プロジェクトの主要コンポーネントを層（レイヤ）で俯瞰し、データ/制御の流れを示します。
下図は **個人利用（Phase A: CLI）** を前提にした最小構成です。

```mermaid
flowchart TD
    subgraph User["ユーザー"]
        A1["自然言語の指示"]
        A2["本人認証 (TOTP/WebAuthn)"]
    end

    subgraph Agent["LLMエージェント層"]
        B1["指示解析"]
        B2["操作計画(DSL/JSON)生成"]
    end

    subgraph Runner["実行エンジン"]
        C1["DSL検証 (jsonschema)"]
        C2["ブラウザ操作<br>(Playwright/Puppeteer)"]
        C3["2FA処理 (メール/SMS/TOTP)"]
        C4["ダウンロード完了検知"]
    end

    subgraph Infra["ストレージ/運用基盤"]
        D1["成果物保存<br>(S3/FS 暗号化)"]
        D2["監査ログ<br>(JSONL + ハッシュチェーン)"]
        D3["ジョブ/キュー<br>(Celery/Temporal)"]
    end

    subgraph Security["セキュリティ/アクセス制御"]
        E1["Vault/KMS 秘密管理"]
        E2["ポリシー制御 (OPA/Casbin)"]
        E3["監査証跡 (不可否認性)"]
    end

    A1 -->|指示送信| B1 --> B2
    A2 -->|JWT発行| Runner
    B2 -->|DSL渡し| C1 --> C2
    C2 --> C3 --> C4
    C4 -->|成果物| D1
    C4 -->|ログ| D2
    Runner --> D3
    D1 & D2 --> Security
