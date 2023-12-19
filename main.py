from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api
from models import Tv as TvModels
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from tabulate import tabulate

session = Session(engine)

app = Flask(__name__)
api = Api(app)


class BaseMethod():

    def __init__(self):
        self.raw_weight = {'nama_tv': 4,'layar': 8, 'resolution':9,'wifi': 1, 
                           'hdmi': 2, 'harga': 7}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(TvModels.nomor, TvModels.nama_tv, TvModels.layar, TvModels.resolution,
                       TvModels.wifi, TvModels.hdmi, TvModels.harga)
        result = session.execute(query).fetchall()
        print(result)
        return [{'nomor': Tv.nomor,'nama_tv': Tv.nama_tv, 'layar': Tv.layar,
                'resolution': Tv.resolution, 'wifi': Tv.wifi, 'hdmi': Tv.hdmi, 'harga': Tv.harga} for Tv in result]

    @property
    def normalized_data(self):
        # x/max [benefit]
        # min/x [cost]
        nama_tv_values = [] # max
        layar_values = []  # max
        resolution_values = []  # max
        wifi_values = []  # max
        hdmi_values = []  # max
        harga_values = []  # min

        for data in self.data:
            # Nama_Tv
            nama_tv_spec = data['nama_tv']
            numeric_values = [int(value.split()[0]) for value in nama_tv_spec.split(
                ',') if value.split()[0].isdigit()]
            max_nama_tv_value = max(numeric_values) if numeric_values else 1
            nama_tv_values.append(max_nama_tv_value)

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
            wifi_numeric_values = [float(value.split()[0]) for value in wifi_spec.split(
            ) if value.replace('.', '').isdigit()]
            max_wifi_value = max(
                wifi_numeric_values) if wifi_numeric_values else 1
            wifi_values.append(max_wifi_value)

            # Hdmi
            hdmi_spec = data['hdmi']
            hdmi_numeric_values = [
                int(value) for value in hdmi_spec.split() if value.isdigit()]
            max_hdmi_value = max(
                hdmi_numeric_values) if hdmi_numeric_values else 1
            hdmi_values.append(max_hdmi_value)

            # Harga
            harga_cleaned = ''.join(
                char for char in data['harga'] if char.isdigit())
            harga_values.append(float(harga_cleaned)
                                if harga_cleaned else 0)  # Convert to float
        
        return [
   {
        'nomor': data['nomor'],
        'nama_tv': nama_tv_value / max(nama_tv_values),
        'layar': layar_value / max(layar_values), 
        'resolution': resolution_value / max(resolution_values),
        'wifi': wifi_value / max(wifi_values),
        'hdmi': hdmi_value / max(hdmi_values),
        'harga': min (harga_values) / max(harga_values) if max(harga_values) != 0 else 0
    }
    for data, nama_tv_value, layar_value, resolution_value, wifi_value, hdmi_value, harga_value
    in zip(self.data, nama_tv_values, layar_values, resolution_values, wifi_values, hdmi_values, harga_values)
]


    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = [
            {
                'nomor': row['nomor'],
                'produk':
                row['nama_tv']**self.weight['nama_tv'] *
                row['layar']**self.weight['layar'] *
                row['resolution']**self.weight['resolution'] *
                row['wifi']**self.weight['wifi'] *
                row['hdmi']**self.weight['hdmi'],
                'harga': row.get('harga', '')
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'ID': product['nomor'],
                'score': round(product['produk'], 3)
            }
            for product in sorted_produk
        ]
        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return sorted(result, key=lambda x: x['score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'tv': sorted(result, key=lambda x: x['score'], reverse=True)}, HTTPStatus.OK.value


class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = [
            {
                'ID': row['nomor'],
                'Score': round(row['layar'] * weight['layar'] +
                               row['resolution'] * weight['resolution'] +
                               row['wifi'] * weight['wifi'] +
                               row['hdmi'] * weight['hdmi'] +
                               row['harga'] * weight['harga'], 3)
            }
            for row in self.normalized_data
        ]
        sorted_result = sorted(result, key=lambda x: x['Score'], reverse=True)
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return sorted(result, key=lambda x: x['Score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'tv': sorted(result, key=lambda x: x['Score'], reverse=True)}, HTTPStatus.OK.value


class Tv(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None

        if page > page_count or page < 1:
            abort(404, description=f'Data Tidak Ditemukan.')
        return {
            'page': page,
            'page_size': page_size,
            'next': next_page,
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = session.query(TvModels).order_by(TvModels.nomor)
        result_set = query.all()
        data = [{'nomor': row.nomor, 'nama_tv': row.nama_tv, 'layar': row.layar,
                 'resolution': row.resolution, 'wifi': row.wifi, 'hdmi': row.hdmi, 'harga': row.harga}
                for row in result_set]
        return self.get_paginated_result('tv/', data, request.args), 200


api.add_resource(Tv, '/tv')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)