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
GLOBE_SIZE = 770         # 地球儀の直径
IMG_W = 960
IMG_H = 965

# 固定座標 (lon, lat)
JAPAN_COORD = (139.6917, 35.6895)
CAMBODIA_COORD = (104.9160, 11.5564)

# 色パレット
COLOR_BG = (12, 18, 40)
COLOR_OCEAN_RING = (40, 80, 130)
COLOR_TEXT = (230, 230, 230)
COLOR_CITY = (255, 50, 50)
COLOR_WHITE = (255, 255, 255)


def geocode_city(city_name):
    # type: (str) -> Tuple[float, float]
    """都市名から座標を取得。CITY_NAME_MAPの事前登録座標を優先"""
    info = CITY_NAME_MAP.get(city_name, {})
    if "lon" in info and "lat" in info:
        return (info["lon"], info["lat"])
    # フォールバック: Nominatimで検索
    geolocator = Nominatim(user_agent="mapgen-app")
    location = geolocator.geocode(city_name)
    if location:
        return (location.longitude, location.latitude)
    location = geolocator.geocode(city_name, language="ja")
    if location:
        return (location.longitude, location.latitude)
    en_name = info.get("en")
    if en_name:
        location = geolocator.geocode(en_name)
        if location:
            return (location.longitude, location.latitude)
    raise ValueError("都市が見つかりません: {}".format(city_name))


# 都市名マッピング（日本語 -> 英語, クメール語, UTC, 日本までの距離km, カンボジアまでの距離km）
CITY_NAME_MAP = {
    # === UTC-11 ===
    "パゴパゴ": {"en": "Pago Pago", "country": "American Samoa", "km": "ប៉ាហ្គោប៉ាហ្គោ", "utc": -11, "dist_jp": 7618, "dist_kh": 9730, "lon": -170.7, "lat": -14.27},
    # === UTC-10 ===
    "ハワイ": {"en": "Honolulu, Hawaii", "country": "USA", "km": "ហាវ៉ៃ", "utc": -10, "dist_jp": 6205, "dist_kh": 10275, "lon": -157.86, "lat": 21.31},
    "ヒロ": {"en": "Hilo, Hawaii", "country": "USA", "km": "ហីឡូ", "utc": -10, "dist_jp": 6543, "dist_kh": 10597, "lon": -155.09, "lat": 19.72},
    # === UTC-9 ===
    "アラスカ": {"en": "Anchorage, Alaska", "country": "USA", "km": "អាឡាស្កា", "utc": -9, "dist_jp": 5563, "dist_kh": 9676, "lon": -149.9, "lat": 61.22},
    "アンカレジ": {"en": "Anchorage", "country": "USA", "km": "អានករ៉ាស", "utc": -9, "dist_jp": 5563, "dist_kh": 9676, "lon": -149.9, "lat": 61.22},
    "フェアバンクス": {"en": "Fairbanks", "country": "USA", "km": "ហ្វែរបែនក្ស", "utc": -9, "dist_jp": 5654, "dist_kh": 9644, "lon": -147.72, "lat": 64.84},
    "ジュノー": {"en": "Juneau", "country": "USA", "km": "ជូណូ", "utc": -9, "dist_jp": 6472, "dist_kh": 10595, "lon": -134.42, "lat": 58.3},
    "ノーム": {"en": "Nome, Alaska", "country": "USA", "km": "ណូម", "utc": -9, "dist_jp": 4816, "dist_kh": 8834, "lon": -165.41, "lat": 64.5},
    # === UTC-8 ===
    "ロサンゼルス": {"en": "Los Angeles", "country": "USA", "km": "ឡូសអង់ជេលេស", "utc": -8, "dist_jp": 8816, "dist_kh": 13197, "lon": -118.24, "lat": 34.05},
    "サンフランシスコ": {"en": "San Francisco", "country": "USA", "km": "សានហ្វ្រាន់ស៊ីស្កូ", "utc": -8, "dist_jp": 8271, "dist_kh": 12644, "lon": -122.42, "lat": 37.77},
    "バンクーバー": {"en": "Vancouver", "country": "Canada", "km": "វ៉ាន់គូវ័រ", "utc": -8, "dist_jp": 7553, "dist_kh": 11786, "lon": -123.12, "lat": 49.28},
    "シアトル": {"en": "Seattle", "country": "USA", "km": "ស៊ីអាថល", "utc": -8, "dist_jp": 7696, "dist_kh": 11952, "lon": -122.33, "lat": 47.61},
    "サンディエゴ": {"en": "San Diego", "country": "USA", "km": "សានឌីអេហ្គោ", "utc": -8, "dist_jp": 8984, "dist_kh": 13369, "lon": -117.16, "lat": 32.72},
    "ラスベガス": {"en": "Las Vegas", "country": "USA", "km": "ឡាសវេហ្គាស", "utc": -8, "dist_jp": 8901, "dist_kh": 13249, "lon": -115.14, "lat": 36.17},
    "ポートランド": {"en": "Portland", "country": "USA", "km": "ផតលែន", "utc": -8, "dist_jp": 7793, "dist_kh": 12083, "lon": -122.68, "lat": 45.52},
    "ティフアナ": {"en": "Tijuana", "country": "Mexico", "km": "ទីហ្វាណា", "utc": -8, "dist_jp": 9006, "dist_kh": 13392, "lon": -117.04, "lat": 32.53},
    # === UTC-7 ===
    "デンバー": {"en": "Denver", "country": "USA", "km": "ដេនវើ", "utc": -7, "dist_jp": 9332, "dist_kh": 13529, "lon": -104.99, "lat": 39.74},
    "フェニックス": {"en": "Phoenix", "country": "USA", "km": "ភីនិច", "utc": -7, "dist_jp": 9309, "dist_kh": 13661, "lon": -112.07, "lat": 33.45},
    "ソルトレイクシティ": {"en": "Salt Lake City", "country": "USA", "km": "សលថ៍ឡេកស៊ីធី", "utc": -7, "dist_jp": 8812, "dist_kh": 13077, "lon": -111.89, "lat": 40.76},
    "エルパソ": {"en": "El Paso", "country": "USA", "km": "អែលផាសូ", "utc": -7, "dist_jp": 9831, "dist_kh": 14155, "lon": -106.44, "lat": 31.76},
    "カルガリー": {"en": "Calgary", "country": "Canada", "km": "កាល់ហ្គារី", "utc": -7, "dist_jp": 7993, "dist_kh": 12103, "lon": -114.07, "lat": 51.05},
    "エドモントン": {"en": "Edmonton", "country": "Canada", "km": "អេដម៉ុនតុន", "utc": -7, "dist_jp": 7868, "dist_kh": 11916, "lon": -113.49, "lat": 53.54},
    # === UTC-6 ===
    "メキシコシティ": {"en": "Mexico City", "country": "Mexico", "km": "ម៉ិចស៊ីកូស៊ីធី", "utc": -6, "dist_jp": 11306, "dist_kh": 15678, "lon": -99.13, "lat": 19.43},
    "シカゴ": {"en": "Chicago", "country": "USA", "km": "ស៊ីកាហ្គោ", "utc": -6, "dist_jp": 10138, "dist_kh": 13936, "lon": -87.63, "lat": 41.88},
    "ヒューストン": {"en": "Houston", "country": "USA", "km": "ហ្យូស្តុន", "utc": -6, "dist_jp": 10737, "dist_kh": 14933, "lon": -95.37, "lat": 29.76},
    "ダラス": {"en": "Dallas", "country": "USA", "km": "ដាឡាស", "utc": -6, "dist_jp": 10397, "dist_kh": 14573, "lon": -96.8, "lat": 32.78},
    "グアテマラシティ": {"en": "Guatemala City", "country": "Guatemala", "km": "ក្វាតេម៉ាឡា", "utc": -6, "dist_jp": 12323, "dist_kh": 16642, "lon": -90.53, "lat": 14.63},
    "サンサルバドル": {"en": "San Salvador", "country": "El Salvador", "km": "សានសាល់វ៉ាឌ័រ", "utc": -6, "dist_jp": 12497, "dist_kh": 16806, "lon": -89.19, "lat": 13.69},
    "テグシガルパ": {"en": "Tegucigalpa", "country": "Honduras", "km": "តេហ្គូស៊ីហ្គាល់ប៉ា", "utc": -6, "dist_jp": 12604, "dist_kh": 16867, "lon": -87.22, "lat": 14.07},
    "ウィニペグ": {"en": "Winnipeg", "country": "Canada", "km": "វីនីភែក", "utc": -6, "dist_jp": 8984, "dist_kh": 12851, "lon": -97.14, "lat": 49.9},
    # === UTC-5 ===
    "アトランタ": {"en": "Atlanta", "country": "USA", "km": "អាត្លង់តា", "utc": -5, "dist_jp": 11038, "dist_kh": 14882, "lon": -84.39, "lat": 33.75},
    "ボストン": {"en": "Boston", "country": "USA", "km": "បូស្តុន", "utc": -5, "dist_jp": 10791, "dist_kh": 14006, "lon": -71.06, "lat": 42.36},
    "フィラデルフィア": {"en": "Philadelphia", "country": "USA", "km": "ភីឡាដែលភៀ", "utc": -5, "dist_jp": 10879, "dist_kh": 14288, "lon": -75.17, "lat": 39.95},
    "デトロイト": {"en": "Detroit", "country": "USA", "km": "ឌេត្រ៉យ", "utc": -5, "dist_jp": 10314, "dist_kh": 13968, "lon": -83.05, "lat": 42.33},
    "メデジン": {"en": "Medellín", "country": "Colombia", "km": "មេដេយីន", "utc": -5, "dist_jp": 14074, "dist_kh": 18034, "lon": -75.56, "lat": 6.25},
    "ニューヨーク": {"en": "New York", "country": "USA", "km": "ញូវយ៉ក", "utc": -5, "dist_jp": 10849, "dist_kh": 14202, "lon": -74.01, "lat": 40.71},
    "ワシントン": {"en": "Washington D.C.", "country": "USA", "km": "វ៉ាស៊ីនតោន", "utc": -5, "dist_jp": 10903, "dist_kh": 14400, "lon": -77.04, "lat": 38.91},
    "マイアミ": {"en": "Miami", "country": "USA", "km": "ម៉ាយអាមី", "utc": -5, "dist_jp": 12001, "dist_kh": 15829, "lon": -80.19, "lat": 25.76},
    "トロント": {"en": "Toronto", "country": "Canada", "km": "តូរ៉ុនតូ", "utc": -5, "dist_jp": 10349, "dist_kh": 13861, "lon": -79.38, "lat": 43.65},
    "モントリオール": {"en": "Montreal", "country": "Canada", "km": "ម៉ុងរ៉េអាល់", "utc": -5, "dist_jp": 10389, "dist_kh": 13669, "lon": -73.57, "lat": 45.5},
    "ハバナ": {"en": "Havana", "country": "Cuba", "km": "ហាវ៉ាណា", "utc": -5, "dist_jp": 12121, "dist_kh": 16080, "lon": -82.37, "lat": 23.11},
    "ボゴタ": {"en": "Bogotá", "country": "Colombia", "km": "បូកូតា", "utc": -5, "dist_jp": 14309, "dist_kh": 18203, "lon": -74.07, "lat": 4.71},
    "リマ": {"en": "Lima", "country": "Peru", "km": "លីម៉ា", "utc": -5, "dist_jp": 15492, "dist_kh": 19795, "lon": -77.04, "lat": -12.05},
    "パナマシティ": {"en": "Panama City", "country": "Panama", "km": "ប៉ាណាម៉ា", "utc": -5, "dist_jp": 13570, "dist_kh": 17679, "lon": -79.52, "lat": 8.98},
    "キト": {"en": "Quito", "country": "Ecuador", "km": "គីតូ", "utc": -5, "dist_jp": 14436, "dist_kh": 18696, "lon": -78.47, "lat": -0.18},
    # === UTC-4 ===
    "カラカス": {"en": "Caracas", "country": "Venezuela", "km": "ការ៉ាកាស", "utc": -4, "dist_jp": 14172, "dist_kh": 17403, "lon": -66.9, "lat": 10.48},
    "サントドミンゴ": {"en": "Santo Domingo", "country": "Dominican Republic", "km": "សាន់តូដូមីងហ្គោ", "utc": -4, "dist_jp": 13233, "dist_kh": 16629, "lon": -69.93, "lat": 18.47},
    "サンフアン": {"en": "San Juan", "country": "Puerto Rico", "km": "សានហ្វាន", "utc": -4, "dist_jp": 13408, "dist_kh": 16534, "lon": -66.11, "lat": 18.47},
    "ラパス": {"en": "La Paz", "country": "Bolivia", "km": "ឡាប៉ាស", "utc": -4, "dist_jp": 16533, "dist_kh": 19087, "lon": -68.15, "lat": -16.5},
    "マナウス": {"en": "Manaus", "country": "Brazil", "km": "ម៉ាណាអូស", "utc": -4, "dist_jp": 15864, "dist_kh": 18110, "lon": -60.03, "lat": -3.12},
    "ハリファックス": {"en": "Halifax", "country": "Canada", "km": "ហាលីហ្វាក់ស", "utc": -4, "dist_jp": 10779, "dist_kh": 13658, "lon": -63.57, "lat": 44.65},
    # === UTC-3 ===
    "アスンシオン": {"en": "Asunción", "country": "Paraguay", "km": "អាសុនស៊ីយ៉ុង", "utc": -3, "dist_jp": 17999, "dist_kh": 17626, "lon": -57.58, "lat": -25.26},
    "サンパウロ": {"en": "São Paulo", "country": "Brazil", "km": "សៅប៉ូឡូ", "utc": -3, "dist_jp": 18534, "dist_kh": 16726, "lon": -46.63, "lat": -23.55},
    "リオデジャネイロ": {"en": "Rio de Janeiro", "country": "Brazil", "km": "រីយ៉ូដឺចាណេរ៉ូ", "utc": -3, "dist_jp": 18567, "dist_kh": 16409, "lon": -43.17, "lat": -22.91},
    "ブエノスアイレス": {"en": "Buenos Aires", "country": "Argentina", "km": "ប៊ុយណូស៍អាយ៉េស", "utc": -3, "dist_jp": 18370, "dist_kh": 16946, "lon": -58.38, "lat": -34.6},
    "サンティアゴ": {"en": "Santiago", "country": "Chile", "km": "សាន់ទីអាហ្គោ", "utc": -3, "dist_jp": 17235, "dist_kh": 17540, "lon": -70.67, "lat": -33.45},
    "モンテビデオ": {"en": "Montevideo", "country": "Uruguay", "km": "ម៉ុងតេវីដេអូ", "utc": -3, "dist_jp": 18575, "dist_kh": 16793, "lon": -56.16, "lat": -34.88},
    "ブラジリア": {"en": "Brasília", "country": "Brazil", "km": "ប្រាស៊ីលីអា", "utc": -3, "dist_jp": 17677, "dist_kh": 17046, "lon": -47.93, "lat": -15.79},
    # === UTC-2 ===
    "フェルナンドデノローニャ": {"en": "Fernando de Noronha", "country": "Brazil", "km": "ហ្វែរណង់ដូដឺណូរ៉ូញ៉ា", "utc": -2, "dist_jp": 16383, "dist_kh": 15242, "lon": -32.42, "lat": -3.85},
    # === UTC-1 ===
    "プライア": {"en": "Praia", "country": "Cape Verde", "km": "ប្រាយ៉ា", "utc": -1, "dist_jp": 14115, "dist_kh": 13617, "lon": -23.51, "lat": 14.93},
    "アゾレス": {"en": "Ponta Delgada", "country": "Portugal", "km": "អាសូរេស", "utc": -1, "dist_jp": 11712, "dist_kh": 12501, "lon": -25.67, "lat": 37.74},
    # === UTC+0 ===
    "エディンバラ": {"en": "Edinburgh", "country": "UK", "km": "អេឌីនបឺក", "utc": 0, "dist_jp": 9236, "dist_kh": 10036, "lon": -3.19, "lat": 55.95},
    "ロンドン": {"en": "London", "country": "UK", "km": "ឡុងដ៍", "utc": 0, "dist_jp": 9559, "dist_kh": 10017, "lon": -0.13, "lat": 51.51},
    "リスボン": {"en": "Lisbon", "country": "Portugal", "km": "លីសបោន", "utc": 0, "dist_jp": 11143, "dist_kh": 11201, "lon": -9.14, "lat": 38.72},
    "ダブリン": {"en": "Dublin", "country": "Ireland", "km": "ឌុយប្លីន", "utc": 0, "dist_jp": 9585, "dist_kh": 10330, "lon": -6.26, "lat": 53.35},
    "アクラ": {"en": "Accra", "country": "Ghana", "km": "អាក្រា", "utc": 0, "dist_jp": 13807, "dist_kh": 11517, "lon": -0.19, "lat": 5.56},
    "カサブランカ": {"en": "Casablanca", "country": "Morocco", "km": "កាសាប្លង់កា", "utc": 0, "dist_jp": 11596, "dist_kh": 11301, "lon": -7.59, "lat": 33.57},
    "レイキャビク": {"en": "Reykjavik", "country": "Iceland", "km": "រេយ្គ្យាវិក", "utc": 0, "dist_jp": 8797, "dist_kh": 10492, "lon": -21.94, "lat": 64.15},
    "ダカール": {"en": "Dakar", "country": "Senegal", "km": "ដាកា", "utc": 0, "dist_jp": 13918, "dist_kh": 13027, "lon": -17.44, "lat": 14.69},
    # === UTC+1 ===
    "パリ": {"en": "Paris", "country": "France", "km": "ប៉ារីស", "utc": 1, "dist_jp": 9712, "dist_kh": 9940, "lon": 2.35, "lat": 48.86},
    "ベルリン": {"en": "Berlin", "country": "Germany", "km": "បែរឡាំង", "utc": 1, "dist_jp": 8916, "dist_kh": 9091, "lon": 13.41, "lat": 52.52},
    "マドリード": {"en": "Madrid", "country": "Spain", "km": "ម៉ាឌ្រីដ", "utc": 1, "dist_jp": 10762, "dist_kh": 10698, "lon": -3.7, "lat": 40.42},
    "ローマ": {"en": "Rome", "country": "Italy", "km": "រ៉ូម", "utc": 1, "dist_jp": 9853, "dist_kh": 9350, "lon": 12.5, "lat": 41.9},
    "ミラノ": {"en": "Milan", "country": "Italy", "km": "មីឡង់", "utc": 1, "dist_jp": 9715, "dist_kh": 9534, "lon": 9.19, "lat": 45.46},
    "アムステルダム": {"en": "Amsterdam", "country": "Netherlands", "km": "អាមស្ទែរដាម", "utc": 1, "dist_jp": 9288, "dist_kh": 9659, "lon": 4.9, "lat": 52.37},
    "ルクセンブルク": {"en": "Luxembourg", "country": "Luxembourg", "km": "លុចសំបួ", "utc": 1, "dist_jp": 9487, "dist_kh": 9653, "lon": 6.13, "lat": 49.61},
    "ブリュッセル": {"en": "Brussels", "country": "Belgium", "km": "ប្រ៊ុចសែល", "utc": 1, "dist_jp": 9448, "dist_kh": 9740, "lon": 4.35, "lat": 50.85},
    "ウィーン": {"en": "Vienna", "country": "Austria", "km": "វីយែន", "utc": 1, "dist_jp": 9128, "dist_kh": 8945, "lon": 16.37, "lat": 48.21},
    "プラハ": {"en": "Prague", "country": "Czech Republic", "km": "ប្រាក", "utc": 1, "dist_jp": 9071, "dist_kh": 9060, "lon": 14.42, "lat": 50.08},
    "ワルシャワ": {"en": "Warsaw", "country": "Poland", "km": "វ៉ារស្សូវី", "utc": 1, "dist_jp": 8579, "dist_kh": 8581, "lon": 21.01, "lat": 52.23},
    "ブダペスト": {"en": "Budapest", "country": "Hungary", "km": "ប៊ុដាប៉ែស", "utc": 1, "dist_jp": 9046, "dist_kh": 8755, "lon": 19.04, "lat": 47.5},
    "ストックホルム": {"en": "Stockholm", "country": "Sweden", "km": "ស្តុកហូម", "utc": 1, "dist_jp": 8169, "dist_kh": 8726, "lon": 18.07, "lat": 59.33},
    "コペンハーゲン": {"en": "Copenhagen", "country": "Denmark", "km": "កូប៉ិនហាក", "utc": 1, "dist_jp": 8689, "dist_kh": 9094, "lon": 12.57, "lat": 55.68},
    "オスロ": {"en": "Oslo", "country": "Norway", "km": "អូស្លូ", "utc": 1, "dist_jp": 8405, "dist_kh": 9128, "lon": 10.75, "lat": 59.91},
    "ラゴス": {"en": "Lagos", "country": "Nigeria", "km": "ឡាហ្គូស", "utc": 1, "dist_jp": 13470, "dist_kh": 11107, "lon": 3.39, "lat": 6.52},
    "キンシャサ": {"en": "Kinshasa", "country": "DR Congo", "km": "គីនស្ហាស", "utc": 1, "dist_jp": 13365, "dist_kh": 10068, "lon": 15.27, "lat": -4.44},
    "ルアンダ": {"en": "Luanda", "country": "Angola", "km": "លូអ័ន់ដា", "utc": 1, "dist_jp": 13845, "dist_kh": 10385, "lon": 13.23, "lat": -8.84},
    "アルジェ": {"en": "Algiers", "country": "Algeria", "km": "អាល់ហ្សេ", "utc": 1, "dist_jp": 10800, "dist_kh": 10271, "lon": 3.06, "lat": 36.75},
    "アビジャン": {"en": "Abidjan", "country": "Ivory Coast", "km": "អាប៊ីចង", "utc": 0, "dist_jp": 14090, "dist_kh": 11936, "lon": -4.03, "lat": 5.32},
    "チューリッヒ": {"en": "Zürich", "country": "Switzerland", "km": "ស៊ូរិច", "utc": 1, "dist_jp": 9578, "dist_kh": 9537, "lon": 8.54, "lat": 47.38},
    "ジュネーブ": {"en": "Geneva", "country": "Switzerland", "km": "ហ្សឺណែវ", "utc": 1, "dist_jp": 9793, "dist_kh": 9745, "lon": 6.14, "lat": 46.20},
    "ミュンヘン": {"en": "Munich", "country": "Germany", "km": "មុយនិច", "utc": 1, "dist_jp": 9369, "dist_kh": 9298, "lon": 11.58, "lat": 48.14},
    "フランクフルト": {"en": "Frankfurt", "country": "Germany", "km": "ហ្វ្រង់ក្វត", "utc": 1, "dist_jp": 9332, "dist_kh": 9462, "lon": 8.68, "lat": 50.11},
    "リヨン": {"en": "Lyon", "country": "France", "km": "លីយ៉ុង", "utc": 1, "dist_jp": 9891, "dist_kh": 9856, "lon": 4.83, "lat": 45.76},
    "ベオグラード": {"en": "Belgrade", "country": "Serbia", "km": "បែលក្រាដ", "utc": 1, "dist_jp": 9178, "dist_kh": 8670, "lon": 20.46, "lat": 44.82},
    "ザグレブ": {"en": "Zagreb", "country": "Croatia", "km": "សាក្រេប", "utc": 1, "dist_jp": 9343, "dist_kh": 9007, "lon": 15.98, "lat": 45.81},
    "チュニス": {"en": "Tunis", "country": "Tunisia", "km": "ទុយនីស", "utc": 1, "dist_jp": 10417, "dist_kh": 9656, "lon": 10.17, "lat": 36.81},
    "バルセロナ": {"en": "Barcelona", "country": "Spain", "km": "បាសេឡូណា", "utc": 1, "dist_jp": 10413, "dist_kh": 10197, "lon": 2.17, "lat": 41.39},
    # === UTC+2 ===
    "トリポリ": {"en": "Tripoli", "country": "Libya", "km": "ទ្រីប៉ូលី", "utc": 2, "dist_jp": 10574, "dist_kh": 9471, "lon": 13.19, "lat": 32.90},
    "ダマスカス": {"en": "Damascus", "country": "Syria", "km": "ដាម៉ាស", "utc": 2, "dist_jp": 8951, "dist_kh": 7328, "lon": 36.29, "lat": 33.51},
    "マプト": {"en": "Maputo", "country": "Mozambique", "km": "ម៉ាពូតូ", "utc": 2, "dist_jp": 13128, "dist_kh": 8858, "lon": 32.57, "lat": -25.97},
    "カイロ": {"en": "Cairo", "country": "Egypt", "km": "កែរ៉ូ", "utc": 2, "dist_jp": 9564, "dist_kh": 7806, "lon": 31.24, "lat": 30.04},
    "ヨハネスブルク": {"en": "Johannesburg", "country": "South Africa", "km": "យ៉ូហានេស្ប៊ឺក", "utc": 2, "dist_jp": 13539, "dist_kh": 9297, "lon": 28.05, "lat": -26.2},
    "ケープタウン": {"en": "Cape Town", "country": "South Africa", "km": "កេបថោន", "utc": 2, "dist_jp": 14732, "dist_kh": 10404, "lon": 18.42, "lat": -33.93},
    "イスタンブール": {"en": "Istanbul", "country": "Turkey", "km": "អ៊ីស្តង់ប៊ុល", "utc": 3, "dist_jp": 8945, "dist_kh": 7992, "lon": 28.98, "lat": 41.01},
    "アテネ": {"en": "Athens", "country": "Greece", "km": "អាតែន", "utc": 2, "dist_jp": 9505, "dist_kh": 8453, "lon": 23.73, "lat": 37.98},
    "ヘルシンキ": {"en": "Helsinki", "country": "Finland", "km": "ហែលស៊ីនគី", "utc": 2, "dist_jp": 7818, "dist_kh": 8341, "lon": 24.94, "lat": 60.17},
    "キエフ": {"en": "Kyiv", "country": "Ukraine", "km": "កៀវ", "utc": 2, "dist_jp": 8199, "dist_kh": 7917, "lon": 30.52, "lat": 50.45},
    "アンカラ": {"en": "Ankara", "country": "Turkey", "km": "អង់ការ៉ា", "utc": 3, "dist_jp": 8763, "dist_kh": 7661, "lon": 32.86, "lat": 39.93},
    "テルアビブ": {"en": "Tel Aviv", "country": "Israel", "km": "តែលអាវីវ", "utc": 2, "dist_jp": 9159, "dist_kh": 7466, "lon": 34.78, "lat": 32.09},
    "ベイルート": {"en": "Beirut", "country": "Lebanon", "km": "បេរូត", "utc": 2, "dist_jp": 8984, "dist_kh": 7402, "lon": 35.5, "lat": 33.89},
    "アンマン": {"en": "Amman", "country": "Jordan", "km": "អាម៉ាន", "utc": 2, "dist_jp": 9082, "dist_kh": 7357, "lon": 35.93, "lat": 31.95},
    "ダルエスサラーム": {"en": "Dar es Salaam", "country": "Tanzania", "km": "ដាអេស្សាឡាម", "utc": 3, "dist_jp": 11387, "dist_kh": 7541, "lon": 39.27, "lat": -6.79},
    "オデッサ": {"en": "Odessa", "country": "Ukraine", "km": "អូដេសា", "utc": 2, "dist_jp": 8455, "dist_kh": 7871, "lon": 30.73, "lat": 46.48},
    "ブカレスト": {"en": "Bucharest", "country": "Romania", "km": "ប៊ុការេស្ត", "utc": 2, "dist_jp": 8879, "dist_kh": 8226, "lon": 26.1, "lat": 44.43},
    "ハラレ": {"en": "Harare", "country": "Zimbabwe", "km": "ហារ៉ារេ", "utc": 2, "dist_jp": 12810, "dist_kh": 8739, "lon": 31.05, "lat": -17.83},
    # === UTC+3 ===
    "カンパラ": {"en": "Kampala", "country": "Uganda", "km": "កំប៉ាឡា", "utc": 3, "dist_jp": 11522, "dist_kh": 8076, "lon": 32.58, "lat": 0.35},
    "アンタナナリボ": {"en": "Antananarivo", "country": "Madagascar", "km": "អង់តាណាណារីវ៉ូ", "utc": 3, "dist_jp": 11409, "dist_kh": 7144, "lon": 47.52, "lat": -18.91},
    "サナア": {"en": "Sana'a", "country": "Yemen", "km": "សាណា", "utc": 3, "dist_jp": 9500, "dist_kh": 6559, "lon": 44.21, "lat": 15.35},
    "カザン": {"en": "Kazan", "country": "Russia", "km": "កាហ្សង់", "utc": 3, "dist_jp": 6833, "dist_kh": 6853, "lon": 49.11, "lat": 55.80},
    "モスクワ": {"en": "Moscow", "country": "Russia", "km": "មូស្គូ", "utc": 3, "dist_jp": 7478, "dist_kh": 7535, "lon": 37.62, "lat": 55.76},
    "サンクトペテルブルク": {"en": "Saint Petersburg", "country": "Russia", "km": "សង់ពេទែរប៊ឺក", "utc": 3, "dist_jp": 7594, "dist_kh": 8041, "lon": 30.32, "lat": 59.93},
    "ナイロビ": {"en": "Nairobi", "country": "Kenya", "km": "ណៃរ៉ូប៊ី", "utc": 3, "dist_jp": 11252, "dist_kh": 7655, "lon": 36.82, "lat": -1.29},
    "アディスアベバ": {"en": "Addis Ababa", "country": "Ethiopia", "km": "អាឌីស អាបេបា", "utc": 3, "dist_jp": 10395, "dist_kh": 7229, "lon": 38.75, "lat": 9.02},
    "リヤド": {"en": "Riyadh", "country": "Saudi Arabia", "km": "រីយ៉ាដ", "utc": 3, "dist_jp": 8693, "dist_kh": 6280, "lon": 46.68, "lat": 24.69},
    "ジェッダ": {"en": "Jeddah", "country": "Saudi Arabia", "km": "ជេដ្ដា", "utc": 3, "dist_jp": 9525, "dist_kh": 7049, "lon": 39.17, "lat": 21.49},
    "バグダッド": {"en": "Baghdad", "country": "Iraq", "km": "បាកដាដ", "utc": 3, "dist_jp": 8349, "dist_kh": 6578, "lon": 44.37, "lat": 33.31},
    "クウェート": {"en": "Kuwait City", "country": "Kuwait", "km": "គុយវ៉ែត", "utc": 3, "dist_jp": 8298, "dist_kh": 6190, "lon": 47.98, "lat": 29.38},
    "ドーハ": {"en": "Doha", "country": "Qatar", "km": "ដូហា", "utc": 3, "dist_jp": 8247, "dist_kh": 5796, "lon": 51.53, "lat": 25.29},
    # === UTC+3.5 ===
    "テヘラン": {"en": "Tehran", "country": "Iran", "km": "តេហេរ៉ង់", "utc": 3.5, "dist_jp": 7662, "dist_kh": 5988, "lon": 51.39, "lat": 35.69},
    # === UTC+4 ===
    "ドバイ": {"en": "Dubai", "country": "UAE", "km": "ឌូបៃ", "utc": 4, "dist_jp": 7931, "dist_kh": 5418, "lon": 55.3, "lat": 25.2},
    "アブダビ": {"en": "Abu Dhabi", "country": "UAE", "km": "អាប៊ុយដាប៊ី", "utc": 4, "dist_jp": 8055, "dist_kh": 5502, "lon": 54.37, "lat": 24.45},
    "マスカット": {"en": "Muscat", "country": "Oman", "km": "ម៉ាស្កាត់", "utc": 4, "dist_jp": 7755, "dist_kh": 5084, "lon": 58.41, "lat": 23.59},
    "バクー": {"en": "Baku", "country": "Azerbaijan", "km": "បាគូ", "utc": 4, "dist_jp": 7523, "dist_kh": 6242, "lon": 49.87, "lat": 40.41},
    "トビリシ": {"en": "Tbilisi", "country": "Georgia", "km": "តប៊ីលីស៊ី", "utc": 4, "dist_jp": 7819, "dist_kh": 6686, "lon": 44.83, "lat": 41.72},
    # === UTC+4.5 ===
    "カブール": {"en": "Kabul", "country": "Afghanistan", "km": "កាប៊ុល", "utc": 4.5, "dist_jp": 6268, "dist_kh": 4422, "lon": 69.17, "lat": 34.53},
    # === UTC+5 ===
    "カラチ": {"en": "Karachi", "country": "Pakistan", "km": "ការ៉ាជី", "utc": 5, "dist_jp": 6929, "dist_kh": 4250, "lon": 67.01, "lat": 24.86},
    "ラホール": {"en": "Lahore", "country": "Pakistan", "km": "ឡាហោរ", "utc": 5, "dist_jp": 5955, "dist_kh": 3841, "lon": 74.35, "lat": 31.55},
    "ドゥシャンベ": {"en": "Dushanbe", "country": "Tajikistan", "km": "ឌូស្ហាន់បេ", "utc": 5, "dist_jp": 6134, "dist_kh": 4667, "lon": 68.77, "lat": 38.56},
    "タシュケント": {"en": "Tashkent", "country": "Uzbekistan", "km": "តាស្ហ្គិន", "utc": 5, "dist_jp": 5990, "dist_kh": 4790, "lon": 69.28, "lat": 41.3},
    "イスラマバード": {"en": "Islamabad", "country": "Pakistan", "km": "អ៊ីស្លាម៉ាបាដ", "utc": 5, "dist_jp": 5976, "dist_kh": 4064, "lon": 73.04, "lat": 33.69},
    "エカテリンブルク": {"en": "Yekaterinburg", "country": "Russia", "km": "អេកាតេរីនប៊ឺក", "utc": 5, "dist_jp": 6124, "dist_kh": 6289, "lon": 60.6, "lat": 56.84},
    # === UTC+5.5 ===
    "デリー": {"en": "Delhi", "country": "India", "km": "ដេលី", "utc": 5.5, "dist_jp": 5837, "dist_kh": 3444, "lon": 77.21, "lat": 28.61},
    "ムンバイ": {"en": "Mumbai", "country": "India", "km": "មុំបៃ", "utc": 5.5, "dist_jp": 6724, "dist_kh": 3530, "lon": 72.88, "lat": 19.08},
    "コルカタ": {"en": "Kolkata", "country": "India", "km": "កុលកាតា", "utc": 5.5, "dist_jp": 5134, "dist_kh": 2141, "lon": 88.36, "lat": 22.57},
    "チェンナイ": {"en": "Chennai", "country": "India", "km": "ឈេន្នៃ", "utc": 5.5, "dist_jp": 6415, "dist_kh": 2682, "lon": 80.27, "lat": 13.08},
    "バンガロール": {"en": "Bangalore", "country": "India", "km": "បេនហ្គាឡូរ", "utc": 5.5, "dist_jp": 6662, "dist_kh": 2972, "lon": 77.59, "lat": 12.97},
    "コロンボ": {"en": "Colombo", "country": "Sri Lanka", "km": "កូឡុំបូ", "utc": 5.5, "dist_jp": 6850, "dist_kh": 2796, "lon": 79.86, "lat": 6.93},
    # === UTC+5.75 ===
    "カトマンズ": {"en": "Kathmandu", "country": "Nepal", "km": "កាត់ម៉ាន់ឌូ", "utc": 5.75, "dist_jp": 5154, "dist_kh": 2720, "lon": 85.32, "lat": 27.72},
    # === UTC+6 ===
    "ダッカ": {"en": "Dhaka", "country": "Bangladesh", "km": "ដាក្កា", "utc": 6, "dist_jp": 4884, "dist_kh": 2051, "lon": 90.41, "lat": 23.81},
    "アルマティ": {"en": "Almaty", "country": "Kazakhstan", "km": "អាល់ម៉ាទី", "utc": 6, "dist_jp": 5324, "dist_kh": 4432, "lon": 76.95, "lat": 43.24},
    "オムスク": {"en": "Omsk", "country": "Russia", "km": "អូមស្កិ", "utc": 6, "dist_jp": 5373, "dist_kh": 5558, "lon": 73.37, "lat": 55.0},
    "ビシュケク": {"en": "Bishkek", "country": "Kyrgyzstan", "km": "ប៊ីស្កែក", "utc": 6, "dist_jp": 5520, "dist_kh": 4546, "lon": 74.59, "lat": 42.87},
    "アスタナ": {"en": "Astana", "country": "Kazakhstan", "km": "អាស្តាណា", "utc": 6, "dist_jp": 5558, "dist_kh": 5341, "lon": 71.43, "lat": 51.13},
    # === UTC+6.5 ===
    "ネピドー": {"en": "Naypyidaw", "country": "Myanmar", "km": "ណេពីដោ", "utc": 6.5, "dist_jp": 4594, "dist_kh": 1310, "lon": 96.13, "lat": 19.76},
    "ヤンゴン": {"en": "Yangon", "country": "Myanmar", "km": "យ៉ាំងហ្គោន", "utc": 6.5, "dist_jp": 4764, "dist_kh": 1109, "lon": 96.2, "lat": 16.87},
    # === UTC+7 ===
    "バンコク": {"en": "Bangkok", "country": "Thailand", "km": "បាងកក", "utc": 7, "dist_jp": 4603, "dist_kh": 538, "lon": 100.5, "lat": 13.76},
    "プノンペン": {"en": "Phnom Penh", "country": "Cambodia", "km": "ភ្នំពេញ", "utc": 7, "dist_jp": 4403, "dist_kh": 1, "lon": 104.92, "lat": 11.56},
    "ホーチミン": {"en": "Ho Chi Minh City", "country": "Vietnam", "km": "ហូជីមីញ", "utc": 7, "dist_jp": 4327, "dist_kh": 204, "lon": 106.63, "lat": 10.82},
    "ハノイ": {"en": "Hanoi", "country": "Vietnam", "km": "ហាណូយ", "utc": 7, "dist_jp": 3665, "dist_kh": 1058, "lon": 105.85, "lat": 21.03},
    "ジャカルタ": {"en": "Jakarta", "country": "Indonesia", "km": "ចាការតា", "utc": 7, "dist_jp": 5785, "dist_kh": 1987, "lon": 106.85, "lat": -6.21},
    "ビエンチャン": {"en": "Vientiane", "country": "Laos", "km": "វៀងចន្ទន៍", "utc": 7, "dist_jp": 4137, "dist_kh": 754, "lon": 102.63, "lat": 17.97},
    "シェムリアップ": {"en": "Siem Reap", "country": "Cambodia", "km": "សៀមរាប", "utc": 7, "dist_jp": 4354, "dist_kh": 231, "lon": 103.86, "lat": 13.36},
    "ノヴォシビルスク": {"en": "Novosibirsk", "country": "Russia", "km": "ណូវ៉ូស៊ីប៊ីស្កិ", "utc": 7, "dist_jp": 4764, "dist_kh": 5201, "lon": 82.93, "lat": 55.03},
    "クラスノヤルスク": {"en": "Krasnoyarsk", "country": "Russia", "km": "ក្រាសណូយ៉ាស្កិ", "utc": 7, "dist_jp": 4159, "dist_kh": 5052, "lon": 92.87, "lat": 56.01},
    # === UTC+8 ===
    "成都": {"en": "Chengdu", "country": "China", "km": "ឆេងឌូ", "utc": 8, "dist_jp": 3347, "dist_kh": 2116, "lon": 104.07, "lat": 30.57},
    "武漢": {"en": "Wuhan", "country": "China", "km": "អ៊ូហាន់", "utc": 8, "dist_jp": 2423, "dist_kh": 2327, "lon": 114.31, "lat": 30.59},
    "南京": {"en": "Nanjing", "country": "China", "km": "ណានជីង", "utc": 8, "dist_jp": 1966, "dist_kh": 2687, "lon": 118.80, "lat": 32.06},
    "北京": {"en": "Beijing", "country": "China", "km": "ប៉េកាំង", "utc": 8, "dist_jp": 2092, "dist_kh": 3348, "lon": 116.41, "lat": 39.9},
    "上海": {"en": "Shanghai", "country": "China", "km": "សៀងហៃ", "utc": 8, "dist_jp": 1759, "dist_kh": 2771, "lon": 121.47, "lat": 31.23},
    "広州": {"en": "Guangzhou", "country": "China", "km": "ក្វាងចូវ", "utc": 8, "dist_jp": 2903, "dist_kh": 1561, "lon": 113.26, "lat": 23.13},
    "深圳": {"en": "Shenzhen", "country": "China", "km": "សិនជិន", "utc": 8, "dist_jp": 2874, "dist_kh": 1560, "lon": 114.06, "lat": 22.54},
    "重慶": {"en": "Chongqing", "country": "China", "km": "ឈុងឈីង", "utc": 8, "dist_jp": 3162, "dist_kh": 2009, "lon": 106.55, "lat": 29.56},
    "天津": {"en": "Tianjin", "country": "China", "km": "ធានជីន", "utc": 8, "dist_jp": 2018, "dist_kh": 3298, "lon": 117.2, "lat": 39.13},
    "香港": {"en": "Hong Kong", "country": "China", "km": "ហុងកុង", "utc": 8, "dist_jp": 2880, "dist_kh": 1548, "lon": 114.17, "lat": 22.32},
    "台北": {"en": "Taipei", "country": "Taiwan", "km": "តៃប៉ិ", "utc": 8, "dist_jp": 2099, "dist_kh": 2305, "lon": 121.56, "lat": 25.03},
    "マニラ": {"en": "Manila", "country": "Philippines", "km": "ម៉ានីល", "utc": 8, "dist_jp": 2996, "dist_kh": 1772, "lon": 120.98, "lat": 14.6},
    "シンガポール": {"en": "Singapore", "country": "Singapore", "km": "សិង្ហបុរី", "utc": 8, "dist_jp": 5315, "dist_kh": 1141, "lon": 103.82, "lat": 1.35},
    "クアラルンプール": {"en": "Kuala Lumpur", "country": "Malaysia", "km": "កូឡាឡាំពួរ", "utc": 8, "dist_jp": 5321, "dist_kh": 1001, "lon": 101.69, "lat": 3.14},
    "デンパサール": {"en": "Denpasar", "country": "Indonesia", "km": "ដែនប៉ាសារ", "utc": 8, "dist_jp": 5557, "dist_kh": 2519, "lon": 115.22, "lat": -8.65},
    "イルクーツク": {"en": "Irkutsk", "country": "Russia", "km": "អ៊ីរគុតស្កិ", "utc": 8, "dist_jp": 3331, "dist_kh": 4530, "lon": 104.28, "lat": 52.29},
    "ウランバートル": {"en": "Ulaanbaatar", "country": "Mongolia", "km": "អ៊ូឡង់បាទ័រ", "utc": 8, "dist_jp": 3007, "dist_kh": 4048, "lon": 106.92, "lat": 47.92},
    "パース": {"en": "Perth", "country": "Australia", "km": "ភឺត", "utc": 8, "dist_jp": 7921, "dist_kh": 4976, "lon": 115.86, "lat": -31.95},
    # === UTC+9 ===
    "名古屋": {"en": "Nagoya", "country": "Japan", "km": "ណាហ្គោយ៉ា", "utc": 9, "dist_jp": 258, "dist_kh": 4157, "lon": 136.91, "lat": 35.18},
    "京都": {"en": "Kyoto", "country": "Japan", "km": "ក្យូតូ", "utc": 9, "dist_jp": 364, "dist_kh": 4059, "lon": 135.77, "lat": 35.01},
    "釜山": {"en": "Busan", "country": "South Korea", "km": "ប៊ូសាន", "utc": 9, "dist_jp": 963, "dist_kh": 3582, "lon": 129.08, "lat": 35.18},
    "東京": {"en": "Tokyo", "country": "Japan", "km": "តូក្យូ", "utc": 9, "dist_jp": 0, "dist_kh": 4404, "lon": 139.69, "lat": 35.69},
    "大阪": {"en": "Osaka", "country": "Japan", "km": "អូសាកា", "utc": 9, "dist_jp": 397, "dist_kh": 4019, "lon": 135.5, "lat": 34.69},
    "ソウル": {"en": "Seoul", "country": "South Korea", "km": "សូល", "utc": 9, "dist_jp": 1152, "dist_kh": 3632, "lon": 126.98, "lat": 37.57},
    "ピョンヤン": {"en": "Pyongyang", "country": "North Korea", "km": "ព្យុងយ៉ាង", "utc": 9, "dist_jp": 1285, "dist_kh": 3683, "lon": 125.75, "lat": 39.02},
    "ウラジオストク": {"en": "Vladivostok", "country": "Russia", "km": "វ្លាឌីវ៉ូស្តុក", "utc": 10, "dist_jp": 1063, "dist_kh": 4366, "lon": 131.89, "lat": 43.12},
    "ヤクーツク": {"en": "Yakutsk", "country": "Russia", "km": "យ៉ាគូតស្កិ", "utc": 9, "dist_jp": 3010, "dist_kh": 5955, "lon": 129.73, "lat": 62.03},
    "札幌": {"en": "Sapporo", "country": "Japan", "km": "សាប៉ូរ៉ូ", "utc": 9, "dist_jp": 832, "dist_kh": 4953, "lon": 141.35, "lat": 43.06},
    "福岡": {"en": "Fukuoka", "country": "Japan", "km": "ហ្វុគូអូកា", "utc": 9, "dist_jp": 879, "dist_kh": 3566, "lon": 130.42, "lat": 33.59},
    # === UTC+9.5 ===
    "アデレード": {"en": "Adelaide", "country": "Australia", "km": "អាដែឡេដ", "utc": 9.5, "dist_jp": 7853, "dist_kh": 6269, "lon": 138.6, "lat": -34.93},
    "ダーウィン": {"en": "Darwin", "country": "Australia", "km": "ដាវីន", "utc": 9.5, "dist_jp": 5434, "dist_kh": 3914, "lon": 130.84, "lat": -12.46},
    # === UTC+10 ===
    "キャンベラ": {"en": "Canberra", "country": "Australia", "km": "កង់បេរ៉ា", "utc": 10, "dist_jp": 7952, "dist_kh": 6980, "lon": 149.13, "lat": -35.28},
    "ゴールドコースト": {"en": "Gold Coast", "country": "Australia", "km": "ហ្គោលកូស្ត", "utc": 10, "dist_jp": 7227, "dist_kh": 6825, "lon": 153.43, "lat": -28.00},
    "シドニー": {"en": "Sydney", "country": "Australia", "km": "ស៊ីដនី", "utc": 10, "dist_jp": 7827, "dist_kh": 7031, "lon": 151.21, "lat": -33.87},
    "メルボルン": {"en": "Melbourne", "country": "Australia", "km": "ម៉ែលប៊ឺន", "utc": 10, "dist_jp": 8191, "dist_kh": 6892, "lon": 144.96, "lat": -37.81},
    "ブリスベン": {"en": "Brisbane", "country": "Australia", "km": "ប្រ៊ីសបេន", "utc": 10, "dist_jp": 7161, "dist_kh": 6760, "lon": 153.03, "lat": -27.47},
    "ポートモレスビー": {"en": "Port Moresby", "country": "Papua New Guinea", "km": "ផតម៉រេសប៊ី", "utc": 10, "dist_jp": 5083, "dist_kh": 5222, "lon": 147.15, "lat": -9.48},
    "グアム": {"en": "Hagatna, Guam", "country": "Guam", "km": "ហ្គាម", "utc": 10, "dist_jp": 2526, "dist_kh": 4329, "lon": 144.79, "lat": 13.44},
    # === UTC+11 ===
    "ヌメア": {"en": "Nouméa", "country": "New Caledonia", "km": "នូមេអា", "utc": 11, "dist_jp": 7035, "dist_kh": 7688, "lon": 166.46, "lat": -22.28},
    "ホニアラ": {"en": "Honiara", "country": "Solomon Islands", "km": "ហូនីអារ៉ា", "utc": 11, "dist_jp": 5449, "dist_kh": 6518, "lon": 159.97, "lat": -9.43},
    "マガダン": {"en": "Magadan", "country": "Russia", "km": "ម៉ាហ្គាដង់", "utc": 11, "dist_jp": 2773, "dist_kh": 6537, "lon": 150.8, "lat": 59.56},
    "ポートビラ": {"en": "Port Vila", "country": "Vanuatu", "km": "ផតវីឡា", "utc": 11, "dist_jp": 6662, "dist_kh": 7683, "lon": 168.32, "lat": -17.73},
    "サハリンスク": {"en": "Yuzhno-Sakhalinsk", "country": "Russia", "km": "សាខាលីនស្កិ", "utc": 11, "dist_jp": 1279, "dist_kh": 5290, "lon": 142.74, "lat": 46.96},
    # === UTC+12 ===
    "オークランド": {"en": "Auckland", "country": "New Zealand", "km": "អូក្លែន", "utc": 12, "dist_jp": 8841, "dist_kh": 9048, "lon": 174.76, "lat": -36.85},
    "ウェリントン": {"en": "Wellington", "country": "New Zealand", "km": "វែលីនតោន", "utc": 12, "dist_jp": 9277, "dist_kh": 9233, "lon": 174.78, "lat": -41.29},
    "フィジー": {"en": "Suva, Fiji", "country": "Fiji", "km": "ហ្វីជី", "utc": 12, "dist_jp": 7244, "dist_kh": 8714, "lon": 178.44, "lat": -18.14},
    "ペトロパブロフスク": {"en": "Petropavlovsk-Kamchatsky", "country": "Russia", "km": "ពេត្រូប៉ាវឡូស្កិ", "utc": 12, "dist_jp": 2430, "dist_kh": 6607, "lon": 158.65, "lat": 53.01},
    "マジュロ": {"en": "Majuro", "country": "Marshall Islands", "km": "ម៉ាជូរ៉ូ", "utc": 12, "dist_jp": 4529, "dist_kh": 7295, "lon": 171.38, "lat": 7.09},
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


def haversine_km(lon1, lat1, lon2, lat2):
    """2点間の大圏距離(km)を返す"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def fetch_flat_map(zoom=2, width=2048, height=2048):
    # type: (int, int, int) -> Image.Image
    """OSMタイルから世界地図を取得（キャッシュ付き）"""
    cache_dir = os.path.join(os.path.dirname(__file__), "cache")
    cache_file = os.path.join(cache_dir, "flatmap_z{}_{}x{}.png".format(zoom, width, height))
    if os.path.exists(cache_file):
        return Image.open(cache_file).convert("RGB")
    # 初回のみネット通信
    m = StaticMap(width, height, url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png")
    m.add_marker(CircleMarker((0, 0), "blue", 1))
    img = m.render(zoom=zoom, center=[0, 0])
    os.makedirs(cache_dir, exist_ok=True)
    img.save(cache_file)
    print("タイルキャッシュ保存: {}".format(cache_file))
    return img


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


def generate_map(city_name, output_dir=".", force_moon=False, force_ufo=False, force_city_auto_add=False, scale=100):
    # type: (str, str) -> str

    if not force_city_auto_add and city_name not in CITY_NAME_MAP:
        print("エラー: 「{}」は登録されていない都市です。".format(city_name))
        print("登録済み都市一覧から選択するか、--force-city-auto-add オプションでNominatim検索を有効にしてください。")
        return None

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

    # === 月 & UFO（重ならないように配置、ヘッダー領域を避ける）===
    HEADER_ZONE_BOTTOM = 210  # ヘッダーテキストの下端
    HEADER_ZONE_RIGHT = 550   # ヘッダーテキストの右端
    show_moon = force_moon or rng.random() < 0.3
    show_ufo = force_ufo or rng.random() < 0.2
    moon_pos = None

    if show_moon:
        for _ in range(20):
            mx = rng.randint(40, IMG_W - 80)
            my = rng.randint(HEADER_ZONE_BOTTOM, 500)
            mdx = mx - globe_center_x
            mdy = my - globe_center_y
            if mdx * mdx + mdy * mdy > (GLOBE_SIZE // 2 + 60) ** 2:
                break
        moon_r = rng.randint(15, 25)
        moon_pos = (mx, my, moon_r)
        moon_img = Image.new("RGBA", (moon_r * 3, moon_r * 3), (0, 0, 0, 0))
        moon_draw = ImageDraw.Draw(moon_img)
        mc = moon_r * 3 // 2
        moon_draw.ellipse([mc - moon_r, mc - moon_r, mc + moon_r, mc + moon_r],
                          fill=(230, 220, 180, 200))
        offset = int(moon_r * 0.6)
        moon_draw.ellipse([mc - moon_r + offset, mc - moon_r - 2,
                           mc + moon_r + offset, mc + moon_r + 2],
                          fill=(0, 0, 0, 0))
        img.paste(moon_img, (mx - mc, my - mc), moon_img)

    if show_ufo:
        for _ in range(40):
            ux = rng.randint(60, IMG_W - 60)
            uy = rng.randint(HEADER_ZONE_BOTTOM, 850)
            # ヘッダー領域を避ける
            if uy < HEADER_ZONE_BOTTOM and ux < HEADER_ZONE_RIGHT:
                continue
            udx = ux - globe_center_x
            udy = uy - globe_center_y
            if udx * udx + udy * udy <= (GLOBE_SIZE // 2 + 50) ** 2:
                continue
            # 月と重ならないかチェック
            if moon_pos:
                mdist = math.sqrt((ux - moon_pos[0]) ** 2 + (uy - moon_pos[1]) ** 2)
                if mdist < moon_pos[2] * 3 + 40:
                    continue
            break
        ufo_size = rng.randint(32, 48)
        ufo_pad = 16
        ufo_total = ufo_size + ufo_pad * 2
        ufo_img = Image.new("RGBA", (ufo_total, ufo_total), (0, 0, 0, 0))
        ud = ImageDraw.Draw(ufo_img)
        c = ufo_total // 2
        r = ufo_size // 2
        body_colors = [
            (180, 200, 230, 210),
            (200, 180, 230, 210),
            (180, 230, 200, 210),
            (230, 200, 180, 210),
        ]
        body_color = body_colors[rng.randint(0, len(body_colors) - 1)]
        rh = r // 2
        ud.ellipse([c - r, c - rh, c + r, c + rh], fill=body_color)
        dome_r = int(r * 0.4)
        ud.ellipse([c - dome_r, c - rh - dome_r, c + dome_r, c - rh + dome_r],
                    fill=(200, 230, 255, 160))
        hl_r = int(r * 0.15)
        ud.ellipse([c - dome_r + 3, c - rh - dome_r + 3,
                     c - dome_r + 3 + hl_r, c - rh - dome_r + 3 + hl_r],
                    fill=(255, 255, 255, 140))
        ring_h = max(3, int(r * 0.15))
        ud.ellipse([c - r - 4, c - ring_h, c + r + 4, c + ring_h],
                    fill=(150, 170, 200, 180))
        light_colors = [(255, 100, 100, 200), (100, 255, 100, 200),
                        (100, 100, 255, 200), (255, 255, 100, 200), (255, 150, 255, 200)]
        for i, lc in enumerate(light_colors):
            angle = (2 * math.pi * i / 5) - math.pi / 2
            lx = int(c + (r * 0.6) * math.cos(angle))
            ly = int(c + (r * 0.3) * math.sin(angle) + r * 0.3)
            ud.ellipse([lx - 2, ly - 2, lx + 2, ly + 2], fill=lc)
        ufo_angle = rng.randint(0, 360)
        ufo_img = ufo_img.rotate(ufo_angle, resample=Image.BICUBIC, expand=False)
        img.paste(ufo_img, (ux - c, uy - c), ufo_img)

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
    draw_flag_jp(draw, jx, jy, size=40)
    draw_dashed_line(draw, (cx, cy), (jx, jy), (200, 200, 200), width=1)

    # カンボジア
    kx = globe_x + kh_gp[0]
    ky = globe_y + kh_gp[1]
    if kh_visible:
        draw.ellipse([kx - 6, ky - 6, kx + 6, ky + 6], fill=(0, 82, 165), outline=COLOR_WHITE, width=2)
    draw_flag_kh(draw, kx, ky, size=40)
    draw_dashed_line(draw, (cx, cy), (kx, ky), (200, 200, 200), width=1)


    # === ヘッダー ===
    font_title = get_font(72, bold=True)
    font_title_km = get_font_km(56)
    font_sub = get_font(18)

    city_info = CITY_NAME_MAP.get(city_name, {})
    km_name = city_info.get("km", "")

    en_name = city_info.get("en", city_name)

    # 1行目: 日本語 + クメール語（長すぎたらフォント縮小）
    max_title_width = IMG_W - 360  # ロゴ領域（300px+余白）を避ける
    title_size = 72
    km_title_size = 56
    while title_size >= 24:
        ft = get_font(title_size, bold=True)
        ftk = get_font_km(km_title_size)
        tw = draw.textlength(city_name, font=ft)
        kw = draw.textlength(km_name, font=ftk) if km_name else 0
        total_w = tw + (20 + kw if km_name else 0)
        if total_w + 40 <= max_title_width:
            break
        title_size -= 4
        km_title_size = int(title_size * 0.78)
    font_title = ft
    font_title_km = ftk
    tw = draw.textlength(city_name, font=font_title)
    # 縁取り付き都市名（日本語）
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx == 0 and dy == 0:
                continue
            draw.text((40 + dx, 15 + dy), city_name, fill=(0, 0, 0), font=font_title)
    draw.text((40, 15), city_name, fill=COLOR_TEXT, font=font_title)
    if km_name:
        km_y = 15 + (title_size - km_title_size) // 2
        # 縁取り付き都市名（クメール語）
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx == 0 and dy == 0:
                    continue
                draw.text((40 + tw + 20 + dx, km_y + dy), km_name, fill=(0, 0, 0), font=font_title_km)
        draw.text((40 + tw + 20, km_y), km_name, fill=(180, 180, 180), font=font_title_km)
    # 2行目: 英語名
    font_en = get_font(20)
    draw.text((40, 92), en_name, fill=(160, 180, 200), font=font_en)
    # 3行目: Japan & Cambodia
    draw.text((40, 118), "Japan & Cambodia", fill=(100, 160, 210), font=font_sub)

    # === ラベル ===
    font_label = get_font(17, bold=True)
    font_label_km = get_font_km(14)
    km_name2 = CITY_NAME_MAP.get(city_name, {}).get("km", "")

    # 日本ラベル（先に描画=下層、縁取り付き）
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx == 0 and dy == 0:
                continue
            draw.text((jx + 14 + dx, jy - 8 + dy), "日本  ", fill=(0, 0, 0), font=font_label)
    draw.text((jx + 14, jy - 8), "日本  ", fill=COLOR_WHITE, font=font_label)
    jw = draw.textlength("日本  ", font=font_label)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx == 0 and dy == 0:
                continue
            draw.text((jx + 14 + jw + dx, jy - 6 + dy), "ជប៉ុន", fill=(0, 0, 0), font=font_label_km)
    draw.text((jx + 14 + jw, jy - 6), "ជប៉ុន", fill=(180, 180, 180), font=font_label_km)

    # カンボジアラベル（先に描画=下層、縁取り付き）
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx == 0 and dy == 0:
                continue
            draw.text((kx + 14 + dx, ky - 8 + dy), "カンボジア  ", fill=(0, 0, 0), font=font_label)
    draw.text((kx + 14, ky - 8), "カンボジア  ", fill=COLOR_WHITE, font=font_label)
    kw = draw.textlength("カンボジア  ", font=font_label)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx == 0 and dy == 0:
                continue
            draw.text((kx + 14 + kw + dx, ky - 6 + dy), "កម្ពុជា", fill=(0, 0, 0), font=font_label_km)
    draw.text((kx + 14 + kw, ky - 6), "កម្ពុជា", fill=(180, 180, 180), font=font_label_km)

    # 都市ラベル（後に描画=上層、ピン上にセンタリング）
    city_label_size = 34
    city_label_km_size = 29
    font_city_label = get_font(city_label_size, bold=True)
    font_city_label_km = get_font_km(city_label_km_size)
    lbl = city_name
    lbl_w = draw.textlength(lbl, font=font_city_label)
    km_w2 = draw.textlength(km_name2, font=font_city_label_km) if km_name2 else 0
    gap = 10 if km_name2 else 0
    total_label_w = lbl_w + gap + km_w2
    label_x = cx - total_label_w / 2
    label_y = cy - city_label_size - 16
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx == 0 and dy == 0:
                continue
            draw.text((label_x + dx, label_y + dy), lbl, fill=COLOR_WHITE, font=font_city_label)
    draw.text((label_x, label_y), lbl, fill=COLOR_CITY, font=font_city_label)
    if km_name2:
        km_x2 = label_x + lbl_w + gap
        km_y2 = label_y + (city_label_size - city_label_km_size) // 2
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx == 0 and dy == 0:
                    continue
                draw.text((km_x2 + dx, km_y2 + dy), km_name2, fill=COLOR_WHITE, font=font_city_label_km)
        draw.text((km_x2, km_y2), km_name2, fill=(255, 80, 80), font=font_city_label_km)

    # === ロゴ（右上）===
    logo_path = os.path.join(os.path.dirname(__file__), "logo_mirai_lab.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        # 幅200pxにリサイズ（アスペクト比維持）
        logo_w = 300
        logo_h = int(logo.height * logo_w / logo.width)
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        # 右上に配置（余白20px）
        lx = IMG_W - logo_w - 20
        ly = 20
        img.paste(logo, (lx, ly), logo)

    # === 距離表示（最前面に描画）===
    font_dist = get_font(26)
    dist_jp = city_info.get("dist_jp")
    dist_kh = city_info.get("dist_kh")
    if dist_jp is None:
        dist_jp = int(round(haversine_km(city_coord[0], city_coord[1], JAPAN_COORD[0], JAPAN_COORD[1])))
    if dist_kh is None:
        dist_kh = int(round(haversine_km(city_coord[0], city_coord[1], CAMBODIA_COORD[0], CAMBODIA_COORD[1])))
    dist_text_jp = "{} ~ Japan: {:,} km".format(en_name, dist_jp)
    dist_text_kh = "{} ~ Cambodia: {:,} km".format(en_name, dist_kh)
    outline_color = (0, 0, 0)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx == 0 and dy == 0:
                continue
            draw.text((40 + dx, 143 + dy), dist_text_jp, fill=outline_color, font=font_dist)
            draw.text((40 + dx, 173 + dy), dist_text_kh, fill=outline_color, font=font_dist)
    draw.text((40, 143), dist_text_jp, fill=(140, 160, 180), font=font_dist)
    draw.text((40, 173), dist_text_kh, fill=(140, 160, 180), font=font_dist)

    # === 保存 ===
    if scale < 100:
        new_w = int(img.width * scale / 100)
        new_h = int(img.height * scale / 100)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        print("リサイズ: {}x{} ({}%)".format(new_w, new_h, scale))
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) / "map_{}_{}_{}.png".format(en_name, timestamp, scale)
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


def _smooth_globe_pos(lon, lat, center_lon, center_lat, globe_diameter, globe_x, globe_y):
    """旗の位置を滑らかに計算。裏側ではジャンプせず徐々に浮く"""
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

    dist = math.sqrt(x * x + y * y)
    if dist < 0.001:
        nx, ny = 0.0, -1.0
    else:
        nx, ny = x / dist, -y / dist

    if cos_c >= 0.15:
        # 表面にしっかり乗っている
        px = globe_x + radius + int(x * radius)
        py = globe_y + radius - int(y * radius)
        return (px, py), True
    elif cos_c >= -0.3:
        # 縁付近: 表面→浮き上がりへ滑らかに遷移
        blend = (0.15 - cos_c) / 0.45  # 0→1
        blend = blend * blend  # ゆっくり始まる
        edge_px = globe_x + radius + nx * radius
        edge_py = globe_y + radius + ny * radius
        out_px = globe_x + radius + nx * (radius + 45)
        out_py = globe_y + radius + ny * (radius + 45)
        px = int(edge_px + (out_px - edge_px) * blend)
        py = int(edge_py + (out_py - edge_py) * blend)
        return (px, py), True
    else:
        # 完全に裏側: 外側に浮いている
        offset = radius + 45
        px = globe_x + radius + int(nx * offset)
        py = globe_y + radius + int(ny * offset)
        return (px, py), False


def generate_gif(city_name, output_dir=".", frames=36, duration=42, direction=None, scale=100, force_moon=False, force_ufo=False):
    # type: (str, str, int, int) -> str
    """地球儀アニメGIF: 右端→中央へ1/4回転し、停止後にラベル表示"""
    if city_name not in CITY_NAME_MAP:
        print("エラー: 「{}」は登録されていない都市です。".format(city_name))
        return None

    city_coord = geocode_city(city_name)
    city_info = CITY_NAME_MAP.get(city_name, {})
    en_name = city_info.get("en", city_name)
    km_name = city_info.get("km", "")

    # 方向設定: (lon_offset, lat_offset) 初期値
    DIR_CONFIG = {
        "right-to-center":        (-60, 0),
        "left-to-center":         (60, 0),
        "top-to-center":          (0, -60),
        "bottom-to-center":       (0, 60),
        "top-right-to-center":    (-45, -40),
        "top-left-to-center":     (45, -40),
        "bottom-right-to-center": (-45, 40),
        "bottom-left-to-center":  (45, 40),
    }
    if direction is None:
        direction = random.choice(list(DIR_CONFIG.keys()))
    dir_lon, dir_lat = DIR_CONFIG[direction]
    # 緯度オフセットを都市の緯度に応じて対称に調整
    if dir_lat != 0:
        max_up = 85 - city_coord[1]    # 上方向の余裕
        max_down = city_coord[1] + 85   # 下方向の余裕
        safe_lat = min(abs(dir_lat), max_up, max_down)
        dir_lat = safe_lat if dir_lat > 0 else -safe_lat
    move_frames = frames
    total = frames + 1
    print("GIF生成: {} (方向={}, 移動{}+停止1={}フレーム)".format(
        city_name, direction, move_frames, total))

    flat_map = fetch_flat_map(zoom=2, width=2048, height=2048)
    seed = int(hashlib.md5(city_name.encode()).hexdigest()[:8], 16)

    globe_x = (IMG_W - GLOBE_SIZE) // 2
    globe_y = (IMG_H - GLOBE_SIZE) // 2
    globe_center_x = globe_x + GLOBE_SIZE // 2
    globe_center_y = globe_y + GLOBE_SIZE // 2
    globe_r_sq = (GLOBE_SIZE // 2 + 10) ** 2

    # ロゴ事前読み込み
    logo_img = None
    logo_path = os.path.join(os.path.dirname(__file__), "logo_mirai_lab.png")
    if os.path.exists(logo_path):
        logo_img = Image.open(logo_path).convert("RGBA")
        logo_w = 225
        logo_h = int(logo_img.height * logo_w / logo_img.width)
        logo_img = logo_img.resize((logo_w, logo_h), Image.LANCZOS)

    # 距離
    dist_jp = city_info.get("dist_jp")
    dist_kh = city_info.get("dist_kh")
    if dist_jp is None:
        dist_jp = int(round(haversine_km(city_coord[0], city_coord[1], JAPAN_COORD[0], JAPAN_COORD[1])))
    if dist_kh is None:
        dist_kh = int(round(haversine_km(city_coord[0], city_coord[1], CAMBODIA_COORD[0], CAMBODIA_COORD[1])))

    # 月・UFO表示判定（PNGと同じランダム確率）
    rng_show = random.Random(seed + 99)
    show_moon = force_moon or rng_show.random() < 0.3
    show_ufo = force_ufo or rng_show.random() < 0.2

    # 月・UFO画像を事前生成
    rng2 = random.Random(seed + 1)
    for _ in range(40):
        moon_base_x = rng2.randint(IMG_W // 2, IMG_W - 80)  # 右側から開始
        moon_base_y = rng2.randint(150, 850)
        mdx = moon_base_x - globe_center_x
        mdy = moon_base_y - globe_center_y
        if mdx * mdx + mdy * mdy > (GLOBE_SIZE // 2 + 80) ** 2:
            break
    moon_r = rng2.randint(15, 25)
    moon_img_pre = Image.new("RGBA", (moon_r * 3, moon_r * 3), (0, 0, 0, 0))
    moon_draw = ImageDraw.Draw(moon_img_pre)
    moon_mc = moon_r * 3 // 2
    moon_draw.ellipse([moon_mc - moon_r, moon_mc - moon_r, moon_mc + moon_r, moon_mc + moon_r],
                      fill=(230, 220, 180, 200))
    offset_m = int(moon_r * 0.6)
    moon_draw.ellipse([moon_mc - moon_r + offset_m, moon_mc - moon_r - 2,
                       moon_mc + moon_r + offset_m, moon_mc + moon_r + 2],
                      fill=(0, 0, 0, 0))

    rng3 = random.Random(seed + 2)
    for _ in range(40):
        ufo_base_x = rng3.randint(IMG_W // 2, IMG_W - 60)  # 右側から開始
        ufo_base_y = rng3.randint(150, 850)
        udx = ufo_base_x - globe_center_x
        udy = ufo_base_y - globe_center_y
        if udx * udx + udy * udy > (GLOBE_SIZE // 2 + 80) ** 2:
            mdist_u = math.sqrt((ufo_base_x - moon_base_x) ** 2 + (ufo_base_y - moon_base_y) ** 2)
            if mdist_u > moon_r * 3 + 40:
                break
    ufo_size = rng3.randint(32, 48)
    ufo_pad = 16
    ufo_total = ufo_size + ufo_pad * 2
    ufo_img_pre = Image.new("RGBA", (ufo_total, ufo_total), (0, 0, 0, 0))
    ud = ImageDraw.Draw(ufo_img_pre)
    ufo_uc = ufo_total // 2
    ur = ufo_size // 2
    body_colors = [(180,200,230,210),(200,180,230,210),(180,230,200,210),(230,200,180,210)]
    bc = body_colors[rng3.randint(0, len(body_colors) - 1)]
    urh = ur // 2
    ud.ellipse([ufo_uc - ur, ufo_uc - urh, ufo_uc + ur, ufo_uc + urh], fill=bc)
    dome_r = int(ur * 0.4)
    ud.ellipse([ufo_uc - dome_r, ufo_uc - urh - dome_r, ufo_uc + dome_r, ufo_uc - urh + dome_r], fill=(200,230,255,160))
    ring_h = max(3, int(ur * 0.15))
    ud.ellipse([ufo_uc - ur - 4, ufo_uc - ring_h, ufo_uc + ur + 4, ufo_uc + ring_h], fill=(150,170,200,180))
    ufo_angle = rng3.randint(0, 360)
    ufo_img_pre = ufo_img_pre.rotate(ufo_angle, resample=Image.BICUBIC, expand=False)

    img_frames = []
    img_frames_rgb = []
    frame_durations = []
    final_frame = None
    last_center_lon = city_coord[0]
    last_center_lat = city_coord[1]

    for i in range(total):
        is_moving = i < move_frames
        is_stopped = not is_moving

        if is_moving:
            t = i / move_frames
            # イージング計算（方向共通）
            v1 = 1.0; v3 = 0.5; t1_end = 0.7; t2_end = 0.85
            e_start = t1_end * v1
            dur2 = t2_end - t1_end
            e_mid = e_start + dur2 * (v1 + (v3 - v1) / 2)
            e_max = e_mid + v3 * (1.0 - t2_end)
            if t < t1_end:
                eased = t * v1
            elif t < t2_end:
                dt = t - t1_end; t2 = dt / dur2
                eased = e_start + dur2 * (v1 * t2 + (v3 - v1) * t2 * t2 / 2)
            else:
                dt3 = t - t2_end
                eased = e_mid + v3 * dt3
            eased = eased / e_max  # 正規化: 0→1.0

            # 方向に応じたオフセット（汎用）
            remain = 1.0 - eased
            center_lon = city_coord[0] + dir_lon * remain
            center_lat = city_coord[1] + dir_lat * remain
            center_lat = max(-85, min(85, center_lat))
            last_center_lon = center_lon
            last_center_lat = center_lat
        else:
            center_lon = last_center_lon
            center_lat = last_center_lat

        while center_lon > 180:
            center_lon -= 360
        while center_lon < -180:
            center_lon += 360

        print("  フレーム {}/{}...".format(i + 1, total))
        globe = orthographic_project(flat_map, center_lon, center_lat, GLOBE_SIZE)

        img = Image.new("RGB", (IMG_W, IMG_H), COLOR_BG)
        draw = ImageDraw.Draw(img)

        # 星空
        rng = random.Random(seed)
        for _ in range(120):
            sx = rng.randint(10, IMG_W - 10)
            sy = rng.randint(140, 890)
            dx = sx - globe_center_x
            dy = sy - globe_center_y
            if dx * dx + dy * dy < globe_r_sq:
                continue
            brightness = rng.randint(120, 255)
            sz = rng.choice([1, 1, 1, 2, 2, 3])
            clr = (brightness, brightness, brightness)
            if sz == 1:
                draw.point((sx, sy), fill=clr)
            else:
                draw.ellipse([sx - sz // 2, sy - sz // 2,
                              sx + sz // 2, sy + sz // 2], fill=clr)

        # 月・UFO（eased に応じて方向別パララックス移動）
        drift = eased * 120
        # lon方向 → x移動, lat方向 → y移動（符号反転: 地球回転と同方向に流れる）
        dx_sign = -1 if dir_lon > 0 else (1 if dir_lon < 0 else 0)
        dy_sign = -1 if dir_lat > 0 else (1 if dir_lat < 0 else 0)
        m_dx = int(drift * 0.7 * dx_sign)
        m_dy = int(drift * 0.7 * dy_sign)
        u_dx = int(drift * dx_sign)
        u_dy = int(drift * dy_sign)

        if show_moon:
            moon_cx = moon_base_x + m_dx
            moon_cy = moon_base_y + m_dy
            img.paste(moon_img_pre, (moon_cx - moon_mc, moon_cy - moon_mc), moon_img_pre)

        if show_ufo:
            ufo_cx = ufo_base_x + u_dx
            ufo_cy = ufo_base_y + u_dy
            img.paste(ufo_img_pre, (ufo_cx - ufo_uc, ufo_cy - ufo_uc), ufo_img_pre)

        # 地球儀の影
        for si in range(8, 0, -1):
            alpha = 30 - si * 3
            clr = (max(0, COLOR_BG[0] + alpha), max(0, COLOR_BG[1] + alpha), max(0, COLOR_BG[2] + alpha))
            draw.ellipse([globe_x - si, globe_y - si,
                          globe_x + GLOBE_SIZE + si, globe_y + GLOBE_SIZE + si], outline=clr, width=2)

        img.paste(globe, (globe_x, globe_y), globe)
        draw.ellipse([globe_x - 1, globe_y - 1,
                      globe_x + GLOBE_SIZE + 1, globe_y + GLOBE_SIZE + 1],
                     outline=COLOR_OCEAN_RING, width=2)

        # マーカー（都市・日本・カンボジア）- 滑らか移動
        city_gp, city_vis = lonlat_to_globe_pixel(
            city_coord[0], city_coord[1], center_lon, center_lat, GLOBE_SIZE)
        cx_p = globe_x + city_gp[0]
        cy_p = globe_y + city_gp[1]
        if city_vis:
            draw.ellipse([cx_p - 8, cy_p - 8, cx_p + 8, cy_p + 8],
                         fill=COLOR_CITY, outline=COLOR_WHITE, width=2)

        (jx, jy), jp_draw = _smooth_globe_pos(
            JAPAN_COORD[0], JAPAN_COORD[1], center_lon, center_lat,
            GLOBE_SIZE, globe_x, globe_y)
        draw_flag_jp(draw, jx, jy, size=32)

        (kx, ky), kh_draw = _smooth_globe_pos(
            CAMBODIA_COORD[0], CAMBODIA_COORD[1], center_lon, center_lat,
            GLOBE_SIZE, globe_x, globe_y)
        draw_flag_kh(draw, kx, ky, size=32)

        # ヘッダー（常に表示: 都市名+クメール語+英語名）
        font_title = get_font(48, bold=True)
        font_title_km = get_font_km(36)
        tw = draw.textlength(city_name, font=font_title)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx == 0 and dy == 0:
                    continue
                draw.text((40 + dx, 15 + dy), city_name, fill=(0, 0, 0), font=font_title)
        draw.text((40, 15), city_name, fill=COLOR_TEXT, font=font_title)
        if km_name:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((40 + tw + 15 + dx, 22 + dy), km_name, fill=(0, 0, 0), font=font_title_km)
            draw.text((40 + tw + 15, 22), km_name, fill=(180, 180, 180), font=font_title_km)
        font_en = get_font(16)
        draw.text((40, 68), en_name, fill=(160, 180, 200), font=font_en)
        font_sub = get_font(14)
        draw.text((40, 88), "Japan & Cambodia", fill=(100, 160, 210), font=font_sub)

        # ロゴ
        if logo_img:
            img.paste(logo_img, (IMG_W - logo_img.width - 15, 15), logo_img)

        # === 停止時のみ: ラベル・距離を表示 ===
        if is_stopped:
            # 日本・カンボジアラベル（先に描画=下層、縁取り付き）
            font_label = get_font(14, bold=True)
            font_label_km = get_font_km(12)
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((jx + 12 + dx, jy - 6 + dy), "日本", fill=(0, 0, 0), font=font_label)
                    draw.text((kx + 12 + dx, ky - 6 + dy), "カンボジア", fill=(0, 0, 0), font=font_label)
            draw.text((jx + 12, jy - 6), "日本", fill=COLOR_WHITE, font=font_label)
            draw.text((kx + 12, ky - 6), "カンボジア", fill=COLOR_WHITE, font=font_label)

            # 都市ラベル（後に描画=上層、scaleが小さいほどフォント大、ピン上にセンタリング）
            city_label_size = int(26 * (100 / max(scale, 50)))
            city_label_km_size = int(city_label_size * 0.85)
            font_city_label = get_font(city_label_size, bold=True)
            font_city_label_km = get_font_km(city_label_km_size)
            lbl = city_name
            lbl_w = draw.textlength(lbl, font=font_city_label)
            km_w = draw.textlength(km_name, font=font_city_label_km) if km_name else 0
            gap = 10 if km_name else 0
            total_w = lbl_w + gap + km_w
            label_x = cx_p - total_w / 2
            label_y = cy_p - city_label_size - 16
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((label_x + dx, label_y + dy), lbl, fill=COLOR_WHITE, font=font_city_label)
            draw.text((label_x, label_y), lbl, fill=COLOR_CITY, font=font_city_label)
            if km_name:
                km_x = label_x + lbl_w + gap
                km_y = label_y + (city_label_size - city_label_km_size) // 2
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if dx == 0 and dy == 0:
                            continue
                        draw.text((km_x + dx, km_y + dy), km_name, fill=COLOR_WHITE, font=font_city_label_km)
                draw.text((km_x, km_y), km_name, fill=(255, 80, 80), font=font_city_label_km)

            # 破線
            draw_dashed_line(draw, (cx_p, cy_p), (jx, jy), (200, 200, 200), width=1)
            draw_dashed_line(draw, (cx_p, cy_p), (kx, ky), (200, 200, 200), width=1)

            # 距離表示（縁取り付き）
            font_dist = get_font(22)
            dist_text_jp = "{} ~ Japan: {:,} km".format(en_name, dist_jp)
            dist_text_kh = "{} ~ Cambodia: {:,} km".format(en_name, dist_kh)
            for ddx in range(-2, 3):
                for ddy in range(-2, 3):
                    if ddx == 0 and ddy == 0:
                        continue
                    draw.text((40 + ddx, 110 + ddy), dist_text_jp, fill=(0, 0, 0), font=font_dist)
                    draw.text((40 + ddx, 135 + ddy), dist_text_kh, fill=(0, 0, 0), font=font_dist)
            draw.text((40, 110), dist_text_jp, fill=(140, 160, 180), font=font_dist)
            draw.text((40, 135), dist_text_kh, fill=(140, 160, 180), font=font_dist)

        # 地球下端の余白を半分にクロップ
        globe_bottom = globe_y + GLOBE_SIZE
        bottom_margin = IMG_H - globe_bottom
        crop_h = globe_bottom + bottom_margin // 2
        img = img.crop((0, 0, IMG_W, crop_h))

        # 縮小はRGB状態で行う（フォントのスムーズさを保つ）
        if scale < 100:
            new_w = int(IMG_W * scale / 100)
            new_h = int(crop_h * scale / 100)
            img = img.resize((new_w, new_h), Image.LANCZOS)

        # RGBフレームを保持（パレット変換は全フレーム揃ってから共通パレットで行う）
        img_frames_rgb.append(img)

        if is_stopped:
            final_frame = img.copy()

        # フレームごとのduration計算
        if is_moving:
            speed_t = t
            frame_dur = int(duration * (0.3 + 2.5 * speed_t * speed_t))
            frame_dur = max(20, min(frame_dur, 200))
            frame_durations.append(frame_dur)
        else:
            # 停止フレーム: 5秒
            frame_durations.append(5000)

    if scale < 100:
        print("リサイズ: {}x{} ({}%)".format(
            int(IMG_W * scale / 100), int(crop_h * scale / 100), scale))

    # 共通パレットで全フレームを変換（回転中も停止時も同じ色を保証）
    # 停止フレーム（最後）を基準に全フレームを結合してパレット生成
    key_colors = [
        COLOR_CITY, (188, 0, 45), (224, 0, 37), (3, 46, 161),
        COLOR_WHITE, COLOR_BG, COLOR_OCEAN_RING, COLOR_TEXT,
        (0, 82, 165), (100, 160, 210), (140, 160, 180),
        (180, 180, 180), (255, 120, 120), (200, 200, 200),
        (100, 100, 100), (230, 220, 180), (160, 180, 200),
        (150, 170, 200), (120, 120, 120), (0, 0, 0),
    ]
    ref = Image.new("RGB", (len(key_colors), 1))
    ref_pixels = ref.load()
    for ci, kc in enumerate(key_colors):
        ref_pixels[ci, 0] = kc
    # 停止フレーム + キーカラーからパレット生成
    last_rgb = img_frames_rgb[-1]
    palette_src = Image.new("RGB", (last_rgb.width, last_rgb.height + 1))
    palette_src.paste(last_rgb, (0, 0))
    palette_src.paste(ref.resize((last_rgb.width, 1)), (0, last_rgb.height))
    palette_img = palette_src.quantize(colors=256, dither=0)
    # 共通パレットを全フレームに適用
    img_frames = []
    for f_rgb in img_frames_rgb:
        img_frames.append(f_rgb.quantize(palette=palette_img, dither=0))

    # GIF保存
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) / "map_{}_{}_{}.gif".format(en_name, timestamp, scale)
    img_frames[0].save(
        str(output_path),
        save_all=True,
        append_images=img_frames[1:],
        duration=frame_durations,
        loop=0,
        optimize=False,
    )
    fsize = os.path.getsize(str(output_path))
    print("GIF保存: {} ({:.1f} KB, {:.1f} MB)".format(output_path, fsize / 1024, fsize / 1024 / 1024))
    return str(output_path)


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
    parser.add_argument("city", nargs="?", default=None, help="都市名（日本語 or 英語）。省略時はランダム選択")
    default_output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    parser.add_argument("--output", "-o", default=default_output, help="出力先ディレクトリ")
    parser.add_argument("--upload", "-u", type=int, help="ChatworkルームIDを指定してアップロード")
    parser.add_argument("--message", "-m", default="", help="アップロード時のメッセージ")
    parser.add_argument("--force-moon", action="store_true", help="三日月を強制表示")
    parser.add_argument("--force-ufo", action="store_true", help="UFOを強制表示")
    parser.add_argument("--force-city-auto-add", action="store_true", help="未登録都市をNominatimで自動検索して生成")
    parser.add_argument("--gif", action="store_true", help="アニメGIFを生成（デフォルトはPNG静止画）")
    parser.add_argument("--gif-frames", type=int, default=36, help="GIFのフレーム数（デフォルト36）")
    parser.add_argument("--gif-duration", type=int, default=50, help="GIFの1フレームの表示時間ms（デフォルト50）")
    parser.add_argument("--force-direction", choices=[
        "right-to-center", "left-to-center", "top-to-center", "bottom-to-center",
        "top-right-to-center", "top-left-to-center",
        "bottom-right-to-center", "bottom-left-to-center",
    ], default=None, help="GIF: 移動方向を指定（未指定=ランダム）")
    parser.add_argument("--scale", type=int, choices=[50, 60, 70, 80, 90, 100], default=None, help="解像度スケール（デフォルト: GIF=60, PNG=100）")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    city = args.city
    if city is None:
        city = random.choice(list(CITY_NAME_MAP.keys()))
        print(city)

    if args.gif:
        scale = args.scale if args.scale is not None else 60
        path = generate_gif(city, args.output, frames=args.gif_frames, duration=args.gif_duration, direction=args.force_direction, scale=scale, force_moon=args.force_moon, force_ufo=args.force_ufo)
    else:
        scale = args.scale if args.scale is not None else 100
        path = generate_map(city, args.output, force_moon=args.force_moon, force_ufo=args.force_ufo, force_city_auto_add=args.force_city_auto_add, scale=scale)

    if path and args.upload:
        upload_to_chatwork(path, args.upload, args.message)
