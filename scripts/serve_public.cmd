@echo off
rem Public demo (deployment note): the API on this laptop plus a Cloudflare quick tunnel (DECISIONS D51).
rem Needs API_KEY in .env (tunnel traffic is refused without it) and cloudflared.exe (default C:\dev\tools).
rem The tunnel URL changes on every start: copy the https://....trycloudflare.com line it prints into the Vercel
rem project's PRAETOR_API_URL and redeploy. Close both windows (or Ctrl+C) to take the demo offline.
setlocal
cd /d "%~dp0.."
if not defined CLOUDFLARED set "CLOUDFLARED=C:\dev\tools\cloudflared.exe"
if not exist "%CLOUDFLARED%" (
  echo cloudflared not found at %CLOUDFLARED% ^(set CLOUDFLARED to its path^)
  exit /b 1
)
findstr /r /c:"^API_KEY=.........." .env >nul || (
  echo API_KEY is missing or too short in .env; the tunnel would refuse every call. See docs\topics\ops\deployment.md
  exit /b 1
)
start "PRAETOR API" cmd /k praetor.cmd serve
echo Starting the API in its own window (the models take about a minute to load) ...
"%CLOUDFLARED%" tunnel --no-autoupdate --url http://127.0.0.1:8000
