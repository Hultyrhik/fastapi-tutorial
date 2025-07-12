from fastapi import FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select, func, col

import string
import random


class HeroBase(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: int | None = Field(default=None, index=True)


class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class HeroCreate(HeroBase):
    pass


class HeroPublic(HeroBase):
    id: int


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def id_generator(size: int=6, chars:str=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def create_data():
    with Session(engine) as session:
        for _ in range(50):
            model_db = Hero(
                name=id_generator(),
                secret_name=id_generator(),
                age=random.randint(0,100)
            )
            session.add(model_db)
            session.commit()

app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()

    create_data()


@app.post("/heroes/", response_model=HeroPublic)
def create_hero(hero: HeroCreate):
    with Session(engine) as session:
        db_hero = Hero.model_validate(hero)
        session.add(db_hero)
        session.commit()
        session.refresh(db_hero)
        return db_hero


@app.get(
        "/heroes/",
        response_model=list[HeroPublic]
        )
def read_heroes(page: int = Query(default=1, ge=1), per_page: int = Query(alias="per-page", default=100, le=100, ge=0)):
    with Session(engine) as session:
        count_statement = select(func.count()).select_from(Hero).where(col(Hero.age) > 0)
        total = session.exec(count_statement).one()
        
        pages = (total // per_page) + 1
        page = page - 1
        offset = per_page * page
        
        heroes = session.exec(select(Hero).offset(offset).limit(per_page)).all()
        return heroes
        return {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
        }



@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(hero_id: int):
    with Session(engine) as session:
        hero = session.get(Hero, hero_id)
        if not hero:
            raise HTTPException(status_code=404, detail="Hero not found")
        return hero