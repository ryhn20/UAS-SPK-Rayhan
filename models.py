from sqlalchemy import String, Integer, Column
from sqlalchemy.orm import declarative_base


Base = declarative_base()

class Tv(Base):
    __tablename__ = "tbl_tv"
    nomor = Column(Integer, primary_key=True)
    nama_tv = Column(String)
    layar = Column(Integer)
    resolution = Column(String)
    wifi = Column(String)
    hdmi = Column(String) 
    harga = Column(String) 

    def _repr_(self):
        return f"Tv(type={self.type!r}, nama_tv={self.nama_tv!r}, layar={self.layar!r}, resolution={self.resolution!r}, wifi={self.wifi!r}, hdmi={self.hdmi!r}, harga={self.harga!r}, benefit={self.benefit!r})"