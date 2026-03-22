# CambodiaJapanEarthMap

都市名を指定すると、地球儀風の地図画像を生成するPythonアプリです。
対象都市を中心にした正射影(orthographic)投影で、日本とカンボジアに旗マーカーを描画します。

## セットアップ

```bash
pip install -r requirements.txt
```

### クメール語フォント（Windows）

クメール語を正しく表示するには、以下のいずれかが必要です:

1. **Khmer UI フォント**（Windows 10/11 に含まれる場合あり）
2. **手動配置**: `fonts/` ディレクトリに [Noto Sans Khmer](https://fonts.google.com/noto/specimen/Noto+Sans+Khmer) を `NotoSansKhmer-Regular.ttf` として配置

### harfbuzz / libraqm（クメール語の結合文字用）

クメール語の母音記号を正しくレンダリングするために必要です:

- **macOS**: `brew install libraqm` → `pip install --force-reinstall Pillow`
- **Windows**: Pillow の最新版（10.x+）には harfbuzz が同梱されています

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
