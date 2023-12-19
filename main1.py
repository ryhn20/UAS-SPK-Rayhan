import sys
from colorama import Fore, Style
from models import Base, Tv
from engine import engine
from tabulate import tabulate

from sqlalchemy import select
from sqlalchemy.orm import Session
from settings import DEV_SCALE

session = Session(engine)


def create_table():
    Base.metadata.create_all(engine)
    print(f'{Fore.GREEN}[Success]: {Style.RESET_ALL}Database has created!')


def review_data():
    query = select(Tv)
    for tv in session.scalars(query):
        print(tv)


class BaseMethod():

    def __init__(self):
        # 1-5
        self.raw_weight = {'layar': 8, 'resolution': 9,
                            'wifi': 1, 'hdmi': 2, 'harga': 7}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(Tv.nomor, Tv.nama_tv, Tv.layar, Tv.resolution,
                       Tv.wifi, Tv.hdmi, Tv.harga)
        result = session.execute(query).fetchall()
        return [{'nomor': tv.nomor, 'nama_tv': tv.nama_tv, 'layar': tv.layar, 'resolution': tv.resolution,
                 'wifi': tv.wifi, 'hdmi': tv.hdmi, 'harga': tv.harga} for tv in result]

    @property
    def normalized_data(self):
        # x/max [benefit]
        # min/x [cost]
        layar_values = []  # max
        resolution_values = []  # max
        wifi_values = []  # max
        hdmi_values = []  # max
        harga_values = []  # min

        for data in self.data:
            # Layar
            layar_spec = data['layar']
            numeric_values = [int(value.split()[0]) for value in layar_spec.split(
                ',') if value.split()[0].isdigit()]
            max_layar_value = max(numeric_values) if numeric_values else 1
            layar_values.append(max_layar_value)

            # Resolution
            resolution_spec = data['resolution']
            resolution_numeric_values = [int(
                value.split()[0]) for value in resolution_spec.split() if value.split()[0].isdigit()]
            max_resolution_value = max(
                resolution_numeric_values) if resolution_numeric_values else 1
            resolution_values.append(max_resolution_value)

            # Wifi
            wifi_spec = data['wifi']
            wifi_numeric_values = [
                int(value) for value in wifi_spec.split() if value.isdigit()]
            max_wifi_value = max(
                wifi_numeric_values) if wifi_numeric_values else 1
            wifi_values.append(max_wifi_value)

            # Hdmi
            hdmi_value = DEV_SCALE['hdmi'].get(data['hdmi'], 1)
            hdmi_values.append(hdmi_value)

            # Harga
            harga_cleaned = ''.join(
                char for char in data['harga'] if char.isdigit())
            harga_values.append(float(harga_cleaned)
                                if harga_cleaned else 0)  # Convert to float

        return [
            {'nomor': data['nomor'],
             'layar': layar_value / max(layar_values),
             'resolution': resolution_value / max(resolution_values),
             'wifi': wifi_value / max(wifi_values),
             'hdmi': hdmi_value / max(hdmi_values),
             # To avoid division by zero
             'harga': min(harga_values) / max(harga_values) if max(harga_values) != 0 else 0
             }
            for data, layar_value, resolution_value, wifi_value, hdmi_value, harga_value
            in zip(self.data, layar_values, resolution_values, wifi_values, hdmi_values, harga_values)
        ]


class WeightedProduct(BaseMethod):
    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = [
            {
                'nomor': row['nomor'],
                'produk': row['layar']**self.weight['layar'] *
                          row['resolution']**self.weight['resolution'] *
                          row['wifi']**self.weight['wifi'] *
                          row['hdmi']**self.weight['hdmi'] *
                          row['harga']**self.weight['harga']
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'nomor': product['nomor'],
                'layar': product['produk'] / self.weight['layar'],
                'resolution': product['produk'] / self.weight['resolution'],
                'wifi': product['produk'] / self.weight['wifi'],
                'hdmi': product['produk'] / self.weight['hdmi'],
                'harga': product['produk'] / self.weight['harga'],
                'score': product['produk']  # Nilai skor akhir
            }
            for product in sorted_produk
        ]
        return sorted_data


class SimpleAdditiveWeighting(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['nomor']:
                  round(row['layar'] * weight['layar'] +
                        row['resolution'] * weight['resolution'] +
                        row['wifi'] * weight['wifi'] +
                        row['hdmi'] * weight['hdmi'] +
                        row['harga'] * weight['harga'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result


def run_saw():
    saw = SimpleAdditiveWeighting()
    result = saw.calculate
    print(tabulate(result.items(), headers=['Nomor', 'Score'], tablefmt='pretty'))


def run_wp():
    wp = WeightedProduct()
    result = wp.calculate
    headers = result[0].keys()
    rows = [
        {k: round(v, 4) if isinstance(v, float) else v for k, v in val.items()}
        for val in result
    ]
    print(tabulate(rows, headers="keys", tablefmt='grid'))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == 'create_table':
            create_table()
        elif arg == 'saw':
            run_saw()
        elif arg == 'wp':
            run_wp()
        else:
            print('command not found')
