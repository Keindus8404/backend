from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from model import *
from database import SessionLocal, engine
from schemas import *
from typing import List

# FastAPI 생성
app = FastAPI()

# 앱을 실행하면 DB에 정의된 모든 테이블을 생성
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal() # 세선 객체 생성
    try:
        yield db # 동기화. 종속된 함수에 세션 주입
    finally:
        db.close() # 요청이 끝나면 자동으로 세션 종료

# 회원가입용 모델 pydantic
class RegisterRequest(BaseModel):
    username : str
    email : str
    password : str

# 라우터(요청에 응답) 정의
@app.post('/api/register')
def register_user(user : RegisterRequest, db : Session=Depends(get_db)):
    # 같은 사용자가 있는지 db에서 조회
    exsiting_user = db.query(User).filter(User.username == user.username).first()
    # 같은 사용자가 있으면 400에러
    if exsiting_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다.")
    # 새 유저에 대한 객체(인스턴스) 생성
    new_user = User(
        username = user.username,
        email = user.email,
        password = user.password
    )
    # db commit하는 과정
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # db에서 자동 생성된 id를 유저 인스턴스에 할당
    return {"success":True, 'message':'회원가입 성공', 'user_id': new_user.id}

@app.post('/api/login')
def login(user:UserCreate, db:Session=Depends(get_db)):
    # 사용자 테이블에서 입력한 이름과 패스워드락 있는지 조회
    found = db.query(User).filter(User.username == user.username, User.password == user.password).first()
    if not found:
        raise HTTPException(status_code=400, detail="로그인 실패")
    return {"success":True,'message':'로그인 성공'}

# 사용자의 고유 id로 user 테이블의 데이터 조회
@app.get('/api/users/{user_id}', response_model=UserResponse)
def get_user(user_id:int, db:Session=Depends(get_db)):
    user = db.query(User).filter(User.id==user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='존재하지 않는 유저입니다.')

# 전체상품 조회
@app.get('/api/products', response_model=List[ProductOut])
def get_produc():
    db = SessionLocal()
    products = db.query(Product).all()
    db.close()
    return products

# 상품 등록
@app.post('/api/products')
def create_product(product:ProductCreate):
    db = SessionLocal()
    product = Product(name = product.name, price = product.price)
    db.add(product)
    db.commit()
    db.refresh(product)
    db.close()
    return {"success":True, "message":"상품 등록 완료", "product_id":product.id}