# Web Automatic Operation AI — CLI Skeleton

この最小構成は **DSL(JSON) を読み込み → スキーマ検証 → 実ブラウザ(Playwright)で実行** まで行います。
`flows/demo_example.json` がサンプルフローです。

## 必要環境
- Python 3.10+（3.13でも動作確認済）
- Playwright（自動インストール可）

## セットアップ
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install  # ← ブラウザ実体をダウンロード
```

## 使い方

### フロー実行
```bash
python app.py --run flows/demo_example.json
```

### スキーマ検証のみ
```bash
python app.py --run flows/demo_example.json --validate
```

### 実行ログ例
```
[INFO] 2025-10-25 17:59:30,565 wao.runner: Run started: site=- version=0.1.0
[INFO] 2025-10-25 17:59:30,565 wao.runner: Step 1: act=log
[INFO] 2025-10-25 17:59:30,565 wao.runner: Opening example.com
[INFO] 2025-10-25 17:59:31,192 wao.runner: Step 3: act=wait
[INFO] 2025-10-25 17:59:32,241 wao.runner: ✅ Flow completed successfully
[INFO] 2025-10-25 17:59:32,261 wao.runner: Run finished
```

### 成果物
- スクリーンショット例：`screenshots/example_basic.png`

## プロジェクト構成
```
.
├── app.py
├── flows/
│   ├── demo_example.json
│   ├── schema.flow.v1.json
│   └── ...
├── src/
│   └── wao/
│       ├── runner.py          # 実行本体 (Playwright連携済)
│       ├── validator.py       # JSON Schema 検証
│       ├── logging_setup.py   # ロガー設定
│       ├── secrets.py         # dotenv対応予定
│       └── ...
└── tests/
    └── test_smoke.py
```

## 今後の拡張（TODO）
- `wait_for_selector` / `wait_for_url` の追加
- ステップ単位のトレースログ(JSONL)出力
- `.env`連携（`secrets.py` をdotenv対応に）
- 失敗時スクリーンショット / HTML保存
- ダウンロードステップの正式実装
