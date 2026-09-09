import json
import urllib.error
import urllib.parse
import urllib.request

from fastapi import FastAPI, HTTPException, Request
from strawberry.fastapi import GraphQLRouter

from auth import CLIENT_ID, TOKEN_URL, context_from_request
from db import init_db
from schema import schema

init_db()


async def get_context(request: Request) -> dict:
    return context_from_request(request)


graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphql_ide="graphiql",
)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")


@app.post("/login")
def login(payload: dict):
    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")

    form_data = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "username": username,
            "password": password,
        }
    ).encode()
    request = urllib.request.Request(TOKEN_URL, data=form_data, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            detail = json.loads(raw).get("error_description") or json.loads(raw).get(
                "error"
            )
        except json.JSONDecodeError:
            detail = str(exc.reason)
        raise HTTPException(status_code=exc.code, detail=detail) from exc
    except urllib.error.URLError as exc:
        raise HTTPException(
            status_code=503, detail=f"Keycloak unreachable: {exc.reason}"
        ) from exc


@app.get("/")
def root():
    return {
        "message": "FastAPI GraphQL API running at /graphql",
        "login": "/login",
        "keycloak": TOKEN_URL,
    }