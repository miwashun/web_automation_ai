# Contributing Guide

このプロジェクトに貢献いただきありがとうございます。以下のガイドラインに従って開発・コミットをお願いします。

---

## 🛠️ 開発環境のセットアップ

1. リポジトリをクローン:
   ```bash
   git clone https://github.com/<your-org>/web_automation_ai.git
   cd web_automation_ai
   ```

2. 仮想環境を作成して依存関係をインストール:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. 開発ツール（pre-commit / black / flake8 / mypy）をインストール:
   ```bash
   pip install pre-commit black flake8 mypy
   ```

4. pre-commit フックをセットアップ:
   ```bash
   pre-commit install               # 通常フック
   pre-commit install --hook-type commit-msg  # コミットメッセージ検査
   ```

> ※ 既存の `.pre-commit-config.yaml` を最新化してください（後述のサンプルを参照）。

---

## ✍️ コミットメッセージ規約（Conventional Commits）

本プロジェクトでは **[Conventional Commits](https://www.conventionalcommits.org/ja/v1.0.0/)** を採用しています。  
コミットメッセージは以下の形式で記述してください:

```
<type>(<scope>): <subject>
```

- **type**: feat | fix | docs | style | refactor | perf | test | build | ci | chore | revert
- **scope**: 任意（例: cli, runner, dsl, playwright, auth, storage, audit, docs）
- **subject**: 72文字以内、文末に句点を付けない、命令形

### ✅ 例
```
feat(cli): add headless option to run command
fix(playwright): increase timeout for login button
docs(operations): add log rotation policy
refactor(runner): extract step executor class
ci: enable python 3.12 in test matrix
```

### 🚨 Breaking Change
```
feat(dsl): rename "wait_ms" to "wait" for consistency

BREAKING CHANGE: "wait_ms" field is removed in favor of "wait".
```

---

## 🔍 コード規約と静的解析

- Python: PEP8 に準拠
- YAML: yamllint に従う（`.egg-info/` は lint 対象外）
- Secrets: `.env` / 認証情報は絶対にコミットしない（詳細は `docs/40-security-secrets.md` を参照）

### ローカルでのチェック例
```bash
# 自動整形
black .

# Lint
flake8 .

# 型チェック（pyproject.toml や mypy.ini があればそれに従います）
mypy .
```

---

## 🔄 Pull Request の流れ

1. ブランチ作成:
   ```bash
   git checkout -b feat/cli-headless
   ```

2. テスト・静的解析を実行:
   ```bash
   pytest          # （テストがある場合）
   black .
   flake8 .
   mypy .
   ```

3. Conventional Commits 形式でコミット:
   ```bash
   git commit -m "feat(cli): add headless option"
   ```

4. プッシュして Pull Request 作成:
   ```bash
   git push origin feat/cli-headless
   ```

- PR タイトルも Conventional Commits 準拠にしてください。
- CI が通っていることを確認してください。

---

## ⚙️ .pre-commit-config.yaml（サンプル）

> 既存の yamllint に加えて、**Conventional Commits / black / flake8 / mypy** を追加した例です。

```yaml
repos:
  # YAML の静的検査
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.35.1
    hooks:
      - id: yamllint
        exclude: |
          (^src/wao\.egg-info/)|(\.egg-info/)

  # コミットメッセージ: Conventional Commits を強制（commit-msg フック）
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.2.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args:
          - --types=feat,fix,docs,style,refactor,perf,test,build,ci,chore,revert
          - --max-subject-length=72
          - --subject-conventional=true

  # Python 自動整形
  - repo: https://github.com/psf/black
    rev: 24.8.0
    hooks:
      - id: black
        language_version: python3.12

  # Python Lint
  - repo: https://github.com/pycqa/flake8
    rev: 7.1.0
    hooks:
      - id: flake8

  # 型チェック
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
```

---

## 📊 参考資料

- Conventional Commits: https://www.conventionalcommits.org/ja/v1.0.0/
- Python Black: https://black.readthedocs.io/
- Flake8: https://flake8.pycqa.org/
- Mypy: https://mypy.readthedocs.io/
