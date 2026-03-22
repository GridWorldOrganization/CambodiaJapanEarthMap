# CambodiaJapanEarthMap

都市名を指定すると、地球儀風の地図画像を生成するPythonアプリです。
対象都市を中心にした正射影(orthographic)投影で、日本とカンボジアに旗マーカーを描画します。

## セットアップ

```bash
pip install -r requirements.txt
```

## フォント設定ガイド（Windows）

### 日本語フォント

Windows に「メイリオ」「MS ゴシック」「游ゴシック」のいずれかが入っていれば自動検出されます。通常はそのまま動きます。

### クメール語フォント

Windows にはクメール語フォントが入っていない場合が多いため、手動で配置が必要です。

**手順:**

1. Google Fonts から **Noto Sans Khmer** をダウンロード
   - https://fonts.google.com/noto/specimen/Noto+Sans+Khmer
   - 「Download family」ボタンをクリック

2. ダウンロードした ZIP を解凍し、`NotoSansKhmer-Regular.ttf` を取り出す

3. プロジェクト内に `fonts` フォルダを作成し、そこに配置する:
   ```
   CambodiaJapanEarthMap/
   ├── mapgen.py
   ├── fonts/
   │   └── NotoSansKhmer-Regular.ttf   ← ここに置く
   └── ...
   ```

4. 再度 `python mapgen.py パリ` を実行

### harfbuzz（クメール語の結合文字用）

クメール語の母音記号が文字からずれて表示される場合は、Pillow に harfbuzz が含まれていない可能性があります。

- **Windows**: Pillow 10.x 以降には harfbuzz が同梱されています。最新版にアップグレードしてください:
  ```bash
  pip install --upgrade Pillow
  ```
- **macOS**: `brew install libraqm` → `pip install --force-reinstall Pillow`

### Chatwork アップロード（オプション）

```bash
export CHATWORK_API_TOKEN="your-token-here"   # macOS/Linux
set CHATWORK_API_TOKEN=your-token-here         # Windows
```

## 使い方

```bash
# 地図画像を生成
python mapgen.py パリ

# 出力先を指定
python mapgen.py 東京 -o ./output

# 三日月を強制表示（無指定だと約30%の確率でランダム表示）
python mapgen.py ロンドン --force-moon

# UFOを強制表示（無指定だと約20%の確率でランダム表示）
python mapgen.py ニューヨーク --force-ufo

# 月もUFOも両方強制表示
python mapgen.py バンコク --force-moon --force-ufo

# Chatwork にアップロード
python mapgen.py ロンドン --upload 426936385
```

### オプション一覧

| オプション | 説明 |
|-----------|------|
| `--output`, `-o` | 出力先ディレクトリを指定 |
| `--force-moon` | 三日月を強制表示（無指定時は約30%の確率でランダム表示） |
| `--force-ufo` | UFOを強制表示（無指定時は約20%の確率でランダム表示） |
| `--force-city-auto-add` | 未登録都市をNominatimで自動検索して生成（要ネット接続） |
| `--upload`, `-u` | ChatworkルームIDを指定してアップロード |
| `--message`, `-m` | アップロード時のメッセージ |

## 対応都市

210以上の主要都市に対応（日本語 → 英語・クメール語の自動マッピング付き、座標・距離は事前計算済み）。
未登録の都市を指定するとエラーで終了します。`--force-city-auto-add` オプションを付けると、Nominatim ジオコーディングで座標を自動取得して生成できます（要ネット接続）。
2回目以降はタイルキャッシュによりオフラインで生成可能です。
