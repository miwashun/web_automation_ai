# MyTokyoGas Site Profile

## Login URL
https://members.tokyo-gas.co.jp/

## 2FA/OTP
- 利用状況: <TODO>（必要なら SMS / メール / アプリ）

## Selectors
- Username field: `<input name="loginId" id="loginId" type="email">`
- Password field: `<input name="password" id="password" type="password">`
- Login button: `<button id="submit-btn" class="mtg-button-cta submit log-button-top">ログイン</button>`
- Other important selectors: <TODO>

## Target Pages
- 請求/使用量ページ: <TODO URL>
- ポイントページ: <TODO URL>

## Constraints
- ログイン後にリダイレクトがある
- セッションタイムアウト: 約 <TODO> 分

## Recovery Steps
- セッション切れ時は再ログイン
- CAPTCHAが出る場合は手動介入
