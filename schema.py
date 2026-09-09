import strawberry

from auth import IsAdminOrHR
from db import get_session
import models as m
from sqlalchemy import func, select

EMPLOYEE_FIELD_DEFAULTS = {
    "id": 0,
    "firstName": "",
    "lastName": "",
    "email": "",
    "department": "",
    "salary": 0.0,
    "hiredAt": "",
    "orgId": None,
}

ORGANIZATION_FIELD_DEFAULTS = {
    "id": 0,
    "name": "",
    "industry": "",
    "website": None,
}

EMPLOYEE_FILTER_MAP = {
    "department": (m.Employee.department, "="),
    "min_salary": (m.Employee.salary, ">="),
    "max_salary": (m.Employee.salary, "<="),
    "email_contains": (m.Employee.email, "like"),
}

ORGANIZATION_FILTER_MAP = {
    "name_contains": (m.Organization.name, "like"),
    "industry": (m.Organization.industry, "="),
}


def build_filters(filter_obj, mapping):
    clauses = []
    for field, (column, op) in mapping.items():
        value = getattr(filter_obj, field, None)
        if value is not None:
            if op == "like":
                clauses.append(column.like(f"%{value}%"))
            elif op == ">=":
                clauses.append(column >= value)
            elif op == "<=":
                clauses.append(column <= value)
            else:
                clauses.append(column == value)
    return clauses


def selected_names(info) -> set[str]:
    selections = info.selected_fields[0].selections if info.selected_fields else None
    if not selections:
        return set()
    return {field.name for field in selections}


def dynamic_columns(info, field_columns, always):
    names = selected_names(info)
    columns = {field_columns[n] for n in names if n in field_columns}
    columns.update(always)
    return list(columns)


def employee_from_row(row, names) -> "Employee":
    data = dict(EMPLOYEE_FIELD_DEFAULTS)
    for name in names:
        if name in m.EMPLOYEE_FIELD_COLUMNS:
            data[name] = row._mapping[m.EMPLOYEE_FIELD_COLUMNS[name].key]
    data["id"] = row._mapping["id"]
    data["orgId"] = row._mapping["org_id"]
    return Employee(**data)


def organization_from_row(row, names) -> "Organization":
    data = dict(ORGANIZATION_FIELD_DEFAULTS)
    for name in names:
        if name in m.ORGANIZATION_FIELD_COLUMNS:
            data[name] = row._mapping[m.ORGANIZATION_FIELD_COLUMNS[name].key]
    data["id"] = row._mapping["id"]
    return Organization(**data)


@strawberry.type
class Employee:
    id: int
    firstName: str
    lastName: str
    email: str
    department: str
    salary: float = strawberry.field(permission_classes=[IsAdminOrHR])
    hiredAt: str
    orgId: int | None

    @strawberry.field
    def organization(self, info: strawberry.Info) -> "Organization | None":
        if self.orgId is None:
            return None
        names = selected_names(info)
        columns = dynamic_columns(
            info, m.ORGANIZATION_FIELD_COLUMNS, always=[m.Organization.id]
        )
        row = None
        with get_session() as session:
            row = session.execute(
                select(*columns).where(m.Organization.id == self.orgId)
            ).first()
        return organization_from_row(row, names) if row else None


@strawberry.type
class Organization:
    id: int
    name: str
    industry: str
    website: str | None

    @strawberry.field
    def employees(self, info: strawberry.Info) -> list["Employee"]:
        names = selected_names(info)
        columns = dynamic_columns(
            info, m.EMPLOYEE_FIELD_COLUMNS, always=[m.Employee.org_id, m.Employee.id]
        )
        with get_session() as session:
            rows = session.execute(
                select(*columns)
                .where(m.Employee.org_id == self.id)
                .order_by(m.Employee.id)
            ).all()
        return [employee_from_row(r, names) for r in rows]


@strawberry.input
class EmployeeFilter:
    department: str | None = None
    min_salary: float | None = None
    max_salary: float | None = None
    email_contains: str | None = None


@strawberry.input
class OrganizationFilter:
    name_contains: str | None = None
    industry: str | None = None


@strawberry.type
class Query:
    @strawberry.field
    def employees(
        self,
        info: strawberry.Info,
        limit: int = 50,
        offset: int = 0,
        filter: EmployeeFilter | None = None,
    ) -> list[Employee]:
        names = selected_names(info)
        columns = dynamic_columns(
            info,
            m.EMPLOYEE_FIELD_COLUMNS,
            always=[m.Employee.id, m.Employee.org_id],
        )
        stmt = select(*columns)
        clauses = build_filters(filter, EMPLOYEE_FILTER_MAP)
        if clauses:
            stmt = stmt.where(*clauses)
        stmt = stmt.order_by(m.Employee.id).limit(limit).offset(offset)
        with get_session() as session:
            rows = session.execute(stmt).all()
        return [employee_from_row(r, names) for r in rows]

    @strawberry.field
    def employee_count(
        self,
        filter: EmployeeFilter | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(m.Employee)
        clauses = build_filters(filter, EMPLOYEE_FILTER_MAP)
        if clauses:
            stmt = stmt.where(*clauses)
        with get_session() as session:
            return session.scalar(stmt)

    @strawberry.field
    def employee(self, info: strawberry.Info, id: int) -> Employee | None:
        names = selected_names(info)
        columns = dynamic_columns(
            info,
            m.EMPLOYEE_FIELD_COLUMNS,
            always=[m.Employee.id, m.Employee.org_id],
        )
        with get_session() as session:
            row = session.execute(
                select(*columns).where(m.Employee.id == id)
            ).first()
        return employee_from_row(row, names) if row else None

    @strawberry.field
    def employees_by_department(
        self,
        info: strawberry.Info,
        department: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Employee]:
        names = selected_names(info)
        columns = dynamic_columns(
            info,
            m.EMPLOYEE_FIELD_COLUMNS,
            always=[m.Employee.id, m.Employee.org_id],
        )
        with get_session() as session:
            rows = session.execute(
                select(*columns)
                .where(m.Employee.department == department)
                .order_by(m.Employee.id)
                .limit(limit)
                .offset(offset)
            ).all()
        return [employee_from_row(r, names) for r in rows]

    @strawberry.field
    def organizations(
        self,
        info: strawberry.Info,
        limit: int = 50,
        offset: int = 0,
        filter: OrganizationFilter | None = None,
    ) -> list[Organization]:
        names = selected_names(info)
        columns = dynamic_columns(
            info,
            m.ORGANIZATION_FIELD_COLUMNS,
            always=[m.Organization.id],
        )
        stmt = select(*columns)
        clauses = build_filters(filter, ORGANIZATION_FILTER_MAP)
        if clauses:
            stmt = stmt.where(*clauses)
        stmt = stmt.order_by(m.Organization.id).limit(limit).offset(offset)
        with get_session() as session:
            rows = session.execute(stmt).all()
        return [organization_from_row(r, names) for r in rows]

    @strawberry.field
    def organization_count(
        self,
        filter: OrganizationFilter | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(m.Organization)
        clauses = build_filters(filter, ORGANIZATION_FILTER_MAP)
        if clauses:
            stmt = stmt.where(*clauses)
        with get_session() as session:
            return session.scalar(stmt)

    @strawberry.field
    def organization(self, info: strawberry.Info, id: int) -> Organization | None:
        names = selected_names(info)
        columns = dynamic_columns(
            info,
            m.ORGANIZATION_FIELD_COLUMNS,
            always=[m.Organization.id],
        )
        with get_session() as session:
            row = session.execute(
                select(*columns).where(m.Organization.id == id)
            ).first()
        return organization_from_row(row, names) if row else None


schema = strawberry.Schema(query=Query)