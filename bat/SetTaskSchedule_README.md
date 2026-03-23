# ClaudeMapApp バッチ 取り扱い説明書

> Windows タスクスケジューラ専用の登録バッチ群です。
> Claude Code を定期実行して、地図画像の生成・Chatwork投稿を自動化します。

---

## ファイル一覧

| ファイル | 役割 |
|---|---|
| `SetTaskSchedule_config.env` | 設定ファイル（間隔・時刻・手順書ファイル名） |
| `SetTaskSchedule_register.bat` | タスクスケジューラへの登録（ダブルクリックで実行） |
| `SetTaskSchedule_register.ps1` | 登録処理の本体（PowerShell）。register.bat から呼ばれる |
| `SetTaskSchedule_runner.bat` | タスクスケジューラから実際に起動されるバッチ |
| `SetTaskSchedule_unregister.bat` | タスクスケジューラからの登録削除 |
| `SetTaskSchedule_watch.bat` | ログをリアルタイム監視するウィンドウを開く |

---

## 設定ファイル（.env）

```ini
# 何分に1回起動するか（分間隔モード）
# 0 にすると SCHEDULE_TIMES の時刻指定モードになる
INTERVAL_MINUTES=10

# 時刻指定モード時の起動時刻（カンマ区切り）
# 例: 09:00,13:00,18:00
SCHEDULE_TIMES=09:00,18:00

# 実行する手順書ファイル名
PROCEDURE_FILE=20260323_1711_AI手順書_地図投稿.md
```

### モードの切り替え

| 設定 | 動作 |
|---|---|
| `INTERVAL_MINUTES=10` | 10分ごとに繰り返し起動 |
| `INTERVAL_MINUTES=0` | `SCHEDULE_TIMES` に指定した時刻に毎日起動 |

> ⚠️ `SetTaskSchedule_config.env` を変更したあとは、**一度削除して再登録**しないと反映されません。

---

## 使い方

### 1. 初回登録

1. `SetTaskSchedule_config.env` を編集して設定を確認する
2. `SetTaskSchedule_register.bat` をダブルクリックして実行
3. 「登録完了。確認:」と表示されれば成功

> 管理者権限は不要です（現在のユーザーとして登録されます）。

### 2. 設定変更時の再登録

1. `SetTaskSchedule_config.env` を編集
2. `SetTaskSchedule_unregister.bat` を実行（既存タスクを削除）
3. `SetTaskSchedule_register.bat` を実行（新しい設定で再登録）

### 3. 登録削除

`SetTaskSchedule_unregister.bat` をダブルクリックして実行。

### 4. 実行状況の確認（ログ監視）

`SetTaskSchedule_watch.bat` を別ウィンドウで開くと、ログがリアルタイムで流れます。

- ログファイル: `bat\SetTaskSchedule.log`（実行のたびに上書き）
- 監視停止: `Ctrl+C`

---

## runner.bat の動作フロー

```
[ClaudeMapApp] 開始: 日時
  ↓
.env 読み込み（PROCEDURE_FILE を取得）
  ↓
[ClaudeMapApp] 手順書: ファイル名
  ↓
[ClaudeMapApp] ディレクトリ移動中...
  ↓
[ClaudeMapApp] Claude実行中...
  ↓ claude --verbose -p "タスクを実行して　{PROCEDURE_FILE}"
  ↓（出力はすべてログファイルへ）
  ↓
正常終了 → [ClaudeMapApp] 完了: 日時  → ウィンドウ自動クローズ
異常終了 → [ClaudeMapApp] エラー発生！ → pause（キー入力待ち）
```

> 実行中は Claude の出力がリアルタイムでログに書かれます。
> `SetTaskSchedule_watch.bat` を開いておくと内容を確認できます。

---

## 注意事項

- **このバッチは Windows タスクスケジューラ専用**です。直接ダブルクリックして runner.bat を起動することも可能ですが、本来はスケジューラから自動起動するように設計されています。
- タスク名は `ClaudeMapApp` で固定です。同名のタスクが既にある場合は上書き登録されます。
- `INTERVAL_MINUTES` が `1` などの極端に小さい値の場合、Claude の実行時間（数分）が間隔を超えてしまいます。`MultipleInstances IgnoreNew` の設定により、前の実行が終わっていない場合は次の起動はスキップされます。
- `SetTaskSchedule_config.env` ファイルはコメント行（`#` で始まる行）と空行を無視して読み込みます。
- ログファイルは実行のたびに**上書き**されます。過去のログは残りません。

---

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| 登録しても起動しない | タスクスケジューラの「タスク スケジューラ ライブラリ」で `ClaudeMapApp` を確認 |
| 文字化けが起きる | このフォルダは Shift-JIS で保存されています。テキストエディタの文字コード設定を確認 |
| `claude` が見つからない | `claude` の PATH が通っているか確認（`where claude` で確認） |
| ログが空のまま | runner.bat を直接ダブルクリックして動作確認。エラーが出れば pause で止まります |
| 設定変更が反映されない | unregister → register の手順で再登録してください |
