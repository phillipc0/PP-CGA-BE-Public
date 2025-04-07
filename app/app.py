from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.orm import sessionmaker
# noinspection PyPackageRequirements
from starlette.responses import JSONResponse, RedirectResponse, FileResponse
# noinspection PyPackageRequirements
from starlette.staticfiles import StaticFiles

from database import engine, Base
from routers import user, game, web


@asynccontextmanager
async def lifespan(_):
    Base.metadata.create_all(bind=engine)
    setup_cron_job()
    yield


app = FastAPI(
    title="Game API",
    version="1.0.0",
    summary="A simple API to manage users and games",
    description="This is a simple API to manage users and games. It allows you to create, read, update, and delete users and games.",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)


def setup_cron_job():
    with sessionmaker(autocommit=False, autoflush=False, bind=engine)() as session:
        try:
            if "postgresql" not in engine.url.drivername:
                return

            session.execute(
                text("CREATE EXTENSION IF NOT EXISTS pg_cron;")
            )

            session.execute(
                text("DELETE FROM cron.job WHERE jobname = :job_name;"), {"job_name": "daily_delete_old_guests"}
            )

            session.execute(
                text("SELECT cron.schedule(:job_name, :schedule_time, :job_query);"),
                {
                    "job_name":      "daily_delete_old_guests",
                    "schedule_time": "0 3 * * *",
                    "job_query":     """
                        DELETE FROM public.user
                        WHERE guest = TRUE
                        AND created < NOW() - INTERVAL '48 hours';
                        """,
                },
            )
            print("Cron job daily_delete_old_guests scheduled.")

            session.execute(
                text("DELETE FROM cron.job WHERE jobname = :job_name;"), {"job_name": "daily_delete_old_games"}
            )

            session.execute(
                text("SELECT cron.schedule(:job_name, :schedule_time, :job_query);"),
                {
                    "job_name":      "daily_delete_old_games",
                    "schedule_time": "0 3 * * *",
                    "job_query":     """
                        DELETE FROM public.game
                        WHERE created < NOW() - INTERVAL '48 hours';
                        """,
                },
            )
            print("Cron job daily_delete_old_games scheduled.")

            session.commit()
        except SQLAlchemyError as e:
            print(f"Error setting up cron job: {str(e)}")


@app.exception_handler(KeyError)
async def key_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Bad Request", "message": f"Missing key: {str(exc)}"},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Bad Request", "message": str(exc)},
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Bad Request", "message": "Integrity Error (most likely unique constraint failed)"},
    )


@app.exception_handler(404)
async def not_found_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "Not Found", "message": str(exc)},
    )


@app.exception_handler(NoResultFound)
async def no_result_found_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "Not Found", "message": "No entry was found."},
    )


app.include_router(user.router)
app.include_router(game.router)
app.include_router(web.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse("static/icon.png")


@app.get("/docs", include_in_schema=False)
def overridden_swagger():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Card Games API",
                               swagger_favicon_url="/static/icon.png")


@app.get("/redoc", include_in_schema=False)
def overridden_redoc():
    return get_redoc_html(openapi_url="/openapi.json", title="ReDoc Card Games",
                          redoc_favicon_url="/static/icon.png")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8070)
