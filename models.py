from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    industry: Mapped[str] = mapped_column(String, nullable=False)
    website: Mapped[str | None] = mapped_column(String, nullable=True)

    employees: Mapped[list["Employee"]] = relationship(back_populates="organization")


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    department: Mapped[str] = mapped_column(String, nullable=False)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    hired_at: Mapped[str] = mapped_column(String, nullable=False)
    org_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )

    organization: Mapped["Organization | None"] = relationship(
        back_populates="employees"
    )


# Mapping from strawberry (camelCase) field name -> SQLAlchemy column attribute
EMPLOYEE_FIELD_COLUMNS = {
    "id": Employee.id,
    "firstName": Employee.first_name,
    "lastName": Employee.last_name,
    "email": Employee.email,
    "department": Employee.department,
    "salary": Employee.salary,
    "hiredAt": Employee.hired_at,
    "orgId": Employee.org_id,
}

ORGANIZATION_FIELD_COLUMNS = {
    "id": Organization.id,
    "name": Organization.name,
    "industry": Organization.industry,
    "website": Organization.website,
}