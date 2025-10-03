@echo off
set MESSAGE=%*
if "%MESSAGE%"=="" set MESSAGE=Auto migration

echo [Generating migration: %MESSAGE%]
alembic revision --autogenerate -m "%MESSAGE%"

echo [Applying migration...]
alembic upgrade head

echo [Migration complete.]
pause