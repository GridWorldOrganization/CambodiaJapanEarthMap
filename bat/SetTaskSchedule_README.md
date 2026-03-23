# ClaudeMapApp バッチ 取り扱い説明書

> Windows タスクスケジューラ専用の登録バッチ群です。
> Claude Code を定期実行して、地図画像の生成・Chatwork投稿を自動化します。

---

## ファイル一覧

| ファイル | 役割 |
|---|---|
| `SetTaskSchedule_config.env` | 設定ファイル（タスク名・実行パス・手順書・スケジュール） |
| `SetTaskSchedule_register.bat` | タスクスケジューラへの登録（ダブルクリックで実行） |
| `SetTaskSchedule_register.ps1` | 登録処理の本体（PowerShell）。register.bat から呼ばれる |
| `SetTaskSchedule_runner.bat` | タスクスケジューラから実際に起動されるバッチ |
| `SetTaskSchedule_unregister.bat` | タスクスケジューラからの登録削除 |
| `SetTaskSchedule_watch.bat` | ログをリアルタイム監視するウィンドウを開く |
| `SetTaskSchedule_config.env.example` | 設定ファイルのサンプル（各項目の説明付き） |
| `maintenance/` | 修正・メンテナンス用ファイル一式 |
| `maintenance/SetTaskSchedule_runner_gen.py` | runner.bat を Shift-JIS で生成する Python スクリプト。runner.bat を編集したい場合はこちらを修正して `python maintenance/SetTaskSchedule_runner_gen.py` を実行する |

---

## 設定ファイル（.env）

```ini
# タスクスケジューラのタスク名
TASK_NAME=ClaudeMapApp

# 何分に1回起動するか（分間隔モード）
# 0 にすると SCHEDULE_TIMES の時刻指定モードになる
INTERVAL_MINUTES=10

# 時刻指定モード時の起動時刻（カンマ区切り）
# 例: 09:00,13:00,18:00
SCHEDULE_TIMES=09:00,18:00

# 実行モード（dev=開発, prod=本番）
MODE=dev

# 実行する手順書ファイル名
PROCEDURE_FILE=

# claude.cmd が入っているフォルダパス（PATH が通っていない環境向け）
# 空欄にすると PATH をそのまま使う
# 例: C:\Users\yourname\AppData\Roaming\npm
CLAUDE_CODE_EXEC_DIR=
```

### スケジュールモードの切り替え

| 設定 | 動作 |
|---|---|
| `INTERVAL_MINUTES=10` | 10分ごとに繰り返し起動 |
| `INTERVAL_MINUTES=0` | `SCHEDULE_TIMES` に指定した時刻に毎日起動 |

### CLAUDE_CODE_EXEC_DIR（claude -p 実行ディレクトリ）

`claude -p` を実行するカレントディレクトリを指定します。空欄の場合は bat フォルダの2階層上を自動で使用します。

| 設定 | 動作 |
|---|---|
| `CLAUDE_CODE_EXEC_DIR=` （空欄） | bat フォルダの2階層上を自動で使用 |
| `CLAUDE_CODE_EXEC_DIR=C:\path\to\project` | 指定したディレクトリで claude を実行 |

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

## 文字コード設定

各ファイルの文字コードは以下の通りです。**編集時は必ずこの設定に合わせてください。**

| ファイル | 文字コード | 理由 |
|---|---|---|
| `SetTaskSchedule_runner.bat` | **Shift-JIS (ANSI)** | cmd.exe はファイルを起動時に Shift-JIS として解析するため。UTF-8 にすると日本語コマンドが文字化けして実行エラーになる |
| `SetTaskSchedule_register.bat` | **Shift-JIS (ANSI)** | 同上 |
| `SetTaskSchedule_unregister.bat` | **Shift-JIS (ANSI)** | 同上 |
| `SetTaskSchedule_watch.bat` | **Shift-JIS (ANSI)** | 同上 |
| `SetTaskSchedule_register.ps1` | **UTF-8 BOM付き** | PowerShell 5 は BOM なし UTF-8 を ANSI と誤認するため、BOM 付きが必要 |
| `SetTaskSchedule_config.env` | **Shift-JIS (ANSI)** | runner.bat の `for /f` ループで読み込むため、bat と同じ文字コードが必要 |
| `SetTaskSchedule_config.env.example` | **Shift-JIS (ANSI)** | 同上 |
| `maintenance/SetTaskSchedule_runner_gen.py` | **UTF-8** | Python スクリプト。Shift-JIS の runner.bat を生成するために使用 |
| `SetTaskSchedule_README.md` | **UTF-8** | 閲覧専用のため制限なし |

### ⚠️ 注意

- `.bat` ファイルを **UTF-8 で保存すると動作しません**（タスクスケジューラ実行時にコマンドが認識されないエラーが発生します）
- `chcp 65001`（UTF-8切り替えコマンド）を先頭に追加しても、**ファイル自体の解析には効かない**ため解決しません
- テキストエディタで編集する場合は、保存時の文字コードを必ず確認してください

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
