from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_connection
from fastapi import UploadFile, File
import shutil
import os

app = FastAPI()

# 🔥 CORS (very important for Flutter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# 📦 MODELS (THIS WAS MISSING)
# ============================

class LoginRequest(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    phone: str
    rollno: str
    course: str
    first_name: str
    last_name: str


class UserUpdate(BaseModel):
    username: str
    email: str
    phone: str
    rollno: str
    course: str
    first_name: str
    last_name: str


# ============================
# 🔐 LOGIN ROUTE
# ============================

@app.post("/login")
def login(data: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, username FROM users WHERE email=%s AND password=%s",
        (data.email, data.password),
    )

    user = cur.fetchone()

    cur.close()
    conn.close()

    if user:
        return {
            "message": "Login successful",
            "user_id": user[0],
            "username": user[1]
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# ============================
# 👤 GET ALL USERS
# ============================

@app.get("/users")
def get_users():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, username, email, phone, rollno, course, first_name, last_name
        FROM users
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id": r[0],
            "username": r[1],
            "email": r[2],
            "phone": r[3],
            "rollno": r[4],
            "course": r[5],
            "first_name": r[6],
            "last_name": r[7],
        }
        for r in rows
    ]


# ============================
# ➕ ADD USER
# ============================

@app.post("/users")
def add_user(user: UserCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users 
        (username, password, email, phone, rollno, course, first_name, last_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user.username,
            user.password,
            user.email,
            user.phone,
            user.rollno,
            user.course,
            user.first_name,
            user.last_name,
        ),
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "User added successfully"}


# ============================
# ✏️ UPDATE USER
# ============================

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET username=%s, email=%s, phone=%s,
            rollno=%s, course=%s,
            first_name=%s, last_name=%s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id=%s
        """,
        (
            user.username,
            user.email,
            user.phone,
            user.rollno,
            user.course,
            user.first_name,
            user.last_name,
            user_id,
        ),
    )

    conn.commit()

    cur.close()
    conn.close()

    return {"message": "User updated successfully"}
# ============================
# 🗑 DELETE USER
# ============================

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()

    cur.close()
    conn.close()

    return {"message": "User deleted successfully"}


# ============================
# 🔍 SEARCH USER
# ============================

@app.get("/search")
def search_users(query: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, username, email, phone
        FROM users
        WHERE username ILIKE %s
        OR email ILIKE %s
        OR phone LIKE %s
        """,
        (f"%{query}%", f"%{query}%", f"%{query}%"),
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id": r[0],
            "username": r[1],
            "email": r[2],
            "phone": r[3],
        }
        for r in rows
    ]


# ============================
# 👤 GET SINGLE USER
# ============================

@app.get("/users/{user_id}")
def get_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, username, email, phone, rollno, course, first_name, last_name
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )

    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user[0],
        "username": user[1],
        "email": user[2],
        "phone": user[3],
        "rollno": user[4],
        "course": user[5],
        "first_name": user[6],
        "last_name": user[7],
    }

@app.post("/upload-profile/{user_id}")
def upload_profile(user_id: int, file: UploadFile = File(None)):  # 👈 optional
    if file is None:
        return {"message": "No file uploaded"}

    file_location = f"uploads/{file.filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET profile_image=%s WHERE id=%s",
        (file_location, user_id),
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Image uploaded"}