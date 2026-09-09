from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Employee, Organization

DB_PATH = Path(__file__).parent / "employees.db"

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session():
    return SessionLocal()


def init_db():
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        org_count = session.scalar(select(func.count()).select_from(Organization))
        if org_count == 0:
            session.add_all(
                [
                    Organization(
                        name="Acme Corp",
                        industry="Technology",
                        website="https://acme.example.com",
                    ),
                    Organization(
                        name="Globex",
                        industry="Retail",
                        website="https://globex.example.com",
                    ),
                    Organization(
                        name="Initech",
                        industry="Finance",
                        website="https://initech.example.com",
                    ),
                ]
            )
            session.commit()

        emp_count = session.scalar(select(func.count()).select_from(Employee))
        if emp_count == 0:
            session.add_all(
                [
                    Employee(
                        first_name="Alice",
                        last_name="Johnson",
                        email="alice@example.com",
                        department="Engineering",
                        salary=95000,
                        hired_at="2023-01-15",
                        org_id=1,
                    ),
                    Employee(
                        first_name="Bob",
                        last_name="Smith",
                        email="bob@example.com",
                        department="Marketing",
                        salary=72000,
                        hired_at="2023-03-20",
                        org_id=2,
                    ),
                    Employee(
                        first_name="Charlie",
                        last_name="Brown",
                        email="charlie@example.com",
                        department="Engineering",
                        salary=105000,
                        hired_at="2022-06-10",
                        org_id=1,
                    ),
                    Employee(
                        first_name="Diana",
                        last_name="Lee",
                        email="diana@example.com",
                        department="HR",
                        salary=68000,
                        hired_at="2023-07-01",
                        org_id=3,
                    ),
                    Employee(
                        first_name="Eve",
                        last_name="Martinez",
                        email="eve@example.com",
                        department="Marketing",
                        salary=75000,
                        hired_at="2022-11-30",
                        org_id=2,
                    ),
                ]
            )
            session.commit()