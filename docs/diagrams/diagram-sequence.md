```mermaid
sequenceDiagram
  autonumber

  %% ===== グルーピング（役割別カラー） =====
  box rgba(56,189,248,0.15) ユーザ領域
    actor User as ユーザー
  end

  box rgba(167,243,208,0.20) 内部システム（実行側）
    participant CLI as CLI(app.py)
    participant Auth as Auth(TOTP/JWT)
    participant Runner as Runner(steps)
    participant PW as Playwright
  end

  box rgba(251,191,36,0.20) 外部サイト
    participant Site as Target Site
  end

  box rgba(196,181,253,0.20) ストレージ/監査
    participant Store as Storage(S3/FS)
    participant Audit as Audit(JSONL)
  end

  %% ===== フロー開始 =====
  User->>CLI: run example.json
  Note right of User: 操作計画(DSL/JSON)を指定して実行

  %% === 実行者認証 ===
  CLI->>Auth: verify TOTP → issue run_token(JWT)
  Note right of Auth: TOTP検証→短寿命JWT発行（aud=automation-run, exp≈10分）
  Auth-->>CLI: run_token

  %% === 実行前確認（confirm_plan） ===
  CLI->>Runner: load & validate DSL (jsonschema)
  Runner-->>CLI: proposed plan summary
  CLI-->>User: Show plan (site, steps, risk hints, est. time)

  alt ユーザーが承認
    User-->>CLI: confirm
    CLI->>Runner: proceed

    %% === ブラウザ操作 ===
    Runner->>PW: open browser (headless/有, accept_downloads)
    Note right of PW: Playwrightでブラウザを起動

    PW->>Site: GET /login (goto)
    Note right of Site: ログインページへ遷移

    Runner->>PW: fill(#user,#pass) + click(login) + wait(network-idle)
    PW->>Site: auth + navigate

    %% === ダウンロードと検証 ===
    Runner->>PW: trigger download
    alt ダウンロード成功
      PW-->>Runner: file path
      Runner->>Store: save(file, hash=sha256, enc=on)
      Note right of Store: S3/FSへ保存（KMS/OS暗号化, バージョニング可）
      Runner->>Audit: write step logs + file meta + hash chain
      Note right of Audit: JSONL構造化ログ + 改ざん防止（チェーン）
      Runner-->>CLI: result(success, path, hash)
      CLI-->>User: Done (path, sha256)
    else 失敗/エラー（UI変更, CAPTCHA, タイムアウト等）
      Note over Runner,PW: on_error ハンドラ発火
      Runner->>PW: capture screenshot()
      Runner->>PW: dump HTML (PII redaction)
      Runner->>Audit: write error logs + exception + evidence + hash link
      Note right of Audit: スクショ/HTMLはPIIマスク後に保存
      Runner-->>CLI: result(failure, reason, evidence_id)
      CLI-->>User: Failed (reason, how-to-retry, evidence link)
    end

  else ユーザーが却下/修正
    User-->>CLI: reject / edit
    CLI-->>User: Aborted (no action)
    Note over CLI,User: 承認されない限りブラウザ操作は実行しない
  end
