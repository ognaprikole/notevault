import bcrypt
from fastapi import FastAPI, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from fastapi import Response, Request, Cookie
from typing import Optional
import secrets
from pathlib import Path
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from backend.database import init_db, get_db, User, Note

from backend.database import init_db, get_db, User

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
app = FastAPI(title="NoteVault")


@app.get("/")
def root():
    return RedirectResponse("/login")


@app.get("/login")
def login_page():
    html = (STATIC / "login.html").read_text(encoding="utf-8")
    return HTMLResponse(html)

@app.get("/static/style.css")
def css():
    return FileResponse(STATIC / "style.css")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

def current_user(session: Optional[str] = Cookie(default=None)) -> str:
    if not session or session not in sessions:
        raise HTTPException(status_code=401, detail="Не вошёл")
    return sessions[session]


@app.get("/api/notes")
def list_notes(db: Session = Depends(get_db), username: str = Depends(current_user)):
    user = db.query(User).filter(User.username == username).first()
    notes = db.query(Note).filter(Note.user_id == user.id).order_by(Note.id.desc()).all()
    return [
        {"id": n.id, "title": n.title, "body": n.body}
        for n in notes
    ]


@app.post("/api/notes")
def create_note(
    title: str = Form(...),
    body: str = Form(""),
    db: Session = Depends(get_db),
    username: str = Depends(current_user),
):
    user = db.query(User).filter(User.username == username).first()
    note = Note(title=title.strip() or "Без названия", body=body, user_id=user.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "title": note.title, "body": note.body}


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), username: str = Depends(current_user)):
    user = db.query(User).filter(User.username == username).first()
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Нет такой заметки")
    db.delete(note)
    db.commit()
    return {"ok": True}


@app.on_event("startup")
def on_startup():
    init_db()
    print("DB ready: notevault.db")


@app.get("/ping")
def ping():
    return {"message": "pong", "project": "NoteVault"}


@app.post("/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip().lower()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Имя слишком короткое")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Пароль слишком короткий")

    exists = db.query(User).filter(User.username == username).first()
    if exists:
        raise HTTPException(status_code=400, detail="Такой пользователь уже есть")

    user = User(
        username=username,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    return {"ok": True, "username": username}


sessions: dict[str, str] = {}


@app.post("/login")
def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip().lower()
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token = secrets.token_hex(16)
    sessions[token] = username
    response.set_cookie(key="session", value=token, httponly=True)
    return {"ok": True, "username": username}


@app.get("/me")
def me(session: Optional[str] = Cookie(default=None)):
    if not session or session not in sessions:
        raise HTTPException(status_code=401, detail="Не вошёл")
    return {"username": sessions[session]}


@app.post("/logout")
def logout(response: Response, session: Optional[str] = Cookie(default=None)):
    if session and session in sessions:
        del sessions[session]
    response.delete_cookie("session")
    return {"ok": True}

@app.get("/notes")
def notes_page():
    html = (STATIC / "notes.html").read_text(encoding="utf-8")
    return HTMLResponse(html)

@app.post("/api/notes/{note_id}/edit")
def edit_note(
    note_id: int,
    title: str = Form(...),
    body: str = Form(""),
    db: Session = Depends(get_db),
    username: str = Depends(current_user),
):
    user = db.query(User).filter(User.username == username).first()
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Нет такой заметки")
    note.title = title.strip() or "Без названия"
    note.body = body
    db.commit()
    return {"id": note.id, "title": note.title, "body": note.body}