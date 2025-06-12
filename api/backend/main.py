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

# 장바구니 담기
@app.post('/api/products')
def add_to_cart(item:CartItem):
    db=SessionLocal()
    cart = Cart(user_id=item.user_id, product_id = item.product_id, quantity = item.quantity)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    db.close()
    return {"success":True, "message":"장바구니에 담겼습니다.", "cart_id":cart.id}

# 장바구니 조회  /api/cart?user_id=1   ?키=벨류&키=벨류  쿼리파라메터
from fastapi import Query
@app.get('/api/cart')
def get_cart(user_id: int = Query(...), db:Session=Depends(get_db)):
    items = db.query(Cart).filter(Cart.user_id == user_id).all()
    return [     
        {
            'product_id':item.product_id ,
            'quantity':item.quantity
        }
     for item in items
    ]


# 주문 요청(장바구니 상품 주문)
@app.post('/api/order')
def place_order(order : OrderRequest, db:Session = Depends(get_db)):
    cart_items = db.query(Cart).filter(Cart.user_id == order.user_id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="장바구니가 비어있습니다.")
    for item in cart_items:
        new_order = Order(
            user_id = item.user_id,
            product_id = item.product_id,
            quantity = item.quantity
        )
        db.add(new_order)
        db.delete(item)
        db.refresh(new_order)
    db.commit()
    return {"success":True, "message" : "주문이 완료되었습니다."}

# 주문 목록 조회
@app.get('/api/order', response_model=List[OrderOut])
def get_orders(user_id:int = Query(...), db:Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    return orders
