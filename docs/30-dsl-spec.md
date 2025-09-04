# 30. アクションDSL 仕様

## 4.1 サンプル
```json
{
  "version": "1.0",
  "site": "example.com",
  "steps": [
    {"act":"goto","url":"https://example.com/login"},
    {"act":"fill","selector":"#username","text":"{{secrets.example.USER}}"},
    {"act":"fill","selector":"#password","text":"{{secrets.example.PASS}}","mask":true},
    {"act":"click","selector":"button[type=submit]"},
    {"act":"wait","for":"network-idle","timeout":15000},
    {"act":"solve_2fa","provider":"email","inbox":"{{secrets.shared.IMAP}}","filter":"From: no-reply@example"},
    {"act":"goto","url":"https://example.com/reports"},
    {"act":"click","selector":"text=月次CSV"},
    {"act":"wait_download","pattern":"売上_{{yyyy}}{{mm}}.csv","to":"s3://bucket/reports/"},
    {"act":"verify_file","hash":"sha256","record":true}
  ]
}
```

## 4.2 アクション一覧（抜粋）
- `goto(url)` / `fill(selector,text,mask?)` / `click(selector)` / `wait(for,timeout)`
- `solve_2fa(provider, ...)` — email / TOTP / SMS / push（将来）
- `wait_download(pattern,to)` — ダウンロード監視 & 保存先指定
- `verify_file(hash,record)` — ハッシュ計算 & 監査記録
- `confirm_plan(summary?)` — **実行前確認（必須）**

## 4.3 confirm_plan の導入
- LLMの誤操作を防ぐため、実行前に人間の承認を必須化。
- 例：`{"act":"confirm_plan","summary":"ログイン→レポート→売上_YYYYMM.csv ダウンロード"}`

## 4.4 検証
- **jsonschema** による構文検証
- セレクタの疎通チェック（オフラインDOM/モックで事前検証）
