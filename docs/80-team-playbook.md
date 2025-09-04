# Team Playbook（小規模チーム用、最終更新版）

## 1. 役割と責務
- **Owner/PM**：スコープ・優先度決定、リリース承認
- **Tech Lead**：設計レビュー、品質ゲートの保守
- **Dev**：実装・テスト、PR作成
- **Reviewer**：PRレビュー、セキュリティ観点チェック
- **Ops（兼任可）**：CI/CD、リリース、障害対応

**備考（将来拡張）**
- Phase C（SaaS化）以降はチーム規模拡大に伴い、以下の専任ロールを追加検討：
  - 専任Ops（監視・インフラ運用）
  - セキュリティ担当（監査・脆弱性対応）
  - Site Profile Maintainer（対象サイトごとの専門担当）

---

## 2. ブランチ戦略
- **main**：常にデプロイ可能、保護設定（レビュー必須、CI必須）
- **feature/***: 課題単位（例：`feature/tokyogas-otp-sms`）
- **hotfix/***: 本番障害の緊急修正
- **タグ**：`vMAJOR.MINOR.PATCH`（例：`v0.3.1`）

---

## 3. コーディング規約（Python）
- **スタイル**：black + isort + flake8（pre-commitで強制）
- **型**：mypy（strict化は段階的）
- **Docstring**：Google style推奨
- **テスト**：pytest、カバレッジ閾値 80% → 安定後 90%
- **命名**：`snake_case`、モジュールは機能ごとに分割

**.editorconfig（抜粋）**
```ini
[*]
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2

[*.py]
indent_size = 4
```

**pre-commit（.pre-commit-config.yaml）**
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 25.1.0
    hooks: [{id: black}]
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks: [{id: isort}]
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks: [{id: flake8}]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks: [{id: mypy}]
# NOTE: Review tool versions every 6 months (Jan/Jul)
#       または 60-roadmap.md の Week 4 Go/No-Go タイミングで確認
```

---

## 4. コミット & PR
- **コミット規約**：Conventional Commits（例: `feat: (機能追加:) ...`、`fix: (修正:) ...`）
- **PR サイズ**：目安 400行以内、1PR=1目的
- **PRチェックリスト**
  - [ ] 目的・背景（WHY）が明確
  - [ ] 変更点（WHAT）と影響範囲
  - [ ] 動作確認ログ or スクショ
  - [ ] secrets/PII未露出
  - [ ] ドキュメント/ADR更新済み
  - [ ] ToS/API再確認
  - [ ] confirm_plan導入
  - [ ] 暗号化/SSE-KMS確認

**PRテンプレ（.github/pull_request_template.md）**
```markdown
## 背景 / WHY
-

## 変更点 / WHAT
-

## 動作確認
-

## セキュリティ・運用
- [ ] secrets未露出
- [ ] 監査ログOK
- [ ] ToS/API確認（該当時）
- [ ] confirm_plan導入済み
- [ ] 暗号化/SSE-KMS確認済み

## ドキュメント
- [ ] docs更新
- [ ] Site Profile更新
```

---

## 5. Issue運用
- **DoR（着手条件）**
  - [ ] 目的・成果物が明確
  - [ ] 受け入れ基準がある
  - [ ] ToS/API確認済み
- **DoD（完了条件）**
  - [ ] テスト通過（ユニット/E2E）
  - [ ] 構造化ログに必要情報（PIIマスク済み）
  - [ ] ドキュメント/ADR更新済み

**Issueテンプレ：Site Profile更新**
```markdown
### 背景
対象サイト：MyTokyoGas

### 変更内容
- ログインDOM変更（#password → input[name="pwd"]）

### やること
- [ ] セレクタ冗長化
- [ ] E2E成功率>=99%
- [ ] ToS/API再確認
- [ ] 監査ログハッシュ検証

### 受け入れ基準
- [ ] CSVを3分以内でDL
- [ ] S3保存（SSE-KMS有効）
```

---

## 6. 会議体
- **週次（30分）**：進捗・課題・KPI確認
- **リリース前レビュー（15分）**：mainマージ前の合意
- **障害ふりかえり（30分）**：原因・恒久対応・再発防止チェック

**障害レポート テンプレ**
```markdown
## 概要
発生時刻 / 検知方法 / 影響範囲

## 原因
直接原因 / 真因

## 対応
暫定対応 / 恒久対応 / オーナー / 期限

## 再発防止
- [ ] テスト追加
- [ ] アラート閾値調整
- [ ] ドキュメント更新
```

---

## 7. CI/CD最低ライン
- **CI**：`lint → typecheck → test → security-scan`
- **セキュリティ**：`bandit` / `pip-audit` / `gitleaks`
- **Artifacts**：CLIパッケージ or Docker image
- **CD**：タグ発行でPyPI/ghcrに配布（MVPは手動でOK）
- **追加**：E2Eテスト（PlaywrightでSite Profile検証）、LLMトークン使用量ログ化

---

## 8. セキュリティ・アクセス制御
- **最小権限**：リポジトリはWrite最小、`main`直push禁止
- **CODEOWNERS**：重要ディレクトリは必須レビュー
- **Secrets**：環境ごとに分離、ローテーション記録必須
- **監査**：閲覧/実行/ダウンロードをログ化（ハッシュチェーン）

---

## 9. ドキュメント運用
- **単一情報源**：`docs/`配下に集約
- **ADR**：Context/Decision/Consequences + Alternatives/Review条件を追記
- **README**：セットアップと最短動作確認を常に最新化

---

## 10. リリース運用
- **バージョニング**：SemVer（MAJOR.MINOR.PATCH）
- **CHANGELOG**：commitizenで自動生成
- **承認**：Owner/PMの確認後にタグ発行

---

## 11. オンボーディング
- [ ] NDA/利用規約確認（対象サイトのToS含む）
- [ ] 環境構築（Python/Playwright/`pre-commit install`）
- [ ] GitHub権限付与
- [ ] Secrets配布ポリシー確認
- [ ] 最初のGood First Issueを完了
- [ ] KPIダッシュボード/監査ログの見方を習得

---

## 12. 継続レビュー・改善
- **ツールバージョン**：半年ごとに更新レビュー（1月/7月）
  または 60-roadmap.md の Week 4 Go/No-Go で確認
- **Playbook**：半年ごとにチームレビュー（DoD適用）
- **KPIダッシュボード**：週次更新、10-requirements.mdの成功指標（成功率≥99%、実行時間≤3分、ゼロ漏えい、コスト上限、Site Profile更新MTTR）とリンク
- **改善Issue**：毎サイクルで「Playbook改善」Issueを立てる

