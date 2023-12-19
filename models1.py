from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Tv(Base):
    __tablename__ = "tbl_tv"
    nomor = Column(Integer, primary_key=True)
    nama_tv = Column(String(255))
    layar = Column(String(255))
    resolution = Column(String(255))
    wifi = Column(String(255))
    hdmi = Column(String(255))
    harga = Column(String(255))

    def __init__(self, nama_tv, layar, resolution, wifi, hdmi, harga):
        self.nama_tv = nama_tv
        self.layar = layar
        self.resolution = resolution
        self.wifi = wifi
        self.hdmi = hdmi
        self.harga = harga

    def calculate_score(self, dev_scale):
        score = 0
        score += self.layar * dev_scale['layar']
        score += self.resolution * dev_scale['resolution']
        score += self.wifi * dev_scale['wifi']
        score += self.hdmi * dev_scale['hdmi']
        score -= self.harga * dev_scale['harga']
        return score

    def __repr__(self):
        return f"Tv(nama_tv={self.nama_tv!r}, layar={self.layar!r}, resolution={self.resolution!r}, wifi={self.wifi!r}, hdmi={self.hdmi!r}, harga={self.harga!r})"
