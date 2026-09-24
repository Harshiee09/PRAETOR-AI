@echo off
rem ===================================================================================================================
rem  PRAETOR AI - AWS teardown for Windows CMD (docs/topics/ops/aws-cost-plan.md, "Deployment steps" 6)
rem
rem  Deletes the two stacks made by infra\aws_setup.cmd: praetor-app (ap-south-1) and praetor-budget (us-east-1).
rem  The S3 bucket is KEPT (the template retains it) so no data is lost by accident; the script prints how to back it
rem  up and empty it. Nothing runs until you type DELETE.
rem ===================================================================================================================
setlocal EnableExtensions EnableDelayedExpansion
set "PROFILE=praetor"
set "REGION=ap-south-1"
set "BUDGET_REGION=us-east-1"
set "APP_STACK=praetor-app"
set "BUDGET_STACK=praetor-budget"
if exist "%ProgramFiles%\Amazon\AWSCLIV2\aws.exe" set "PATH=%ProgramFiles%\Amazon\AWSCLIV2;%PATH%"
pushd "%~dp0.." || (echo Cannot find the repository root. & exit /b 1)
set "OUT=data\scratch\aws"
if not exist "%OUT%" mkdir "%OUT%"
set "TMPF=%OUT%\_out.txt"

aws sts get-caller-identity --profile %PROFILE% --query "[Account,Arn]" --output text > "%TMPF%" 2>&1
if errorlevel 1 (
  type "%TMPF%"
  echo Could not sign in as "%PROFILE%". For SSO run:  aws sso login --profile %PROFILE%
  goto end
)
for /f "usebackq tokens=1,2" %%a in ("%TMPF%") do (
  set "ACCOUNT=%%a"
  set "CALLER_ARN=%%b"
)
set "BUCKET="
aws cloudformation describe-stacks --stack-name %APP_STACK% --region %REGION% --profile %PROFILE% --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text > "%TMPF%" 2>nul
set /p "BUCKET=" < "%TMPF%"
set "POLICY_ARN="
aws cloudformation describe-stacks --stack-name %APP_STACK% --region %REGION% --profile %PROFILE% --query "Stacks[0].Outputs[?OutputKey=='AppPolicyArn'].OutputValue" --output text > "%TMPF%" 2>nul
set /p "POLICY_ARN=" < "%TMPF%"

echo Account !ACCOUNT!, signed in as !CALLER_ARN!
echo This will delete:
echo   - stack %APP_STACK% in %REGION%: the praetor-app IAM policy; the bucket !BUCKET! is kept
echo   - stack %BUDGET_STACK% in %BUDGET_REGION%: the praetor-monthly budget and its alerts
set "OK="
set /p "OK=Type DELETE to continue, anything else to cancel: "
if not "!OK!"=="DELETE" (
  echo Cancelled; nothing was changed.
  goto end
)

if "!POLICY_ARN!"=="" goto delete_app
rem A managed policy cannot be deleted while attached: detach it from IAM users first.
aws iam list-entities-for-policy --policy-arn !POLICY_ARN! --profile %PROFILE% --query "PolicyUsers[].UserName" --output text > "%TMPF%" 2>nul
for /f "usebackq tokens=*" %%u in ("%TMPF%") do (
  for %%n in (%%u) do (
    if /i not "%%n"=="None" (
      echo Detaching praetor-app from IAM user %%n
      aws iam detach-user-policy --user-name %%n --policy-arn !POLICY_ARN! --profile %PROFILE%
    )
  )
)
aws iam list-entities-for-policy --policy-arn !POLICY_ARN! --profile %PROFILE% --query "length([PolicyRoles[], PolicyGroups[]][])" --output text > "%TMPF%" 2>nul
set "OTHERS=0"
set /p "OTHERS=" < "%TMPF%"
if not "!OTHERS!"=="0" (
  echo praetor-app is still attached to !OTHERS! role or group, for example through an IAM Identity Center permission
  echo set. Remove it there first, then run this again.
  goto end
)

:delete_app
echo Deleting %APP_STACK% ...
aws cloudformation delete-stack --stack-name %APP_STACK% --region %REGION% --profile %PROFILE%
aws cloudformation wait stack-delete-complete --stack-name %APP_STACK% --region %REGION% --profile %PROFILE%
if errorlevel 1 echo %APP_STACK% did not finish deleting; check the CloudFormation console in %REGION%.
echo Deleting %BUDGET_STACK% ...
aws cloudformation delete-stack --stack-name %BUDGET_STACK% --region %BUDGET_REGION% --profile %PROFILE%
aws cloudformation wait stack-delete-complete --stack-name %BUDGET_STACK% --region %BUDGET_REGION% --profile %PROFILE%
if errorlevel 1 echo %BUDGET_STACK% did not finish deleting; check the CloudFormation console in %BUDGET_REGION%.

echo.
if "!BUCKET!"=="" goto end
echo The bucket !BUCKET! still exists and is still billed for what it stores.
echo   1. Keep a copy if you need one:   aws s3 sync s3://!BUCKET! data\scratch\s3-backup --profile %PROFILE%
echo   2. Then in the S3 console: select the bucket, choose Empty - this also removes old versions - then Delete.

:end
if exist "%TMPF%" del "%TMPF%" >nul 2>&1
popd
endlocal
exit /b 0
