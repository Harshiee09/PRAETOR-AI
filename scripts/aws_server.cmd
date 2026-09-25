@echo off
rem PRAETOR cloud API on AWS EC2 (DECISIONS D58):  aws_server status | start | stop
rem Stopping ends the $0.34/hour instance charge (c6i.2xlarge, D60); the 40 GB disk and the Elastic IP still cost a few cents a day
rem while stopped. The address never changes: https://3-111-113-83.sslip.io (Vercel's PRAETOR_API_URL).
rem The API and HTTPS start by themselves about two minutes after "start".
setlocal
set "ID=i-08f9fc33d209a2c2e"
set "REGION=ap-south-1"
set "URL=https://3-111-113-83.sslip.io/v1/healthz"
if /i "%~1"=="start" (
  aws ec2 start-instances --instance-ids %ID% --region %REGION% --query "StartingInstances[0].CurrentState.Name" --output text
  echo Ready in about two minutes: %URL%
  exit /b
)
if /i "%~1"=="stop" (
  aws ec2 stop-instances --instance-ids %ID% --region %REGION% --query "StoppingInstances[0].CurrentState.Name" --output text
  exit /b
)
aws ec2 describe-instances --instance-ids %ID% --region %REGION% --query "Reservations[0].Instances[0].State.Name" --output text
curl -s --max-time 15 %URL%
echo.
