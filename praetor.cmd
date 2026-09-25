@echo off
rem Runs the praetor CLI through Python. Use this if Windows Smart App Control blocks the praetor.exe launcher
rem that uv generates (DECISIONS V37). Example:  praetor serve
setlocal
pushd "%~dp0"
uv run python -m app.cli %*
set "RC=%errorlevel%"
popd
exit /b %RC%
