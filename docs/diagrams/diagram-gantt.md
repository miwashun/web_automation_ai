```mermaid

gantt
  title Web自動操作AI 開発WBS
  dateFormat  YYYY-MM-DD
  section 設計
    要件レビュー :a1, 2025-09-01, 3d
    アーキテクチャ確定 :a2, after a1, 4d
  section 実装
    CLI MVP実装 :b1, after a2, 10d
    Playwright連携 :b2, after b1, 7d
  section テスト
    単体テスト :c1, after b2, 5d
    E2Eテスト :c2, after c1, 5d
  section リリース
    GitHub Actions整備 :d1, after c2, 3d
    MVPリリース :d2, after d1, 1d
