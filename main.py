from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select


class RegionBase(SQLModel):
    name: str


class Region(RegionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cities: list["City"] = Relationship(back_populates="region")


class RegionPublic(RegionBase):
    id: int


class CityBase(SQLModel):
    name: str
    region_id: int = Field(foreign_key="region.id")


class City(CityBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    region: Region = Relationship(back_populates="cities")
    heroes: list["Hero"] = Relationship(back_populates="city")


class CityPublic(CityBase):
    id: int


class CityPublicWithRelations(CityPublic):
    region: RegionPublic


class TeamBase(SQLModel):
    name: str = Field(index=True)
    headquarters: str


class Team(TeamBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    heroes: list["Hero"] = Relationship(back_populates="team")


class TeamCreate(TeamBase):
    pass


class TeamPublic(TeamBase):
    id: int


class TeamUpdate(SQLModel):
    id: int | None = None
    name: str | None = None
    headquarters: str | None = None


class HeroBase(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: int | None = Field(default=None, index=True)

    team_id: int | None = Field(default=None, foreign_key="team.id")
    city_id: int = Field(foreign_key="city.id")


class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    team: Team | None = Relationship(back_populates="heroes")
    city: City = Relationship(back_populates="heroes")


class HeroPublic(HeroBase):
    id: int


class HeroCreate(HeroBase):
    pass


class HeroUpdate(SQLModel):
    name: str | None = None
    secret_name: str | None = None
    age: int | None = None
    team_id: int | None = None


class HeroPublicWithTeam(HeroPublic):
    team: TeamPublic | None = None
    city: CityPublicWithRelations


class TeamPublicWithHeroes(TeamPublic):
    heroes: list[HeroPublic] = []


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def create_teams():
    generator = get_session()
    session = next(generator)

    db_model = Team(name="X-men", headquarters="House")
    db_model2 = Team(name="Sinister six", headquarters="roof")
    session.add(db_model)
    session.add(db_model2)

    session.commit()


def create_heroes():
    session = next(get_session())
    db_model = Hero(name="Spider", secret_name="Pak", age=23, team_id=1, city_id=1)
    db_model2 = Hero(name="Rust", secret_name="Tone", age=37, team_id=2, city_id=2)
    db_model3 = Hero(name="Aqua", secret_name="Mor", age=42, team_id=1, city_id=3)
    session.add(db_model)
    session.add(db_model2)
    session.add(db_model3)
    session.commit()


def create_region():
    session = next(get_session())
    db_list: list[Region] = []
    db_model = Region(name="Texas")
    db_list.append(db_model)
    db_model = Region(name="Washington")
    db_list.append(db_model)
    db_model = Region(name="Milwakee")
    db_list.append(db_model)
    for db_model in db_list:
        session.add(db_model)
        session.commit()


def create_city():
    session = next(get_session())
    db_list: list[City] = []
    db_model = City(name="Austin", region_id=1)
    db_list.append(db_model)
    db_model = City(name="Washington D.C", region_id=2)
    db_list.append(db_model)
    db_model = City(name="Wiskonsin", region_id=3)
    db_list.append(db_model)
    for db_model in db_list:
        session.add(db_model)
        session.commit()


def get_session():
    with Session(engine) as session:
        yield session


app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    create_region()
    create_city()
    create_teams()
    create_heroes()


@app.post("/heroes/", response_model=HeroPublic)
def create_hero(*, session: Session = Depends(get_session), hero: HeroCreate):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero


@app.get("/heroes/", response_model=list[HeroPublicWithTeam])
def read_heroes(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes


@app.get("/heroes/{hero_id}", response_model=HeroPublicWithTeam)
def read_hero(*, session: Session = Depends(get_session), hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(
    *, session: Session = Depends(get_session), hero_id: int, hero: HeroUpdate
):
    db_hero = session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_data = hero.model_dump(exclude_unset=True)
    db_hero.sqlmodel_update(hero_data)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero


@app.delete("/heroes/{hero_id}")
def delete_hero(*, session: Session = Depends(get_session), hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}


@app.post("/teams/", response_model=TeamPublic)
def create_team(*, session: Session = Depends(get_session), team: TeamCreate):
    db_team = Team.model_validate(team)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team


@app.get("/teams/", response_model=list[TeamPublic])
def read_teams(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    teams = session.exec(select(Team).offset(offset).limit(limit)).all()
    return teams


@app.get("/teams/{team_id}", response_model=TeamPublicWithHeroes)
def read_team(*, team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@app.patch("/teams/{team_id}", response_model=TeamPublic)
def update_team(
    *,
    session: Session = Depends(get_session),
    team_id: int,
    team: TeamUpdate,
):
    db_team = session.get(Team, team_id)
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
    team_data = team.model_dump(exclude_unset=True)
    db_team.sqlmodel_update(team_data)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team


@app.delete("/teams/{team_id}")
def delete_team(*, session: Session = Depends(get_session), team_id: int):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    session.delete(team)
    session.commit()
    return {"ok": True}
