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

# Chatwork にアップロード
python mapgen.py ロンドン --upload 426936385
```

## 対応都市

80以上の主要都市に対応（日本語 → 英語・クメール語の自動マッピング付き）。
マッピングにない都市でも、Nominatim ジオコーディングで座標を取得して生成できます。
