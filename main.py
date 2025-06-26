from sqlmodel import Field, SQLModel, create_engine, Session


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: int | None = None


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def create_heroes():
    hero_1 = Hero(name="Dead", secret_name="Dive")
    hero_2 = Hero(name="Spider", secret_name="Piter")
    hero_3 = Hero(name="Iron", secret_name="Tommy", age=48)

    session = Session(engine)

    session.add(hero_1)
    session.add(hero_2)
    session.add(hero_3)
    session.commit()

    session.close()

def main():
    create_db_and_tables()
    create_heroes()

if __name__ == "__main__":
    main()