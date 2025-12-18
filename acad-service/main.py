from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, BigInteger, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
import os

app = FastAPI(title="Academic Service API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_HOST = os.getenv("DB_HOST", "acad-db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "db_kelas")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Mahasiswa(Base):
    __tablename__ = "mahasiswa"
    
    nim = Column(String(10), primary_key=True)
    nama = Column(String(100), nullable=False)
    jurusan = Column(String(50))
    angkatan = Column(Integer)
    
    krs_list = relationship("KRS", back_populates="mahasiswa")

class MataKuliah(Base):
    __tablename__ = "mata_kuliah"
    
    kode_mk = Column(String(10), primary_key=True)
    nama_mk = Column(String(100), nullable=False)
    sks = Column(Integer, nullable=False)
    
    krs_list = relationship("KRS", back_populates="mata_kuliah")

class KRS(Base):
    __tablename__ = "krs"
    
    id_krs = Column(BigInteger, primary_key=True, autoincrement=True)
    nim = Column(String(10), ForeignKey("mahasiswa.nim"), nullable=False)
    kode_mk = Column(String(10), ForeignKey("mata_kuliah.kode_mk"), nullable=False)
    nilai = Column(String(2), ForeignKey("bobot_nilai.nilai"))
    semester = Column(Integer)
    
    mahasiswa = relationship("Mahasiswa", back_populates="krs_list")
    mata_kuliah = relationship("MataKuliah", back_populates="krs_list")
    bobot_rel = relationship("BobotNilai")

class BobotNilai(Base):
    __tablename__ = "bobot_nilai"
    
    nilai = Column(String(2), primary_key=True)
    bobot = Column(Float, nullable=False)

class MahasiswaSchema(BaseModel):
    nim: str
    nama: str
    jurusan: str
    angkatan: int
    
    class Config:
        from_attributes = True

class MataKuliahSchema(BaseModel):
    kode_mk: str
    nama_mk: str
    sks: int
    
    class Config:
        from_attributes = True

class KRSSchema(BaseModel):
    nim: str
    kode_mk: str
    nilai: str
    semester: int
    
    class Config:
        from_attributes = True

class IPSRequest(BaseModel):
    nim: str
    semester: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"status": "Academic Service Online", "type": "SQLAlchemy ORM"}

@app.get("/health")
async def health_check():
    return {"status": "Academic Service running", "timestamp": datetime.now().isoformat()}

@app.get("/api/acad/mahasiswa")
async def get_all_mahasiswa(db: Session = Depends(get_db)):
    try:
        mahasiswa_list = db.query(Mahasiswa).order_by(Mahasiswa.nim).all()
        return {
            "success": True,
            "data": [
                {
                    "nim": mhs.nim,
                    "nama": mhs.nama,
                    "jurusan": mhs.jurusan,
                    "angkatan": mhs.angkatan
                }
                for mhs in mahasiswa_list
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/acad/mahasiswa/{nim}")
async def get_mahasiswa(nim: str, db: Session = Depends(get_db)):
    try:
        mhs = db.query(Mahasiswa).filter(Mahasiswa.nim == nim).first()
        
        if not mhs:
            raise HTTPException(status_code=404, detail="Mahasiswa not found")
        
        return {
            "success": True,
            "data": {
                "nim": mhs.nim,
                "nama": mhs.nama,
                "jurusan": mhs.jurusan,
                "angkatan": mhs.angkatan
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/acad/mahasiswa")
async def create_mahasiswa(mhs: MahasiswaSchema, db: Session = Depends(get_db)):
    try:
        new_mhs = Mahasiswa(
            nim=mhs.nim,
            nama=mhs.nama,
            jurusan=mhs.jurusan,
            angkatan=mhs.angkatan
        )
        db.add(new_mhs)
        db.commit()
        db.refresh(new_mhs)
        
        return {
            "success": True,
            "message": "Mahasiswa created successfully",
            "data": {
                "nim": new_mhs.nim,
                "nama": new_mhs.nama,
                "jurusan": new_mhs.jurusan,
                "angkatan": new_mhs.angkatan
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/acad/matakuliah")
async def get_all_matakuliah(db: Session = Depends(get_db)):
    try:
        matkul_list = db.query(MataKuliah).order_by(MataKuliah.kode_mk).all()
        return {
            "success": True,
            "data": [
                {
                    "kode_mk": mk.kode_mk,
                    "nama_mk": mk.nama_mk,
                    "sks": mk.sks
                }
                for mk in matkul_list
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/acad/matakuliah")
async def create_matakuliah(mk: MataKuliahSchema, db: Session = Depends(get_db)):
    try:
        new_mk = MataKuliah(
            kode_mk=mk.kode_mk,
            nama_mk=mk.nama_mk,
            sks=mk.sks
        )
        db.add(new_mk)
        db.commit()
        db.refresh(new_mk)
        
        return {
            "success": True,
            "message": "Mata kuliah created successfully",
            "data": {
                "kode_mk": new_mk.kode_mk,
                "nama_mk": new_mk.nama_mk,
                "sks": new_mk.sks
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/acad/krs/{nim}")
async def get_krs(nim: str, semester: Optional[int] = None, db: Session = Depends(get_db)):
    try:
        query = db.query(
            KRS.id_krs,
            KRS.nim,
            Mahasiswa.nama.label('nama_mahasiswa'),
            MataKuliah.kode_mk,
            MataKuliah.nama_mk,
            MataKuliah.sks,
            KRS.nilai,
            KRS.semester
        ).join(
            Mahasiswa, KRS.nim == Mahasiswa.nim
        ).join(
            MataKuliah, KRS.kode_mk == MataKuliah.kode_mk
        ).filter(KRS.nim == nim)
        
        if semester:
            query = query.filter(KRS.semester == semester)
        
        results = query.order_by(KRS.semester, MataKuliah.kode_mk).all()
        
        krs_list = []
        for row in results:
            krs_list.append({
                "id_krs": row.id_krs,
                "nim": row.nim,
                "nama_mahasiswa": row.nama_mahasiswa,
                "kode_mk": row.kode_mk,
                "nama_mk": row.nama_mk,
                "sks": row.sks,
                "nilai": row.nilai,
                "semester": row.semester
            })
        
        return {"success": True, "data": krs_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/acad/krs")
async def create_krs(krs: KRSSchema, db: Session = Depends(get_db)):
    try:
        new_krs = KRS(
            nim=krs.nim,
            kode_mk=krs.kode_mk,
            nilai=krs.nilai,
            semester=krs.semester
        )
        db.add(new_krs)
        db.commit()
        db.refresh(new_krs)
        
        return {
            "success": True,
            "message": "KRS created successfully",
            "data": {
                "id_krs": new_krs.id_krs,
                "nim": new_krs.nim,
                "kode_mk": new_krs.kode_mk,
                "nilai": new_krs.nilai,
                "semester": new_krs.semester
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/acad/calculate-ips")
async def calculate_ips(request: IPSRequest, db: Session = Depends(get_db)):
    try:
        results = db.query(
            MataKuliah.sks,
            BobotNilai.bobot,
            MataKuliah.nama_mk,
            KRS.nilai
        ).join(
            MataKuliah, KRS.kode_mk == MataKuliah.kode_mk
        ).join(
            BobotNilai, KRS.nilai == BobotNilai.nilai
        ).filter(
            KRS.nim == request.nim,
            KRS.semester == request.semester
        ).all()
        
        if not results:
            raise HTTPException(status_code=404, detail="No KRS data found for this semester")
        
        total_bobot = 0
        total_sks = 0
        details = []
        
        for row in results:
            sks = row.sks
            bobot = row.bobot
            nama_mk = row.nama_mk
            nilai = row.nilai
            
            bobot_x_sks = bobot * sks
            total_bobot += bobot_x_sks
            total_sks += sks
            
            details.append({
                "mata_kuliah": nama_mk,
                "sks": sks,
                "nilai": nilai,
                "bobot": bobot,
                "bobot_x_sks": round(bobot_x_sks, 2)
            })
        
        ips = total_bobot / total_sks if total_sks > 0 else 0
        
        mhs = db.query(Mahasiswa).filter(Mahasiswa.nim == request.nim).first()
        nama_mahasiswa = mhs.nama if mhs else "Unknown"
        
        return {
            "success": True,
            "data": {
                "nim": request.nim,
                "nama": nama_mahasiswa,
                "semester": request.semester,
                "ips": round(ips, 2),
                "total_sks": total_sks,
                "total_bobot": round(total_bobot, 2),
                "details": details
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/acad/db-status")
async def database_status(db: Session = Depends(get_db)):
    try:
        count_mhs = db.query(Mahasiswa).count()
        count_mk = db.query(MataKuliah).count()
        count_krs = db.query(KRS).count()
        
        result = db.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        
        return {
            "status": "connected",
            "database": "PostgreSQL",
            "version": version.split()[0:2],
            "statistics": {
                "total_mahasiswa": count_mhs,
                "total_mata_kuliah": count_mk,
                "total_krs": count_krs
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)