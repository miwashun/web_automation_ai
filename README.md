# Web Automatic Operation AI — CLI Skeleton

この最小構成は **DSL(JSON) を読み込み → スキーマ検証 → ダミー実行** までを行います。
Playwright等の実ブラウザ操作は未実装（TODO）です。

## 必要環境
- Python 3.10+（3.12 推奨）

## セットアップ
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 使い方
```bash
python app.py --run example.json
# もしくは
python -m wao.cli --run example.json
```

## 構成
```
.
├── app.py
├── requirements.txt
├── example.json
├── src/
│   └── wao/
│       ├── __init__.py
│       ├── cli.py
│       ├── logging_setup.py
│       ├── runner.py
│       ├── secrets.py
│       └── schema.json
└── tests/
    └── test_smoke.py
```

## 今後の拡張（TODO）
- Playwright連携（`runner.py` の TODO セクション）
- ステップの実行トレースをJSONLに出力
- .env連携（`secrets.py` をdotenv対応に）
- 失敗時のスクショ保存
