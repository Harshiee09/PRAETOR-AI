@echo off
rem Whole app on this laptop behind ONE public link (the alternative to Vercel, DECISIONS D53):
rem   API (127.0.0.1:8000, never exposed) + production website (127.0.0.1:3100) + a Cloudflare quick tunnel to the website.
rem The website's server-side routes call the API locally with API_KEY from frontend\.env.local.
rem The public link is printed below and saved to data\scratch\app-tunnel.log. Keep all three windows open;
rem Ctrl+C or closing a window takes the site offline. A restart gives a new link.
setlocal
cd /d "%~dp0.."
if not defined CLOUDFLARED set "CLOUDFLARED=C:\dev\tools\cloudflared.exe"
if not exist "%CLOUDFLARED%" (
  echo cloudflared not found at %CLOUDFLARED% ^(set CLOUDFLARED to its path^)
  exit /b 1
)
if not exist frontend\.env.local (
  echo frontend\.env.local is missing: copy frontend\.env.example and set PRAETOR_API_KEY to the API_KEY in .env
  exit /b 1
)
rem API: start it unless something already listens on 8000
netstat -ano | findstr /r /c:"127.0.0.1:8000 .*LISTENING" >nul || start "PRAETOR API" /d "%~dp0.." cmd /k call "%~dp0..\praetor.cmd" serve
rem Website: install if needed, build, serve in production mode
start "PRAETOR website" /d "%~dp0..\frontend" cmd /k "(if not exist node_modules npm ci) && npm run build && npx next start --hostname 127.0.0.1 --port 3100"
echo Starting the API and the website in their own windows (about a minute) ...
if not exist data\scratch mkdir data\scratch
if exist data\scratch\app-tunnel.log del data\scratch\app-tunnel.log
"%CLOUDFLARED%" tunnel --no-autoupdate --url http://127.0.0.1:3100 --logfile data\scratch\app-tunnel.log
