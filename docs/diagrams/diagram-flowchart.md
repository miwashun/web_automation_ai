```mermaid
flowchart TD
    A[web_automation_ai/] --> B[docs/]
    A --> C[src/]
    A --> D[tests/]
    A --> E[.github/]
    A --> F[README.md]

    B --> B1[README.md]
    B --> B2[10-requirements.md]
    B --> B3[20-architecture.md]
    B --> B4[30-dsl-spec.md]
    B --> B5[40-security-secrets.md]
    B --> B6[50-operations.md]
    B --> B7[60-roadmap.md]
    B --> B8[70-site-profiles/]
    B --> B9[80-team-playbook.md]
    B --> B10[90-compliance.md]
    B --> B11[kpi-dashboard.md]
    B8 --> B8a[TEMPLATE.md]

    C[アプリケーションコード]
    D[テストコード]
    E[CI/CDワークフロー]
