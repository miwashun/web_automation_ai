# コンポーネント図

```mermaid
flowchart LR
  subgraph CLI
    A[app.py]
  end

  subgraph Security
    B[auth.py<br/>TOTP/JWT]
    C[policy.py<br/>権限制御]
  end

  subgraph Runner
    D[steps.py<br/>DSL実行制御]
    E[browser.py<br/>Playwright操作]
  end

  subgraph IO
    F[secrets.py<br/>シークレット管理]
    G[storage.py<br/>S3/FS保存]
    H[audit.py<br/>JSONL監査ログ]
  end

  A --> B
  A --> C
  A --> D
  D --> E
  D --> F
  D --> G
  D --> H

  %% 将来拡張（必要時に有効化）
  %% subgraph UI
  %%   I[webui.py<br/>FastAPI/HTMX]
  %% end
  %% A --> I

  %% subgraph API
  %%   J[api_gateway<br/>OIDC/mTLS]
  %% end
  %% I --> J
