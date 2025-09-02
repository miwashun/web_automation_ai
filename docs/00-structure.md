# プロジェクト構成

本プロジェクトのディレクトリ構成は以下の通りです。

```text
web_automatic_operation_ai/
├── README.md
├── LICENSE
├── .gitignore
├── .editorconfig
├── .pre-commit-config.yaml
├── pyproject.toml
├── requirements.txt
├── setup.py
├── .env.example
├── CODEOWNERS
├── CONTRIBUTING.md         # 開発者ガイド
├── justfile                # コマンド簡易化 (or Makefile)
├── docs/
│   ├── 00-structure.md     # 本ファイル: ディレクトリ構成
│   ├── 10-requirements.md
│   ├── 20-architecture.md
│   ├── 30-dsl-spec.md
│   ├── 40-security-secrets.md  # .env変数一覧テーブル追加
│   ├── 50-operations.md    # ログローテーション設計追記
│   ├── 60-roadmap.md
│   ├── 80-team-playbook.md
│   ├── 90-compliance.md
│   └── adr/
│       └── TEMPLATE.md
├── site_profiles/
│   ├── TEMPLATE.md
│   ├── example.com.md
│   └── mytokyogas.md
├── src/                    # バックエンド (Python)
│   ├── __init__.py
│   ├── main.py             # CLIエントリポイント
│   ├── agent/
│   │   └── plan_generator.py
│   ├── engine/
│   │   ├── browser.py
│   │   └── dsl_executor.py
│   ├── tools/
│   │   ├── twofa.py
│   │   ├── storage.py
│   │   └── verify.py
│   ├── security/
│   │   ├── auth.py
│   │   └── policy.py
│   ├── utils/
│   │   └── logger.py
│   └── api/                # FastAPI/Flask (Web UIバックエンド部分)
│       ├── __init__.py
│       ├── app.py          # FastAPIメインアプリ
│       └── routes/         # エンドポイント定義
├── frontend/               # Next.js
│   ├── package.json        # Node.js依存管理
│   ├── next.config.js      # Next.js設定 (Next.jsの場合)
│   ├── src/                # フロントエンドソース
│   │   ├── pages/          # Next.jsページ (or app/ for App Router)
│   │   ├── components/     # UIコンポーネント
│   │   ├── styles/         # CSS/SCSS
│   │   └── utils/          # フロントユーティリティ (APIコールなど)
│   ├── public/             # 静的アセット (画像など)
│   └── tests/              # フロントエンドテスト (Jestなど)
├── tests/                  # バックエンドテスト
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── conftest.py
├── scripts/
│   ├── cron_runner.py
│   └── rotate_logs.py      # ログローテーション
├── .github/
│   ├── workflows/
│   │   └── ci.yml
│   ├── pull_request_template.md
│   └── ISSUE_TEMPLATE/
├── logs/                   # .gitignoreで無視
├── artifacts/              # .gitignoreで無視
└── infra/                  # 空 (将来用: Terraformなど)
