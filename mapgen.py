#!/usr/bin/env python3
"""
都市名を指定して、地球儀風の地図画像を生成する。
対象都市を中心にした正射影(orthographic)投影で、日本とカンボジアに旗を描画。

使い方:
  python3 mapgen.py パリ
  python3 mapgen.py "ニューヨーク" --upload 426936385
"""

import sys
import os
import math
import subprocess
from pathlib import Path
from typing import Tuple, Optional

import random
import hashlib

from staticmap import StaticMap, CircleMarker
from geopy.geocoders import Nominatim
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# === 定数 ===
GLOBE_SIZE = 700         # 地球儀の直径
IMG_W = 960
IMG_H = 990

# 固定座標 (lon, lat)
JAPAN_COORD = (139.6917, 35.6895)
CAMBODIA_COORD = (104.9160, 11.5564)

# 色パレット
COLOR_BG = (12, 18, 40)
COLOR_OCEAN_RING = (40, 80, 130)
COLOR_TEXT = (230, 230, 230)
COLOR_CITY = (220, 30, 30)
COLOR_WHITE = (255, 255, 255)


def geocode_city(city_name):
    # type: (str) -> Tuple[float, float]
    """都市名から座標を取得。日本語→英語→各種言語でリトライ"""
    geolocator = Nominatim(user_agent="mapgen-app")
    # まずそのまま検索
    location = geolocator.geocode(city_name)
    if location:
        return (location.longitude, location.latitude)
    # 日本語指定で検索
    location = geolocator.geocode(city_name, language="ja")
    if location:
        return (location.longitude, location.latitude)
    # 英語名マッピングで検索
    en_name = CITY_NAME_MAP.get(city_name, {}).get("en")
    if en_name:
        location = geolocator.geocode(en_name)
        if location:
            return (location.longitude, location.latitude)
    raise ValueError("都市が見つかりません: {}".format(city_name))


# 都市名マッピング（日本語 -> 英語, クメール語）
CITY_NAME_MAP = {
    "パリ": {"en": "Paris", "km": "ប៉ារីស"},
    "ロンドン": {"en": "London", "km": "ឡុងដ៍"},
    "ニューヨーク": {"en": "New York", "km": "ញូវយ៉ក"},
    "東京": {"en": "Tokyo", "km": "តូក្យូ"},
    "バグダッド": {"en": "Baghdad", "km": "បាកដាដ"},
    "ヨハネスブルク": {"en": "Johannesburg", "km": "យ៉ូហានេស្ប៊ឺក"},
    "プノンペン": {"en": "Phnom Penh", "km": "ភ្នំពេញ"},
    "バンコク": {"en": "Bangkok", "km": "បាងកក"},
    "シドニー": {"en": "Sydney", "km": "ស៊ីដនី"},
    "カイロ": {"en": "Cairo", "km": "កែរ៉ូ"},
    "ドバイ": {"en": "Dubai", "km": "ឌូបៃ"},
    "ソウル": {"en": "Seoul", "km": "សូល"},
    "ムンバイ": {"en": "Mumbai", "km": "មុំបៃ"},
    "メキシコシティ": {"en": "Mexico City", "km": "ម៉ិចស៊ីកូស៊ីធី"},
    "モスクワ": {"en": "Moscow", "km": "មូស្គូ"},
    "ブエノスアイレス": {"en": "Buenos Aires", "km": "ប៊ុយណូស៍អាយ៉េស"},
    "ナイロビ": {"en": "Nairobi", "km": "ណៃរ៉ូប៊ី"},
    "バンクーバー": {"en": "Vancouver", "km": "វ៉ាន់គូវ័រ"},
    "イスタンブール": {"en": "Istanbul", "km": "អ៊ីស្តង់ប៊ុល"},
    "リマ": {"en": "Lima", "km": "លីម៉ា"},
    "ヘルシンキ": {"en": "Helsinki", "km": "ហែលស៊ីនគី"},
    "サンティアゴ": {"en": "Santiago", "km": "សាន់ទីអាហ្គោ"},
    "ラゴス": {"en": "Lagos", "km": "ឡាហ្គូស"},
    "アンカレジ": {"en": "Anchorage", "km": "អានករ៉ាស"},
    "ダッカ": {"en": "Dhaka", "km": "ដាក្កា"},
    "オークランド": {"en": "Auckland", "km": "អូក្លែន"},
    "カラカス": {"en": "Caracas", "km": "ការ៉ាកាស"},
    "タシュケント": {"en": "Tashkent", "km": "តាស្ហ្គិន"},
    "アディスアベバ": {"en": "Addis Ababa", "km": "អាឌីស អាបេបា"},
    "レイキャビク": {"en": "Reykjavik", "km": "រេយ្គ្យាវិក"},
    "キンシャサ": {"en": "Kinshasa", "km": "គីនស្ហាស"},
    "アルマティ": {"en": "Almaty", "km": "អាល់ម៉ាទី"},
    "パナマシティ": {"en": "Panama City", "km": "ប៉ាណាម៉ា"},
    "ルアンダ": {"en": "Luanda", "km": "លូអ័ន់ដា"},
    "北京": {"en": "Beijing", "km": "ប៉េកាំង"},
    "上海": {"en": "Shanghai", "km": "សៀងហៃ"},
    "広州": {"en": "Guangzhou", "km": "ក្វាងចូវ"},
    "深圳": {"en": "Shenzhen", "km": "សិនជិន"},
    "重慶": {"en": "Chongqing", "km": "ឈុងឈីង"},
    "天津": {"en": "Tianjin", "km": "ធានជីន"},
    "香港": {"en": "Hong Kong", "km": "ហុងកុង"},
    "台北": {"en": "Taipei", "km": "តៃប៉ិ"},
    "大阪": {"en": "Osaka", "km": "អូសាកា"},
    "マニラ": {"en": "Manila", "km": "ម៉ានីល"},
    "ジャカルタ": {"en": "Jakarta", "km": "ចាការតា"},
    "シンガポール": {"en": "Singapore", "km": "សិង្ហបុរី"},
    "クアラルンプール": {"en": "Kuala Lumpur", "km": "កូឡាឡាំពួរ"},
    "ホーチミン": {"en": "Ho Chi Minh City", "km": "ហូជីមីញ"},
    "ハノイ": {"en": "Hanoi", "km": "ហាណូយ"},
    "ヤンゴン": {"en": "Yangon", "km": "យ៉ាំងហ្គោន"},
    "デリー": {"en": "Delhi", "km": "ដេលី"},
    "コルカタ": {"en": "Kolkata", "km": "កុលកាតា"},
    "チェンナイ": {"en": "Chennai", "km": "ឈេន្នៃ"},
    "バンガロール": {"en": "Bangalore", "km": "បេនហ្គាឡូរ"},
    "カラチ": {"en": "Karachi", "km": "ការ៉ាជី"},
    "ラホール": {"en": "Lahore", "km": "ឡាហោរ"},
    "テヘラン": {"en": "Tehran", "km": "តេហេរ៉ង់"},
    "バグダッド": {"en": "Baghdad", "km": "បាកដាដ"},
    "リヤド": {"en": "Riyadh", "km": "រីយ៉ាដ"},
    "ジェッダ": {"en": "Jeddah", "km": "ជេដ្ដា"},
    "アンカラ": {"en": "Ankara", "km": "អង់ការ៉ា"},
    "テルアビブ": {"en": "Tel Aviv", "km": "តែលអាវីវ"},
    "ベルリン": {"en": "Berlin", "km": "បែរឡាំង"},
    "マドリード": {"en": "Madrid", "km": "ម៉ាឌ្រីដ"},
    "ローマ": {"en": "Rome", "km": "រ៉ូម"},
    "ミラノ": {"en": "Milan", "km": "មីឡង់"},
    "アムステルダム": {"en": "Amsterdam", "km": "អាមស្ទែរដាម"},
    "ブリュッセル": {"en": "Brussels", "km": "ប្រ៊ុចសែល"},
    "ウィーン": {"en": "Vienna", "km": "វីយែន"},
    "プラハ": {"en": "Prague", "km": "ប្រាក"},
    "ワルシャワ": {"en": "Warsaw", "km": "វ៉ារស្សូវី"},
    "ブダペスト": {"en": "Budapest", "km": "ប៊ុដាប៉ែស"},
    "アテネ": {"en": "Athens", "km": "អាតែន"},
    "ストックホルム": {"en": "Stockholm", "km": "ស្តុកហូម"},
    "コペンハーゲン": {"en": "Copenhagen", "km": "កូប៉ិនហាក"},
    "オスロ": {"en": "Oslo", "km": "អូស្លូ"},
    "ダブリン": {"en": "Dublin", "km": "ឌុយប្លីន"},
    "リスボン": {"en": "Lisbon", "km": "លីសបោន"},
    "キエフ": {"en": "Kyiv", "km": "កៀវ"},
    "サンクトペテルブルク": {"en": "Saint Petersburg", "km": "សង់ពេទែរប៊ឺក"},
    "ワシントン": {"en": "Washington D.C.", "km": "វ៉ាស៊ីនតោន"},
    "ロサンゼルス": {"en": "Los Angeles", "km": "ឡូសអង់ជេលេស"},
    "シカゴ": {"en": "Chicago", "km": "ស៊ីកាហ្គោ"},
    "ヒューストン": {"en": "Houston", "km": "ហ្យូស្តុន"},
    "マイアミ": {"en": "Miami", "km": "ម៉ាយអាមី"},
    "サンフランシスコ": {"en": "San Francisco", "km": "សានហ្វ្រាន់ស៊ីស្កូ"},
    "トロント": {"en": "Toronto", "km": "តូរ៉ុនតូ"},
    "モントリオール": {"en": "Montreal", "km": "ម៉ុងរ៉េអាល់"},
    "サンパウロ": {"en": "São Paulo", "km": "សៅប៉ូឡូ"},
    "リオデジャネイロ": {"en": "Rio de Janeiro", "km": "រីយ៉ូដឺចាណេរ៉ូ"},
    "ボゴタ": {"en": "Bogotá", "km": "បូកូតា"},
    "ハバナ": {"en": "Havana", "km": "ហាវ៉ាណា"},
    "ダルエスサラーム": {"en": "Dar es Salaam", "km": "ដាអេស្សាឡាម"},
    "アクラ": {"en": "Accra", "km": "អាក្រា"},
    "アビジャン": {"en": "Abidjan", "km": "អាប៊ីចង"},
    "カサブランカ": {"en": "Casablanca", "km": "កាសាប្លង់កា"},
    "アルジェ": {"en": "Algiers", "km": "អាល់ហ្សេ"},
    "ケープタウン": {"en": "Cape Town", "km": "កេបថោន"},
    "シェムリアップ": {"en": "Siem Reap", "km": "សៀមរាប"},
    "ウラジオストク": {"en": "Vladivostok", "km": "វ្លាឌីវ៉ូស្តុក"},
    "ピョンヤン": {"en": "Pyongyang", "km": "ព្យុងយ៉ាង"},
    "ウランバートル": {"en": "Ulaanbaatar", "km": "អ៊ូឡង់បាទ័រ"},
    "デンパサール": {"en": "Denpasar", "km": "ដែនប៉ាសារ"},
    "カトマンズ": {"en": "Kathmandu", "km": "កាត់ម៉ាន់ឌូ"},
    "コロンボ": {"en": "Colombo", "km": "កូឡុំបូ"},
    "ドーハ": {"en": "Doha", "km": "ដូហា"},
    "アブダビ": {"en": "Abu Dhabi", "km": "អាប៊ុយដាប៊ី"},
    "クウェート": {"en": "Kuwait City", "km": "គុយវ៉ែត"},
    "アンマン": {"en": "Amman", "km": "អាម៉ាន"},
    "ベイルート": {"en": "Beirut", "km": "បេរូត"},
}


def _find_font(candidates):
    """候補リストから最初に見つかったフォントパスを返す"""
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def get_font(size, bold=False):
    if bold:
        candidates = [
            # macOS
            "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
            # Windows
            "C:/Windows/Fonts/meiryo.ttc",
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/YuGothB.ttc",
            # fonts/ ディレクトリ（手動配置用）
            os.path.join(os.path.dirname(__file__), "fonts", "NotoSansJP-Bold.ttf"),
        ]
    else:
        candidates = [
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "C:/Windows/Fonts/meiryo.ttc",
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/YuGothR.ttc",
            os.path.join(os.path.dirname(__file__), "fonts", "NotoSansJP-Regular.ttf"),
        ]
    path = _find_font(candidates)
    if path:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            pass
    return ImageFont.load_default()


def get_font_km(size):
    """クメール語フォント"""
    candidates = [
        # macOS
        "/System/Library/Fonts/Supplemental/Khmer MN.ttc",
        "/System/Library/Fonts/Supplemental/Khmer Sangam MN.ttf",
        # Windows (要手動インストール)
        "C:/Windows/Fonts/KhmerUI.ttf",
        "C:/Windows/Fonts/KhmerUIb.ttf",
        # fonts/ ディレクトリ（手動配置用）
        os.path.join(os.path.dirname(__file__), "fonts", "NotoSansKhmer-Regular.ttf"),
    ]
    path = _find_font(candidates)
    if path:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            pass
    return get_font(size)


def fetch_flat_map(zoom=2, width=2048, height=2048):
    # type: (int, int, int) -> Image.Image
    """OSMタイルから世界地図を取得（中心=(0,0)固定）"""
    m = StaticMap(width, height, url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png")
    # ダミーマーカー（描画されないほど小さい）
    m.add_marker(CircleMarker((0, 0), "blue", 1))
    return m.render(zoom=zoom, center=[0, 0])


def orthographic_project(flat_map, center_lon, center_lat, globe_diameter):
    # type: (Image.Image, float, float, int) -> Image.Image
    """フラットマップを正射影（地球儀風）に変換"""
    fw, fh = flat_map.size
    radius = globe_diameter // 2
    out_size = globe_diameter
    globe = Image.new("RGBA", (out_size, out_size), (0, 0, 0, 0))

    clat_r = math.radians(center_lat)
    clon_r = math.radians(center_lon)

    cos_clat = math.cos(clat_r)
    sin_clat = math.sin(clat_r)

    # フラットマップのメルカトル座標系パラメータ
    # zoom=2, center=(0,0) でレンダリングされた画像
    # Web Mercator: world_size = 256 * 2^zoom
    zoom = 2
    world_size = 256 * (2 ** zoom)  # 1024
    # 中心は (0,0) なので world の中心ピクセル
    cx_world = world_size / 2.0
    cy_world = world_size / 2.0
    # 画像の中心ピクセル
    cx_img = fw / 2.0
    cy_img = fh / 2.0

    for py in range(out_size):
        for px in range(out_size):
            nx = (px - radius) / radius
            ny = (radius - py) / radius

            dist2 = nx * nx + ny * ny
            if dist2 > 1.0:
                continue

            nz = math.sqrt(1.0 - dist2)

            lat = math.asin(ny * cos_clat + nz * sin_clat)
            lon = clon_r + math.atan2(
                nx,
                nz * cos_clat - ny * sin_clat
            )

            lat_d = math.degrees(lat)
            lon_d = math.degrees(lon)

            while lon_d > 180:
                lon_d -= 360
            while lon_d < -180:
                lon_d += 360

            # Web Mercator ピクセル座標
            x_world = (lon_d + 180) / 360 * world_size
            lat_clamped = max(min(lat_d, 85.05), -85.05)
            lat_rad = math.radians(lat_clamped)
            y_world = (1 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2 * world_size

            # world座標 -> 画像ピクセル座標
            sx = int(x_world - cx_world + cx_img)
            sy = int(y_world - cy_world + cy_img)

            if sx < 0 or sx >= fw or sy < 0 or sy >= fh:
                continue

            color = flat_map.getpixel((sx, sy))
            if isinstance(color, int):
                color = (color, color, color)
            if len(color) == 3:
                color = color + (255,)

            edge_factor = 1.0 - dist2 * 0.3
            color = (
                int(color[0] * edge_factor),
                int(color[1] * edge_factor),
                int(color[2] * edge_factor),
                color[3]
            )

            globe.putpixel((px, py), color)

    return globe


def lonlat_to_globe_pixel(lon, lat, center_lon, center_lat, globe_diameter):
    # type: (float, float, float, float, int) -> Tuple[Optional[Tuple[int, int]], bool]
    """経緯度を地球儀上のピクセル座標に変換。
    戻り値: (ピクセル座標, 表面かどうか)
    裏面の場合も方向を示す縁外の座標を返す。
    """
    radius = globe_diameter // 2

    clat_r = math.radians(center_lat)
    clon_r = math.radians(center_lon)
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)

    dlon = lon_r - clon_r

    cos_c = math.sin(clat_r) * math.sin(lat_r) + \
            math.cos(clat_r) * math.cos(lat_r) * math.cos(dlon)

    x = math.cos(lat_r) * math.sin(dlon)
    y = math.cos(clat_r) * math.sin(lat_r) - \
        math.sin(clat_r) * math.cos(lat_r) * math.cos(dlon)

    if cos_c >= 0:
        # 表面
        px = int(radius + x * radius)
        py = int(radius - y * radius)
        return ((px, py), True)
    else:
        # 裏面 → 方向を計算して縁の外に配置
        dist = math.sqrt(x * x + y * y)
        if dist < 0.001:
            # 真裏 → 下方向に配置
            nx, ny = 0.0, -1.0
        else:
            nx = x / dist
            ny = -y / dist  # y反転

        # 地球儀の縁から少し外（40px離す）
        offset = radius + 40
        px = int(radius + nx * offset)
        py = int(radius + ny * offset)
        return ((px, py), False)


def draw_flag_jp(draw, cx, cy, size=20):
    """日の丸を描画"""
    fw, fh = int(size * 1.5), size
    x0 = cx - fw // 2
    y0 = cy - fh - 10
    # ポール
    draw.line([(cx, cy), (cx, y0 + fh)], fill=(100, 100, 100), width=2)
    # 旗
    draw.rectangle([x0, y0, x0 + fw, y0 + fh], fill=COLOR_WHITE, outline=(100, 100, 100))
    r = min(fw, fh) // 3
    draw.ellipse([x0 + fw // 2 - r, y0 + fh // 2 - r,
                  x0 + fw // 2 + r, y0 + fh // 2 + r], fill=(188, 0, 45))


def draw_flag_kh(draw, cx, cy, size=20):
    """カンボジア国旗（青赤青＋アンコールワット）"""
    fw, fh = int(size * 1.5), size
    x0 = cx - fw // 2
    y0 = cy - fh - 10
    # ポール
    draw.line([(cx, cy), (cx, y0 + fh)], fill=(100, 100, 100), width=2)
    # 青赤青の帯（比率 1:2:1）
    h4 = fh // 4
    draw.rectangle([x0, y0, x0 + fw, y0 + h4], fill=(3, 46, 161))
    draw.rectangle([x0, y0 + h4, x0 + fw, y0 + h4 * 3], fill=(224, 0, 37))
    draw.rectangle([x0, y0 + h4 * 3, x0 + fw, y0 + fh], fill=(3, 46, 161))

    # アンコールワット（赤帯の中央に白で描画）
    acx = x0 + fw // 2
    red_top = y0 + h4
    red_bot = y0 + h4 * 3
    red_h = red_bot - red_top
    base_y = red_bot - int(red_h * 0.2)  # 土台の上端
    base_w = int(fw * 0.55)

    # 土台
    draw.rectangle([acx - base_w // 2, base_y, acx + base_w // 2, base_y + 2], fill=COLOR_WHITE)

    # 中央塔（一番高い）
    tw = max(2, int(fw * 0.06))
    th = int(red_h * 0.55)
    draw.rectangle([acx - tw, base_y - th, acx + tw, base_y], fill=COLOR_WHITE)
    # 中央塔の尖塔
    draw.polygon([(acx - tw - 1, base_y - th),
                  (acx, base_y - th - int(red_h * 0.15)),
                  (acx + tw + 1, base_y - th)], fill=COLOR_WHITE)

    # 左右の塔
    side_offset = int(fw * 0.15)
    sth = int(red_h * 0.35)
    stw = max(1, int(fw * 0.04))
    for dx in [-side_offset, side_offset]:
        tx = acx + dx
        draw.rectangle([tx - stw, base_y - sth, tx + stw, base_y], fill=COLOR_WHITE)
        # 尖塔
        draw.polygon([(tx - stw - 1, base_y - sth),
                      (tx, base_y - sth - int(red_h * 0.1)),
                      (tx + stw + 1, base_y - sth)], fill=COLOR_WHITE)

    # 枠
    draw.rectangle([x0, y0, x0 + fw, y0 + fh], outline=(100, 100, 100))


def generate_map(city_name, output_dir="."):
    # type: (str, str) -> str

    city_coord = geocode_city(city_name)
    print("都市: {} -> lon={:.4f}, lat={:.4f}".format(city_name, city_coord[0], city_coord[1]))

    # 1. OSMタイルでフラットマップ取得
    print("タイル取得中...")
    flat_map = fetch_flat_map(zoom=2, width=2048, height=2048)

    # 2. 正射影で地球儀に変換
    print("地球儀レンダリング中...")
    globe = orthographic_project(flat_map, city_coord[0], city_coord[1], GLOBE_SIZE)

    # 3. 最終画像に合成
    img = Image.new("RGB", (IMG_W, IMG_H), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # 地球儀を中央に配置
    globe_x = (IMG_W - GLOBE_SIZE) // 2
    globe_y = 170

    # === 星空 ===
    # 都市名をシードにして毎回同じ星配置にする
    seed = int(hashlib.md5(city_name.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    globe_center_x = globe_x + GLOBE_SIZE // 2
    globe_center_y = globe_y + GLOBE_SIZE // 2
    globe_r_sq = (GLOBE_SIZE // 2 + 10) ** 2

    for _ in range(120):
        sx = rng.randint(10, IMG_W - 10)
        sy = rng.randint(140, 890)
        # 地球儀の内側には描かない
        dx = sx - globe_center_x
        dy = sy - globe_center_y
        if dx * dx + dy * dy < globe_r_sq:
            continue
        brightness = rng.randint(120, 255)
        size = rng.choice([1, 1, 1, 2, 2, 3])
        c = (brightness, brightness, brightness)
        if size == 1:
            draw.point((sx, sy), fill=c)
        else:
            draw.ellipse([sx - size // 2, sy - size // 2,
                          sx + size // 2, sy + size // 2], fill=c)

    # === 月（約30%の確率で表示）===
    if rng.random() < 0.3:
        # 地球儀と被らない位置に配置
        for _ in range(20):
            mx = rng.randint(40, IMG_W - 80)
            my = rng.randint(150, 500)
            mdx = mx - globe_center_x
            mdy = my - globe_center_y
            if mdx * mdx + mdy * mdy > (GLOBE_SIZE // 2 + 60) ** 2:
                break
        moon_r = rng.randint(15, 25)
        # 三日月風: 大きい円を描いてから少しずらした暗い円で削る
        moon_img = Image.new("RGBA", (moon_r * 3, moon_r * 3), (0, 0, 0, 0))
        moon_draw = ImageDraw.Draw(moon_img)
        mc = moon_r * 3 // 2
        # 月本体（淡い黄色）
        moon_draw.ellipse([mc - moon_r, mc - moon_r, mc + moon_r, mc + moon_r],
                          fill=(230, 220, 180, 200))
        # 影で三日月に
        offset = int(moon_r * 0.6)
        moon_draw.ellipse([mc - moon_r + offset, mc - moon_r - 2,
                           mc + moon_r + offset, mc + moon_r + 2],
                          fill=(0, 0, 0, 0))
        img.paste(moon_img, (mx - mc, my - mc), moon_img)

    # 地球儀の影（リング）
    shadow_draw = ImageDraw.Draw(img)
    for i in range(8, 0, -1):
        alpha = 30 - i * 3
        c = (max(0, COLOR_BG[0] + alpha), max(0, COLOR_BG[1] + alpha), max(0, COLOR_BG[2] + alpha))
        shadow_draw.ellipse([
            globe_x - i, globe_y - i,
            globe_x + GLOBE_SIZE + i, globe_y + GLOBE_SIZE + i
        ], outline=c, width=2)

    img.paste(globe, (globe_x, globe_y), globe)

    # 地球儀のリムライト（円弧）
    draw.ellipse([
        globe_x - 1, globe_y - 1,
        globe_x + GLOBE_SIZE + 1, globe_y + GLOBE_SIZE + 1
    ], outline=COLOR_OCEAN_RING, width=2)

    # === マーカーと旗 ===
    globe_radius = GLOBE_SIZE // 2
    globe_cx = globe_x + globe_radius
    globe_cy = globe_y + globe_radius

    # 各ポイントの座標と表裏を取得
    city_gp, city_visible = lonlat_to_globe_pixel(
        city_coord[0], city_coord[1], city_coord[0], city_coord[1], GLOBE_SIZE)
    jp_gp, jp_visible = lonlat_to_globe_pixel(
        JAPAN_COORD[0], JAPAN_COORD[1], city_coord[0], city_coord[1], GLOBE_SIZE)
    kh_gp, kh_visible = lonlat_to_globe_pixel(
        CAMBODIA_COORD[0], CAMBODIA_COORD[1], city_coord[0], city_coord[1], GLOBE_SIZE)

    # 都市マーカー（常に表面＝中心）
    cx = globe_x + city_gp[0]
    cy = globe_y + city_gp[1]
    r = 10
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=COLOR_CITY, outline=COLOR_WHITE, width=2)

    # 日本
    jx = globe_x + jp_gp[0]
    jy = globe_y + jp_gp[1]
    if jp_visible:
        draw.ellipse([jx - 6, jy - 6, jx + 6, jy + 6], fill=(0, 82, 165), outline=COLOR_WHITE, width=2)
    draw_flag_jp(draw, jx, jy)
    draw_dashed_line(draw, (cx, cy), (jx, jy), (200, 200, 200), width=1)

    # カンボジア
    kx = globe_x + kh_gp[0]
    ky = globe_y + kh_gp[1]
    if kh_visible:
        draw.ellipse([kx - 6, ky - 6, kx + 6, ky + 6], fill=(0, 82, 165), outline=COLOR_WHITE, width=2)
    draw_flag_kh(draw, kx, ky)
    draw_dashed_line(draw, (cx, cy), (kx, ky), (200, 200, 200), width=1)


    # === ヘッダー ===
    font_title = get_font(36, bold=True)
    font_title_km = get_font_km(28)
    font_sub = get_font(18)

    city_info = CITY_NAME_MAP.get(city_name, {})
    km_name = city_info.get("km", "")

    draw.text((40, 40), city_name, fill=COLOR_TEXT, font=font_title)
    tw = draw.textlength(city_name, font=font_title)
    ja_right = 40 + tw
    if km_name:
        draw.text((ja_right + 20, 48), km_name, fill=(180, 180, 180), font=font_title_km)
    draw.text((40, 100), "Japan & Cambodia", fill=(100, 160, 210), font=font_sub)

    # === ラベル ===
    font_label = get_font(14, bold=True)
    font_label_km = get_font_km(12)
    km_name2 = CITY_NAME_MAP.get(city_name, {}).get("km", "")

    # 都市ラベル
    lbl = city_name
    if km_name2:
        lbl = city_name + "  "
    draw.text((cx + 14, cy - 8), lbl, fill=COLOR_CITY, font=font_label)
    if km_name2:
        lw = draw.textlength(lbl, font=font_label)
        draw.text((cx + 14 + lw, cy - 6), km_name2, fill=(255, 120, 120), font=font_label_km)

    # 日本ラベル
    draw.text((jx + 14, jy - 8), "日本  ", fill=COLOR_WHITE, font=font_label)
    jw = draw.textlength("日本  ", font=font_label)
    draw.text((jx + 14 + jw, jy - 6), "ជប៉ុន", fill=(180, 180, 180), font=font_label_km)

    # カンボジアラベル
    draw.text((kx + 14, ky - 8), "カンボジア  ", fill=COLOR_WHITE, font=font_label)
    kw = draw.textlength("カンボジア  ", font=font_label)
    draw.text((kx + 14 + kw, ky - 6), "កម្ពុជា", fill=(180, 180, 180), font=font_label_km)

    # === フッター（クレジット）===
    draw.rectangle([0, 900, IMG_W, IMG_H], fill=COLOR_WHITE)
    font_credit = get_font(11)
    draw.text((30, 920), "Map tiles: OpenStreetMap contributors", fill=(120, 120, 120), font=font_credit)
    draw.text((30, 940), "Generated by mapgen.py", fill=(150, 150, 150), font=font_credit)

    # === 保存 ===
    output_path = Path(output_dir) / "map_{}.png".format(city_name)
    img.save(str(output_path), optimize=True)
    fsize = os.path.getsize(str(output_path))
    print("保存: {} ({:.1f} KB)".format(output_path, fsize / 1024))

    # バグダッドの前回テスト用ファイルも消す
    alt_name = CITY_NAME_MAP.get(city_name, {}).get("en", "")
    if alt_name:
        alt_path = Path(output_dir) / "map_{}.png".format(alt_name)
        if alt_path.exists() and str(alt_path) != str(output_path):
            alt_path.unlink()

    return str(output_path)


def draw_dashed_line(draw, p1, p2, color, width=2, dash_len=8):
    """直線の破線を描画"""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dist = math.sqrt(dx * dx + dy * dy)
    if dist == 0:
        return
    steps = int(dist / dash_len)
    if steps == 0:
        return
    for i in range(0, steps, 2):
        t1 = i / steps
        t2 = min((i + 1) / steps, 1.0)
        x1 = int(p1[0] + dx * t1)
        y1 = int(p1[1] + dy * t1)
        x2 = int(p1[0] + dx * t2)
        y2 = int(p1[1] + dy * t2)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)


def great_circle_points(lon1, lat1, lon2, lat2, n=80):
    """2点間の大圏航路上の中間点を返す (lon, lat) のリスト"""
    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lat2_r = math.radians(lat2)
    lon2_r = math.radians(lon2)

    # 角距離
    d = math.acos(
        max(-1.0, min(1.0,
            math.sin(lat1_r) * math.sin(lat2_r) +
            math.cos(lat1_r) * math.cos(lat2_r) * math.cos(lon2_r - lon1_r)
        ))
    )
    if d < 0.001:
        return [(lon1, lat1), (lon2, lat2)]

    points = []
    for i in range(n + 1):
        f = i / n
        a = math.sin((1 - f) * d) / math.sin(d)
        b = math.sin(f * d) / math.sin(d)
        x = a * math.cos(lat1_r) * math.cos(lon1_r) + b * math.cos(lat2_r) * math.cos(lon2_r)
        y = a * math.cos(lat1_r) * math.sin(lon1_r) + b * math.cos(lat2_r) * math.sin(lon2_r)
        z = a * math.sin(lat1_r) + b * math.sin(lat2_r)
        lat = math.degrees(math.atan2(z, math.sqrt(x * x + y * y)))
        lon = math.degrees(math.atan2(y, x))
        points.append((lon, lat))
    return points


def draw_great_circle_line(draw, lon1, lat1, lon2, lat2,
                           center_lon, center_lat, globe_diameter,
                           globe_x, globe_y, color, width=2, dash_len=8):
    """大圏航路に沿った破線を地球儀上に描画（表面部分のみ）"""
    points = great_circle_points(lon1, lat1, lon2, lat2, n=80)

    # 各点を地球儀座標に変換（表面のみ）
    projected = []
    for lon, lat in points:
        gp, visible = lonlat_to_globe_pixel(lon, lat, center_lon, center_lat, globe_diameter)
        if visible:
            projected.append((globe_x + gp[0], globe_y + gp[1]))
        else:
            projected.append(None)  # 裏面

    # 表面の連続セグメントを破線で描画
    segment = []
    for pt in projected:
        if pt is not None:
            segment.append(pt)
        else:
            if len(segment) >= 2:
                _draw_polyline_dashed(draw, segment, color, width, dash_len)
            segment = []
    if len(segment) >= 2:
        _draw_polyline_dashed(draw, segment, color, width, dash_len)


def _draw_polyline_dashed(draw, points, color, width=2, dash_len=8):
    """ポリライン（点列）を破線で描画"""
    total_dist = 0
    drawing = True
    since_toggle = 0.0

    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        seg_dx = x2 - x1
        seg_dy = y2 - y1
        seg_dist = math.sqrt(seg_dx * seg_dx + seg_dy * seg_dy)
        if seg_dist < 0.5:
            continue

        consumed = 0.0
        while consumed < seg_dist:
            remain_in_dash = dash_len - since_toggle
            remain_in_seg = seg_dist - consumed
            step = min(remain_in_dash, remain_in_seg)

            if drawing:
                t1 = consumed / seg_dist
                t2 = (consumed + step) / seg_dist
                px1 = int(x1 + seg_dx * t1)
                py1 = int(y1 + seg_dy * t1)
                px2 = int(x1 + seg_dx * t2)
                py2 = int(y1 + seg_dy * t2)
                draw.line([(px1, py1), (px2, py2)], fill=color, width=width)

            consumed += step
            since_toggle += step
            if since_toggle >= dash_len:
                drawing = not drawing
                since_toggle = 0.0


def _find_edge_point(lon1, lat1, lon2, lat2,
                     center_lon, center_lat, globe_diameter,
                     globe_x, globe_y):
    """大圏航路上で、表面→裏面に切り替わる縁のピクセル座標を返す"""
    points = great_circle_points(lon1, lat1, lon2, lat2, n=200)
    last_visible = None
    for lon, lat in points:
        gp, visible = lonlat_to_globe_pixel(lon, lat, center_lon, center_lat, globe_diameter)
        if visible:
            last_visible = (globe_x + gp[0], globe_y + gp[1])
        else:
            if last_visible:
                return last_visible
    return last_visible


def upload_to_chatwork(file_path, room_id, message=""):
    # type: (str, int, str) -> Optional[str]
    api_token = os.environ.get("CHATWORK_API_TOKEN", "")
    if not api_token:
        print("Error: CHATWORK_API_TOKEN 環境変数を設定してください")
        return None
    city_name = Path(file_path).stem.replace("map_", "")
    if not message:
        message = city_name

    cmd = [
        "curl", "-s", "-X", "POST",
        "-H", "X-ChatWorkToken: {}".format(api_token),
        "-F", "file=@{}".format(file_path),
        "-F", "message={}".format(message),
        "https://api.chatwork.com/v2/rooms/{}/files".format(room_id),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("Chatwork upload: {}".format(result.stdout.strip()))
    return result.stdout.strip()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="地球儀風地図画像を生成")
    parser.add_argument("city", help="都市名（日本語 or 英語）")
    parser.add_argument("--output", "-o", default=".", help="出力先ディレクトリ")
    parser.add_argument("--upload", "-u", type=int, help="ChatworkルームIDを指定してアップロード")
    parser.add_argument("--message", "-m", default="", help="アップロード時のメッセージ")
    args = parser.parse_args()

    path = generate_map(args.city, args.output)

    if args.upload:
        upload_to_chatwork(path, args.upload, args.message)
