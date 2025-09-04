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
- `confirm_plan(summary?)` — **実行前確認（必須）**
- `goto(url)` / `fill(selector,text,mask?)` / `click(selector)` / `wait(for,timeout)`
- `wait_for(selector?,state?,timeout?)` — 要素の出現/消失/有効化まで待機
- `solve_2fa(provider, ...)` — email / TOTP / SMS / push（将来）
- `totp(secret,algo?,digits?,period?,skew?)` — TOTPコード生成（`set_var`併用を想定）
- `set_var(name,value)` — 実行時変数の設定（テンプレ対応）
- `extract(selector,attr?,regex?,as?)` — 画面から値を抽出し変数に格納
- `assert(left,op,right,message?)` — 値/DOMの検証。`op`: eq/ne/contains/matches/gt/gte/lt/lte/exists
- `foreach(listVar,item,varIndex?,steps)` — 配列に対する反復実行
- `retry(steps,max_attempts,backoff_ms?)` — 一連の`steps`を再試行
- `timeout(ms,steps)` — 指定時間内に`steps`が完了するか検証
- `screenshot(target?,path?,fullpage?,record?)` — スクショ保存（証跡）
- `wait_download(pattern,to)` — ダウンロード監視 & 保存先指定
- `save_artifact(path,kind?,meta?)` — 生成物を成果物として登録
- `upload_file(selector,path)` — `<input type=file>` へのアップロード
- `cookies(set?[],clear?[])` / `headers(set?{},clear?[])` — セッション調整
- `eval_js(expression,as?)` — ページコンテキストでJS評価し変数に格納
- `verify_file(hash,record)` — ハッシュ計算 & 監査記録

## 4.3 confirm_plan の導入
- LLMの誤操作を防ぐため、実行前に人間の承認を必須化。
- 例：`{"act":"confirm_plan","summary":"ログイン→レポート→売上_YYYYMM.csv ダウンロード"}`

## 4.4 検証
- **jsonschema** による構文検証
- セレクタの疎通チェック（オフラインDOM/モックで事前検証）

## 4.5 追加アクション仕様

### 4.5.1 wait_for
- 目的: 要素や状態の安定化を待つユーティリティ。
- フィールド:
  - `selector` (string, optional): 対象。省略時はネットワーク/ロード状態のみを待機。
  - `state` (string, default: `visible`): `attached` | `detached` | `visible` | `hidden` | `enabled` | `disabled` | `stable`。
  - `timeout` (int, ms, default: 10000)
- 例:
```json
{"act":"wait_for","selector":"#result","state":"visible","timeout":15000}
```

### 4.5.2 set_var
- 目的: 実行中に変数を定義/上書き。
- 例:
```json
{"act":"set_var","name":"year","value":"{{yyyy}}"}
```

### 4.5.3 extract
- 目的: DOM/属性/正規表現から値を取り出し、変数に保存。
- フィールド: `selector`, `attr`(text|value|href|src|任意属性), `regex`(optional), `as`(保存名)
- 例:
```json
{"act":"extract","selector":".price","regex":"([0-9,]+)","as":"price"}
```

### 4.5.4 assert
- 目的: 値の検証。失敗時は`on_fail`方針に従う。
- フィールド: `left`, `op`, `right`, `message?`
- `op`: `eq`|`ne`|`contains`|`matches`|`gt`|`gte`|`lt`|`lte`|`exists`
- 例:
```json
{"act":"assert","left":"{{price}}","op":"matches","right":"^[0-9,]+$","message":"価格形式が不正"}
```

### 4.5.5 foreach
- 目的: 配列に対してサブステップを繰り返し実行。
- フィールド: `listVar`, `item`, `varIndex?`, `steps[]`
- 例:
```json
{
  "act":"foreach",
  "listVar":"reports",
  "item":"rep",
  "steps":[
    {"act":"goto","url":"https://example.com/{{rep.path}}"},
    {"act":"wait_for","selector":"#ready"}
  ]
}
```

### 4.5.6 retry
- 目的: 一時的失敗に対する再試行ブロック。
- フィールド: `steps[]`, `max_attempts`(>=1), `backoff_ms?`(指数/固定は実装依存)
- 例:
```json
{"act":"retry","max_attempts":3,"backoff_ms":1000,
 "steps":[{"act":"click","selector":"text=ダウンロード"},{"act":"wait_download","pattern":"*.csv","to":"./dl/"}]}
```

### 4.5.7 timeout
- 目的: ブロックの総時間上限を設定。
- フィールド: `ms`, `steps[]`
- 例:
```json
{"act":"timeout","ms":20000,"steps":[{"act":"wait_for","selector":"#done"}]}
```

### 4.5.8 screenshot
- 目的: 証跡/デバッグ用スクショ。
- フィールド: `target?`(fullpage|viewport|selector), `path?`, `fullpage?`, `record?`(監査記録に添付)
- 例:
```json
{"act":"screenshot","target":"selector","path":"artifacts/login.png","record":true}
```

### 4.5.9 save_artifact
- 目的: 生成物(ファイル/テキスト)の明示的登録。
- フィールド: `path`, `kind?`(file|text|image), `meta?`(任意キー)
- 例:
```json
{"act":"save_artifact","path":"./reports/売上_{{yyyy}}{{mm}}.csv","kind":"file","meta":{"site":"example"}}
```

### 4.5.10 upload_file
- 目的: `<input type=file>` へのファイル指定。
- フィールド: `selector`, `path`
- 例:
```json
{"act":"upload_file","selector":"input[type=file]","path":"./data/import.csv"}
```

### 4.5.11 cookies / headers
- 目的: セッションやリクエストヘッダの調整。
- 例:
```json
{"act":"cookies","set":[{"name":"locale","value":"ja-JP","domain":"example.com"}]}
{"act":"headers","set":{"X-Requested-With":"fetch"}}
```

### 4.5.12 eval_js
- 目的: ページ内でJS式を評価し結果を変数に格納。
- フィールド: `expression`, `as`
- 例:
```json
{"act":"eval_js","expression":"document.title","as":"title"}
```

### 4.5.13 totp / solve_2fa(email)
- `totp`はコードを生成して`set_var`で`{{totp_code}}`などに格納して`fill`で使用。
- `solve_2fa`(email) の追加フィールド: `inbox`(IMAP/POP接続文字列), `filter`, `subject_regex?`, `body_regex?`, `timeout`。

---

## 4.6 変数とテンプレート
- 形式: `{{var}}`。組込: `{{yyyy}}`, `{{mm}}`, `{{dd}}`, `{{hh}}`, `{{mi}}`, `{{ss}}`
- 名前空間例: `secrets.*`, `env.*`, `run.*`（実行ID等）, `extract.*`
- フォールバック: `{{var | default("N/A")}}`
- 文字列結合: `{{year}}{{mm}}` / `{{join(list, ',')}}`

## 4.7 エラーハンドリング
- すべてのアクションは任意に `on_fail` を受け付ける。
  - `on_fail`: `abort`(既定) | `continue` | `retry:n` | `screenshot:path` (複合指定は配列)
- 例:
```json
{"act":"click","selector":"#submit","on_fail":["screenshot:artifacts/err.png","retry:2"]}
```

## 4.8 セキュリティ/監査ガイド
- `mask:true` はログ/監査上で値を秘匿。
- `record:true` は監査トレイルへ添付（ハッシュ化して保存）。
- シークレットは `{{secrets.<scope>.<KEY>}}` 参照のみ。平文直書き禁止。

## 4.9 JSON Schema 断片（実装指針）
> 実装は `jsonschema` ベース。以下は主要アクションの最小スキーマ例。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["version","site","steps"],
  "properties": {
    "version": {"type":"string"},
    "site": {"type":"string"},
    "steps": {
      "type":"array",
      "items": {"$ref":"#/defs/Step"}
    }
  },
  "defs": {
    "Step": {
      "type":"object",
      "required":["act"],
      "properties":{
        "act":{"type":"string"}
      },
      "oneOf":[
        {"properties":{"act":{"const":"goto"},"url":{"type":"string"}},"required":["url"]},
        {"properties":{"act":{"const":"fill"},"selector":{"type":"string"},"text":{"type":"string"},"mask":{"type":"boolean"}},"required":["selector","text"]},
        {"properties":{"act":{"const":"click"},"selector":{"type":"string"}},"required":["selector"]},
        {"properties":{"act":{"const":"wait_for"},"selector":{"type":"string"},"state":{"enum":["attached","detached","visible","hidden","enabled","disabled","stable"]},"timeout":{"type":"integer"}}},
        {"properties":{"act":{"const":"extract"},"selector":{"type":"string"},"attr":{"type":"string"},"regex":{"type":"string"},"as":{"type":"string"}},"required":["selector","as"]},
        {"properties":{"act":{"const":"assert"},"left":{},"op":{"enum":["eq","ne","contains","matches","gt","gte","lt","lte","exists"]},"right":{}},"required":["left","op"]},
        {"properties":{"act":{"const":"screenshot"},"target":{"enum":["fullpage","viewport","selector"]},"path":{"type":"string"},"record":{"type":"boolean"}}}
      ]
    }
  }
}
```
