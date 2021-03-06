from fastapi import FastAPI
from fastapi.testclient import TestClient

from IPython import embed
from sqlalchemy import create_engine
from app.database import Base
from app.main import app
import pytest
from fastapi.encoders import jsonable_encoder
from app.database import SessionLocal
from app import crud
from app.schemas import UserCreate
from os import getenv

engine = create_engine(getenv("DATABASE_URL"))
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def cleanup():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_can_get_all_users(db, cleanup):
    email = "dan@example.com"
    password = "123456"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(db, user=user_in)
    email2 = "bob@example.com"
    password = "123456"
    user_in2 = UserCreate(email=email2, password=password)
    user2 = crud.create_user(db, user=user_in2)
    response = client.get("/users/")
    assert response.status_code == 200
    resp = response.json()
    assert resp[0]['email'] == 'dan@example.com'
    assert resp[1]['email'] == 'bob@example.com'
    assert len(resp) == 2

def test_can_get_a_single_user(db, cleanup):
    email = "dan@example.com"
    password = "123456"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(db, user=user_in)
    response = client.get("/users/1")
    assert response.status_code == 200
    resp = response.json()
    assert resp['email'] == 'dan@example.com'
    assert resp['id'] == 1
    assert resp['favorites'] == []

def test_it_can_register_a_user(db, cleanup):
    email = 'bob@example.com'
    password = "123456"
    response = client.post("/users/register",
    json={"email": email, "password": password})
    assert response.status_code == 200
    resp = response.json()
    assert resp['email'] == email
    assert resp['id'] == 1

def test_it_cant_register_a_user_without_email(db, cleanup):
    email = 'bob'
    password = '123456'
    response = client.post("/users/register",
    json={"email": email, "password": password})
    resp = response.json()
    assert resp['detail'][0]['msg'] == 'value is not a valid email address'

def test_it_can_update_a_user(db, cleanup):
    email = "dan@example.com"
    password = "123456"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(db, user=user_in)
    update_response = client.put(f"/users/{user.id}", 
    json={"username": "chunky_lover"})
    assert update_response.status_code == 200

    resp = update_response.json()
    assert resp['username'] == 'chunky_lover'

    update_response2 = client.put(f"/users/{user.id}", 
    json={"email": "chunky_lover@gmail.com", "image": "dancing_cat.jpg"})
    assert update_response2.status_code == 200
    resp2 = update_response2.json()
    assert resp2['image'] == "dancing_cat.jpg"
    assert resp2['email'] == 'chunky_lover@gmail.com'

def test_it_cant_update_a_user_that_doesnt_exist(db, cleanup):
    update_response = client.put("/users/1",
    json={"username": "chunky_lover", "email": "bob@example.com"})
    assert update_response.status_code == 404

def test_it_can_update_a_users_password(db, cleanup):
    email = "dan@example.com"
    password = "123456"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(db, user=user_in)
    update_response = client.put(f"/users/{user.id}", 
    json={"password": "apple"})
    assert update_response.status_code == 200

    response = client.post("/login/token",
    data={"username": email, "password": 'apple'})
    token = response.json()
    assert response.status_code == 200
    assert "access_token" in token
    assert token["access_token"]