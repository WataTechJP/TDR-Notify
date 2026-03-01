# TDR Notify (MVP)

Tokyo Disney Resort の特定ページセクションを定期監視し、変更時に Expo Push Notification を送る MVP です。  
現在は `backend`（FastAPI）と `frontend`（Expo React Native）を実装しています。

この実装は `SPEC.md` 準拠で、`ISSUE.md` は未反映です。

## 実装済みスコープ

- 監視対象: 単一 URL + 単一 CSS セレクタ（環境変数で指定）
  - 既定値は `https://www.tokyodisneyresort.jp/tdr/news/update/` の更新情報一覧（`.linkList6.listUpdate ul`）
- 監視ロジック: 取得 → セクション抽出 → テキスト化 → SHA256 比較
- 変更時処理: `monitor_state` 更新 + 登録トークンへ push 通知
- スケジュール: 60分以上間隔、0-30秒ジッター、起動時1回実行
- 制約: robots.txt 確認、5秒タイムアウト、3連続失敗で停止
- API:
  - `POST /register`
  - `GET /status`

## ディレクトリ

```text
backend/
frontend/
```

## 前提

- Python 3.11+（ローカル検証は 3.14.3 で実施）
- `uv`
- PostgreSQL
- Node.js 20+ / npm（ローカル検証は Node 22.12.0）

## 環境変数

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
MONITOR_URL=https://www.tokyodisneyresort.jp/tdr/news/update/
MONITOR_SELECTOR=.linkList6.listUpdate ul
CHECK_INTERVAL_MINUTES=60
USER_AGENT=DisneyMonitorBot/1.0
REQUEST_TIMEOUT_SECONDS=5
RANDOM_DELAY_MAX_SECONDS=30
MAX_CONSECUTIVE_FAILURES=3
EXPO_PUSH_URL=https://exp.host/--/api/v2/push/send
```

## ローカル起動

### Backend

初回セットアップ:

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

2回目以降（`backend/` にいる前提）:

```bash
.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```

コード変更の自動リロードを使いたい場合:

```bash
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run start
```

`frontend/.env` に以下を設定してください（`.env.example` あり）。

```bash
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
EXPO_PUBLIC_EAS_PROJECT_ID=<your-eas-project-id>
```

実機で Expo Go を使う場合は `127.0.0.1` ではなく、PC の LAN IP（例: `http://192.168.1.10:8000`）を設定してください。
`EXPO_PUBLIC_EAS_PROJECT_ID` は `eas project:info` の `projectId` を設定してください。

## API

### `POST /register`

Request:

```json
{
  "push_token": "ExponentPushToken[...]"
}
```

Response:

```json
{
  "status": "registered"
}
```

### `GET /status`

Response:

```json
{
  "last_checked_at": "2026-02-25T14:51:10.772446Z",
  "last_updated_at": "2026-02-25T14:51:12.677619Z"
}
```

初回など状態未生成時は両方 `null` を返します。

## Docker

### Docker Compose（推奨）

```bash
cd /path/to/TDR_Notify
docker compose up --build -d
curl http://127.0.0.1:8000/status
```

停止:

```bash
docker compose down
```

DB データも消す場合:

```bash
docker compose down -v
```

`compose.yaml` は backend と PostgreSQL を同時起動し、backend は `db` サービスのヘルスチェック完了後に起動します。

### 単体起動（backend コンテナのみ）

```bash
cd backend
docker build -t tdr-notify .
docker run --rm -p 8000:8000 \
  -e DATABASE_URL='postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/tdr_notify' \
  -e MONITOR_URL='https://www.tokyodisneyresort.jp/tdr/news/update/' \
  -e MONITOR_SELECTOR='.linkList6.listUpdate ul' \
  tdr-notify
```

## 実行確認（2026-02-25 実施）

- 依存導入後、FastAPI 起動と API 疎通を確認
  - `GET /status` → `{"last_checked_at":null,"last_updated_at":null}`
  - `POST /register` → `{"status":"registered"}`
- 監視ロジックの実行確認
  - ローカルHTTPターゲット + PostgreSQL で起動時チェックを2回実施
  - 1回目: `changed=False`, `last_checked_at` のみ更新
  - 2回目（HTML変更後）: `changed=True`, `last_updated_at` 更新
- Frontend 実装確認
  - `npm install` 成功
  - `npx expo --version` → `0.24.24`

## 注意点

- 実運用では監視対象サイトの robots.txt と利用規約に従ってください。
- 実行環境によっては HTTPS 証明書ストア不足で `CERTIFICATE_VERIFY_FAILED` が発生します。
  - その場合は OS/ランタイム側の CA 証明書設定を修正してください。
