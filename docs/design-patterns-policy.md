Design Patterns Policy for web_automation_ai (v0.1)

このドキュメントは、web_automation_ai の主要レイヤに適用するデザインパターンの 推奨セットを明文化し、実装・レビュー・拡張の一貫性を高めるための基準を示します。

⸻

0. 目的と適用範囲
	•	目的: 拡張容易性、保守性、テスト容易性、責務分離を強化。
	•	適用範囲: DSLパーサ/バリデーション、Runner、Action実装、Logging/Observability、Config/Secrets、Browser抽象、エラー/リトライ制御。
	•	原則: 小さく始めて必要に応じて強化（YAGNI）、命名/責務/テストの三点セットを守る。

⸻

1. パターン一覧（レイヤ別）

1.1 Actions 層（wao.actions.*）
	•	必須: Command パターン
	•	各アクションは execute(ctx) を持つ コマンド。副作用は ctx に集約。
	•	効果: 追加・差し替えが容易、モック容易。
	•	推奨: Factory + Registry
	•	DSLの {"action": "click", ...} をアクション名→クラスに解決するレジストリ。
	•	効果: 新規アクションは 登録一行で利用可能。
	•	任意: Decorator（副作用追加）
	•	ログ、スクリーンショット、メトリクス、トレースをデコレータで付加。

1.2 Runner 層（wao.runner）
	•	推奨: Template Method
	•	run_flow() の骨格（前処理→実行→後処理→集計）をテンプレート化。
	•	推奨: Chain of Responsibility
	•	リトライ、タイムアウト、サーキットブレーカ、例外変換をチェーンで合成。
	•	任意: Strategy（スケジューリング/並列化）
	•	実行戦略（直列/並列/分割）を差し替え可能に。

1.3 DSL Parser / Validation（wao.dsl_parser, wao.validation）
	•	推奨: Builder
	•	フローの中間表現（IR）を段階的に構築。
	•	推奨: Factory
	•	バージョン別/方言別のパーサ実装を切替。
	•	任意: Specification
	•	バリデーションルールを再利用可能な仕様として合成。

1.4 Browser 抽象（Playwright/将来差替え）
	•	推奨: Strategy
	•	ブラウザ操作（click/type/wait 等）はインターフェースを固定し、実装（Playwright/他）を差替え。
	•	任意: Adapter
	•	ランタイムAPI差分を Adapter で吸収。

1.5 Config / Secrets（wao.config）
	•	推奨: Singleton（実装は DI で代替可）
	•	読み出しは不変（イミュータブル）とし、テストでは差替え可能に。

1.6 Observability（Logging / Screenshot / Metrics / Trace）
	•	推奨: Decorator + Event Emitter
	•	アクション実行前後のフックにデコレータを適用。任意でイベント発火。

1.7 エラー制御 / リトライ
	•	推奨: Policy/Strategy + Chain
	•	RetryPolicy, TimeoutPolicy, CircuitBreakerPolicy を組合せて Runner に注入。

⸻

2. ディレクトリと命名指針
	•	wao/actions/ … 各アクション（*_action.py）と registry.py
	•	wao/runner.py … テンプレート/チェーン骨格
	•	wao/dsl_parser.py, wao/validation.py … Builder/Factory/Spec
	•	wao/browser/ … Strategy/Adapter
	•	wao/observers/ … Decorator, Emitters（log/screenshot/metrics）
	•	wao/config.py … Singleton/DIエントリ

命名: FooAction（Command）, FooPolicy, FooStrategy, FooAdapter, FooSpec。

⸻

3. 最小インターフェース（準拠必須）

# wao/types.py
from dataclasses import dataclass
from typing import Any, Mapping

@dataclass(frozen=True)
class Step:
    name: str
    params: Mapping[str, Any]

class Action:
    def execute(self, ctx: "Context", step: Step) -> None:  # 必須
        raise NotImplementedError

class Context:
    page: Any  # Playwright page 等
    logger: Any
    artifacts: Any  # スクショ/ログ/メトリクス収集


⸻

4. Registry（Factory）規約

# wao/actions/registry.py
_REGISTRY = {}

def register(name: str):
    def deco(cls):
        _REGISTRY[name] = cls
        return cls
    return deco

def create(name: str, **kwargs):
    cls = _REGISTRY.get(name)
    if not cls:
        raise KeyError(f"Unknown action: {name}")
    return cls(**kwargs)

DSLの {"action": "click", ...} は create("click") で具象コマンドへ解決する。

⸻

5. Decorator による副作用（例: log / screenshot）

# wao/observers/decorators.py
from functools import wraps

def with_logging(fn):
    @wraps(fn)
    def wrapper(self, ctx, step):
        ctx.logger.info({"start": step.name, "params": dict(step.params)})
        try:
            return fn(self, ctx, step)
        finally:
            ctx.logger.info({"end": step.name})
    return wrapper

def with_screenshot_on_error(fn):
    @wraps(fn)
    def wrapper(self, ctx, step):
        try:
            return fn(self, ctx, step)
        except Exception:
            ctx.artifacts.screenshot(label=f"error_{step.name}")
            raise
    return wrapper


⸻

6. 代表的アクション実装（Command）

6.1 sleep_random （ユーティリティ系）

# wao/actions/sleep_random_action.py
import random, time
from wao.actions.registry import register
from wao.types import Action, Step
from wao.observers.decorators import with_logging

@register("sleep_random")
class SleepRandomAction(Action):
    @with_logging
    def execute(self, ctx, step: Step) -> None:
        lo = float(step.params.get("min", 0.5))
        hi = float(step.params.get("max", 2.0))
        sec = random.uniform(lo, hi)
        time.sleep(sec)
        ctx.artifacts.note(key="sleep_random", value=sec)

6.2 assert_title （検証系）

# wao/actions/assert_title_action.py
from wao.actions.registry import register
from wao.types import Action, Step
from wao.observers.decorators import with_logging, with_screenshot_on_error

@register("assert_title")
class AssertTitleAction(Action):
    @with_logging
    @with_screenshot_on_error
    def execute(self, ctx, step: Step) -> None:
        expect = str(step.params["equals"])  # 必須
        title = ctx.page.title()
        if title != expect:
            raise AssertionError(f"title mismatch: {title} != {expect}")

6.3 screenshot （成果物残し）

# wao/actions/screenshot_action.py
from wao.actions.registry import register
from wao.types import Action, Step
from wao.observers.decorators import with_logging

@register("screenshot")
class ScreenshotAction(Action):
    @with_logging
    def execute(self, ctx, step: Step) -> None:
        label = step.params.get("label") or step.name
        ctx.artifacts.screenshot(label=label)

6.4 log （任意ログを残す）

# wao/actions/log_action.py
from wao.actions.registry import register
from wao.types import Action, Step
from wao.observers.decorators import with_logging

@register("log")
class LogAction(Action):
    @with_logging
    def execute(self, ctx, step: Step) -> None:
        level = (step.params.get("level") or "info").lower()
        message = step.params.get("message") or ""
        getattr(ctx.logger, level)({"message": message, "step": step.name})


⸻

7. Runner（Template + Chain）骨格

# wao/runner.py
class Runner:
    def __init__(self, policies):  # Retry/Timeout/Circuit 等
        self.policies = policies

    def run_flow(self, ctx, steps):
        self.before_all(ctx, steps)
        try:
            for step in steps:
                self.before_each(ctx, step)
                self._execute_with_policies(ctx, step)
                self.after_each(ctx, step)
        finally:
            self.after_all(ctx, steps)

    # --- Template hooks ---
    def before_all(self, ctx, steps): ...
    def after_all(self, ctx, steps): ...
    def before_each(self, ctx, step): ...
    def after_each(self, ctx, step): ...

    def _execute_with_policies(self, ctx, step):
        action = create(step.name)
        # 例: リトライポリシでラップ
        fn = lambda: action.execute(ctx, step)
        for p in self.policies:
            fn = p.wrap(fn)
        return fn()


⸻

8. DSL バリデーション（Specification）例

# wao/validation.py
class Rule:
    def is_valid(self, step) -> bool: raise NotImplementedError

class RequiredParam(Rule):
    def __init__(self, key): self.key = key
    def is_valid(self, step): return self.key in step.params

class OneOf(Rule):
    def __init__(self, key, choices): self.key, self.choices = key, set(choices)
    def is_valid(self, step): return step.params.get(self.key) in self.choices

SPEC = {
  "assert_title": [RequiredParam("equals")],
  "sleep_random": [OneOf("profile", {None, "short", "long"})],
}


⸻

9. Config/Secrets（Singleton/DI）

# wao/config.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    env: str
    secrets_path: str

_config_singleton: Config | None = None

def get_config() -> Config:
    global _config_singleton
    if _config_singleton is None:
        # 実装は環境変数/JSON から構築
        _config_singleton = Config(env="dev", secrets_path="secrets.json")
    return _config_singleton


⸻

10. PR レビュー・チェックリスト（準拠確認）
	•	新規アクションは Command として execute(ctx, step) を実装している
	•	Registry に登録され、DSL から解決できる
	•	ログ/スクショ等の副作用は Decorator 経由で付加
	•	Runner の骨格は Template Method に従っている
	•	リトライ/タイムアウトは Policy/Strategy で注入（直書きしない）
	•	Parser/Validation は Builder/Spec を活用
	•	Config/Secrets は Singleton/DI で注入/差替え可能
	•	単体テストが Action 単位で存在し、Context をモック可能

⸻

11. アンチパターン（避けるべき）
	•	大規模 if/elif でアクション分岐（→ Registry/Factory で置換）
	•	Action 内で直接 time.sleep リトライ/タイムアウトを実装（→ Policy に抽出）
	•	Playwright 直接呼び出しの散在（→ Browser Strategy/Adapter を経由）
	•	グローバル書換え可能な設定オブジェクト（→ 不変/DI）

⸻

12. 移行メモ（最小パッチ）
	1.	wao/types.py に Action/Step/Context を定義。
	2.	wao/actions/registry.py を導入し、既存アクションを順次登録化。
	3.	ログ/スクショは Decorator に切出し、Action から直呼びを削減。
	4.	Runner を Template 骨格に整理し、リトライ等は Policy に抽出。
	5.	バリデーションを Spec へ段階的に移管。

本ポリシーは v0.1（草案）。採用/修正は PR で合意の上、docs/20-architecture.md にリンクを追加してください。
