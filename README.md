# CambodiaJapanEarthMap

都市名を指定すると、地球儀風の地図画像を生成するPythonアプリです。
対象都市を中心にした正射影(orthographic)投影で、日本とカンボジアに旗マーカーを描画します。

## セットアップ

```bash
pip install -r requirements.txt
```

## フォント設定ガイド

### 日本語フォント

- **Windows**: 「メイリオ」「MS ゴシック」「游ゴシック」のいずれかが入っていれば自動検出されます。通常はそのまま動きます。
- **macOS**: システムフォントが自動使用されます。

### クメール語フォント

**Noto Sans Khmer** がリポジトリの `fonts/` に同梱済みです。追加作業は不要です。

```
CambodiaJapanEarthMap/
├── mapgen.py
├── fonts/
│   └── NotoSansKhmer-Regular.ttf   ← 同梱済み
└── ...
```

> **注意:** macOS では `/System/Library/Fonts/Supplemental/Khmer MN.ttc` が優先使用されます。Windows では同梱フォントが自動的に使われます。

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

### PNG静止画の生成

```bash
# 都市名を指定して生成
python mapgen.py パリ

# 出力先を指定
python mapgen.py 東京 -o ./output

# 三日月を強制表示（無指定だと約30%の確率でランダム表示）
python mapgen.py ロンドン --force-moon

# UFOを強制表示（無指定だと約20%の確率でランダム表示）
python mapgen.py ニューヨーク --force-ufo

# 月もUFOも両方強制表示
python mapgen.py バンコク --force-moon --force-ufo

# 都市名を省略するとランダムに選出
python mapgen.py
```

### アニメGIFの生成

地球儀が回転して都市を中心に停止するアニメーションGIFを生成します。

```bash
# 基本（デフォルト: 60%スケール）
python mapgen.py 東京 --gif

# スケール指定（50/60/70/80/90/100）
python mapgen.py 東京 --gif --gif-scale 80

# 移動方向を指定（未指定=ランダム）
python mapgen.py 東京 --gif --force-direction right-to-center

# フレーム数・速度を調整
python mapgen.py 東京 --gif --gif-frames 48 --gif-duration 40

# 全部盛り
python mapgen.py ウラジオストク --gif --gif-scale 60 --force-moon --force-ufo --force-direction right-to-center
```

出力ファイル名: `map_{都市名}_{YYYYMMDD_HHMMSS}_{scale}.gif`

#### GIF スケール別ファイルサイズ目安

| スケール | 解像度 | ファイルサイズ |
|---------|--------|-------------|
| 100 | 960x916 | 約 6.7 MB |
| 90 | 864x824 | 約 6.8 MB |
| 80 | 768x733 | 約 5.6 MB |
| 70 | 672x641 | 約 4.5 MB |
| 60 | 576x549 | 約 2.4 MB |
| 50 | 480x458 | 約 2.6 MB |

#### 移動方向の選択肢

`--force-direction` で指定可能な値:

- `right-to-center`, `left-to-center`
- `top-to-center`, `bottom-to-center`
- `top-right-to-center`, `top-left-to-center`
- `bottom-right-to-center`, `bottom-left-to-center`

### Chatwork へのアップロード

```bash
python mapgen.py ロンドン --upload 426936385
python mapgen.py ロンドン --upload 426936385 -m "カスタムメッセージ"
```

### オプション一覧

| オプション | 説明 |
|-----------|------|
| `--output`, `-o` | 出力先ディレクトリを指定（デフォルト: カレント） |
| `--force-moon` | 三日月を強制表示（無指定時は約30%の確率でランダム表示） |
| `--force-ufo` | UFOを強制表示（無指定時は約20%の確率でランダム表示） |
| `--force-city-auto-add` | 未登録都市をNominatimで自動検索して生成（要ネット接続） |
| `--gif` | アニメGIFを生成（デフォルトはPNG静止画） |
| `--gif-scale` | GIF解像度: 50/60/70/80/90/100（デフォルト: 60） |
| `--gif-frames` | GIFのフレーム数（デフォルト: 36） |
| `--gif-duration` | GIFの1フレームの表示時間ms（デフォルト: 50） |
| `--force-direction` | GIFの移動方向を指定（未指定=ランダム） |
| `--upload`, `-u` | ChatworkルームIDを指定してアップロード |
| `--message`, `-m` | アップロード時のメッセージ |

## 対応都市

210以上の主要都市に対応（日本語 → 英語・クメール語の自動マッピング付き、座標・距離は事前計算済み）。
未登録の都市を指定するとエラーで終了します。`--force-city-auto-add` オプションを付けると、Nominatim ジオコーディングで座標を自動取得して生成できます（要ネット接続）。
2回目以降はタイルキャッシュによりオフラインで生成可能です。

## 技術的な注意点

- GIFは全フレームで共通パレット（256色）を使用。停止フレーム基準でパレットを生成するため、回転中も停止時も色が一貫します。
- スケール縮小時はRGB状態でLANCZOSリサイズ後にパレット変換するため、フォントがスムーズに描画されます。
- スケールが小さいほど、停止時の中央都市名ラベルのフォントサイズが自動で大きくなります（視認性確保）。
