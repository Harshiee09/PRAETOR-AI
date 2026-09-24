@echo off
rem ===================================================================================================================
rem  PRAETOR AI - AWS setup for Windows CMD  (Phase 3 preparation; docs/topics/ops/aws-cost-plan.md)
rem
rem  Run it yourself from any folder:   infra\aws_setup.cmd
rem  It is a menu; run the steps in order (1, 2, 3, 4, 5, 7), and re-run any step later.
rem
rem  What it does NOT do:
rem    - it never invokes a Bedrock model (the first paid call is made by the app through its cost meter, after "go")
rem    - it never sees, prints or stores credentials (you type them into the AWS CLI's own prompts)
rem    - it never edits .env (it writes the lines for you to paste)
rem    - it never calls the Cost Explorer API (charged per request)
rem  Steps 4, 5 and 6 create or change AWS resources and only run after you type YES.
rem  Logs and your answers go to data\scratch\aws\ (gitignored).
rem ===================================================================================================================
setlocal EnableExtensions EnableDelayedExpansion

set "PROFILE=praetor"
set "REGION=ap-south-1"
set "BUDGET_REGION=us-east-1"
set "APP_STACK=praetor-app"
set "BUDGET_STACK=praetor-budget"

rem Put AWS CLI v2 first on PATH: a pip-installed v1 "aws" can also be on this machine.
if exist "%ProgramFiles%\Amazon\AWSCLIV2\aws.exe" set "PATH=%ProgramFiles%\Amazon\AWSCLIV2;%PATH%"

pushd "%~dp0.." || (echo Cannot find the repository root. & exit /b 1)
if not exist "infra\cloudformation.yaml" (echo Run this from the praetor-ai repository: infra\cloudformation.yaml not found. & popd & exit /b 1)
set "OUT=data\scratch\aws"
if not exist "%OUT%" mkdir "%OUT%"
set "TMPF=%OUT%\_out.txt"
set "ERRF=%OUT%\_err.txt"
set "STATE=%OUT%\state.cmd"
set "TS="
for /f %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss" 2^>nul') do set "TS=%%t"
if not defined TS set "TS=run"
set "LOG=%OUT%\setup_%TS%.log"

set "BEDROCK_MODEL_ID="
set "BEDROCK_ARNS="
set "ALERT_EMAIL="
set "BUDGET_LIMIT=20"
set "EMPTY=0"
if exist "%STATE%" call "%STATE%"
echo PRAETOR AI AWS setup log %TS% > "%LOG%"

:menu
echo.
echo ======================== PRAETOR AI - AWS setup ========================
echo  profile: %PROFILE%    region: %REGION%    log: %LOG%
echo  chosen Bedrock model: !BEDROCK_MODEL_ID!
echo.
echo  1  AWS CLI check and the "praetor" profile                       [local only]
echo  2  Pre-flight: identity, region, Bedrock models, budgets          [read-only, free]
echo  3  Choose the Bedrock model or inference profile                  [read-only]
echo  4  Budget with email alerts, us-east-1                            [CREATES a resource]
echo  5  S3 bucket and least-privilege app policy, ap-south-1           [CREATES resources]
echo  6  Attach the app policy to your IAM user                         [changes IAM]
echo  7  Show stack outputs and the .env lines                          [read-only]
echo  Q  Quit
echo =========================================================================
set "CH="
set /p "CH=Choose a step: "
rem three empty answers in a row end the script (also stops a loop when input is piped and runs out)
if "!CH!"=="" (
  set /a "EMPTY+=1"
  if !EMPTY! GEQ 3 goto done
  goto menu
)
set "EMPTY=0"
if /i "!CH!"=="1" call :step_profile & goto menu
if /i "!CH!"=="2" call :step_preflight & goto menu
if /i "!CH!"=="3" call :step_model & goto menu
if /i "!CH!"=="4" call :step_budget & goto menu
if /i "!CH!"=="5" call :step_app & goto menu
if /i "!CH!"=="6" call :step_attach & goto menu
if /i "!CH!"=="7" call :step_outputs & goto menu
if /i "!CH!"=="Q" goto done
goto menu

rem -------------------------------------------------------------------------------------------------------------------
:step_profile
call :section "Step 1 - AWS CLI and profile"
where aws >nul 2>&1
if errorlevel 1 (
  echo The AWS CLI v2 is not installed. Install it, open a new CMD window and run this again:
  echo     winget install -e --id Amazon.AWSCLI
  exit /b 1
)
aws --version > "%TMPF%" 2>&1
call :show
findstr /b /c:"aws-cli/2." "%TMPF%" >nul
if errorlevel 1 (
  echo This is not AWS CLI version 2. Install v2 with:  winget install -e --id Amazon.AWSCLI
  exit /b 1
)
aws configure list-profiles > "%TMPF%" 2>nul
findstr /x /c:"%PROFILE%" "%TMPF%" >nul
if not errorlevel 1 goto profile_region
echo The "%PROFILE%" profile does not exist yet. How do you sign in to AWS?
echo    S  IAM Identity Center / SSO   - recommended, no long-lived keys
echo    K  an IAM user's access key    - never use the root user's keys
echo    N  not now
set "ANS="
set /p "ANS=S, K or N: "
if /i "!ANS!"=="K" goto profile_keys
if /i not "!ANS!"=="S" exit /b 0
echo The AWS CLI will ask for your SSO start URL and SSO region, then open a browser to sign in.
echo When it asks for the CLI default client Region, enter %REGION%.
aws configure sso --profile %PROFILE%
goto profile_region
:profile_keys
echo You type the access key ID and secret into the AWS CLI's own prompts; this script never sees or stores them.
echo When it asks for the default region, enter %REGION%.
aws configure --profile %PROFILE%

:profile_region
set "CURREG="
aws configure get region --profile %PROFILE% > "%TMPF%" 2>nul
set /p "CURREG=" < "%TMPF%"
if /i "!CURREG!"=="%REGION%" goto profile_ok
echo The profile's default region is "!CURREG!"; this project uses %REGION%.
set "ANS="
set /p "ANS=Set the %PROFILE% profile's default region to %REGION%? Y or N: "
if /i not "!ANS!"=="Y" goto profile_ok
aws configure set region %REGION% --profile %PROFILE%
:profile_ok
call :identity
if errorlevel 1 exit /b 1
echo Signed in as !CALLER_ARN!
echo Profile ready. Next: step 2.
exit /b 0

rem -------------------------------------------------------------------------------------------------------------------
:step_preflight
call :section "Step 2 - pre-flight (read-only)"
call :identity
if errorlevel 1 exit /b 1
echo Account: !ACCOUNT!
echo Caller:  !CALLER_ARN!
echo Account: !ACCOUNT!  Caller: !CALLER_ARN! >> "%LOG%"
if "!CALLER_ARN:~-5!"==":root" echo WARNING: this profile uses the ROOT user. Use an IAM Identity Center user or an IAM user instead.
aws configure get region --profile %PROFILE% > "%TMPF%" 2>nul
set "CURREG="
set /p "CURREG=" < "%TMPF%"
echo Profile region: !CURREG!   required: %REGION%
if /i not "!CURREG!"=="%REGION%" echo WARNING: run step 1 to set the region.

call :section "Bedrock foundation models: on-demand, text output, %REGION%"
aws bedrock list-foundation-models --region %REGION% --by-inference-type ON_DEMAND --by-output-modality TEXT --profile %PROFILE% --query "modelSummaries[].[providerName,modelId,modelLifecycle.status]" --output table > "%TMPF%" 2>&1
call :show
call :section "Bedrock system-defined inference profiles in %REGION%"
aws bedrock list-inference-profiles --region %REGION% --type-equals SYSTEM_DEFINED --profile %PROFILE% --query "inferenceProfileSummaries[].[inferenceProfileId,status]" --output table > "%TMPF%" 2>&1
call :show
call :section "Budgets in account !ACCOUNT!"
aws budgets describe-budgets --account-id !ACCOUNT! --region %BUDGET_REGION% --profile %PROFILE% --query "Budgets[].[BudgetName,BudgetLimit.Amount,BudgetLimit.Unit,CostTypes.IncludeCredit]" --output table > "%TMPF%" 2>&1
call :show

call :section "Do these by hand in the AWS console"
echo  a. Billing and Cost Management - Credits: note the balance, the expiry date and the eligible services.
echo     Check that Amazon Bedrock is eligible, and whether Anthropic models are billed through AWS Marketplace.
echo  b. Amazon Bedrock console, region %REGION%: open the model catalog or "Model access" page and make sure the model
echo     you will pick in step 3 is available to this account. Anthropic models can ask for a one-time use-case form.
echo  c. Amazon Bedrock pricing page: note the input and output price per 1,000 tokens for that model, with today's
echo     date. They go into app\config\prices.yaml in Phase 3 - nothing is paid until then.
echo  d. AWS Budgets pricing page: confirm what one budget costs.
(
  echo Console checks: credits balance/expiry/eligible services; Bedrock model access in %REGION%;
  echo Bedrock prices for the chosen model; AWS Budgets pricing.
) >> "%LOG%"
echo.
echo Pre-flight done. Send me the log file %LOG% when you want me to record it in DECISIONS.md.
exit /b 0

rem -------------------------------------------------------------------------------------------------------------------
:step_model
call :section "Step 3 - choose the Bedrock model"
echo Pick an id from the step 2 lists. For Anthropic models in %REGION%, this is usually a system-defined
echo inference profile such as one starting with "apac." - copy the id exactly as listed.
set "IN="
set /p "IN=Model id or inference profile id [!BEDROCK_MODEL_ID!]: "
if "!IN!"=="" set "IN=!BEDROCK_MODEL_ID!"
if "!IN!"=="" (
  echo No id given.
  exit /b 1
)
set "PARN="
set "MARNS="
aws bedrock get-inference-profile --inference-profile-identifier !IN! --region %REGION% --profile %PROFILE% --query "inferenceProfileArn" --output text > "%TMPF%" 2> "%ERRF%"
if errorlevel 1 goto model_foundation
set /p "PARN=" < "%TMPF%"
aws bedrock get-inference-profile --inference-profile-identifier !IN! --region %REGION% --profile %PROFILE% --query "join(',', models[].modelArn)" --output text > "%TMPF%" 2> "%ERRF%"
if errorlevel 1 goto model_fail
set /p "MARNS=" < "%TMPF%"
set "BEDROCK_ARNS=!PARN!,!MARNS!"
echo "!IN!" is an inference profile. The app policy will allow the profile and the models it routes to:
goto model_save
:model_foundation
aws bedrock get-foundation-model --model-identifier !IN! --region %REGION% --profile %PROFILE% --query "modelDetails.modelArn" --output text > "%TMPF%" 2> "%ERRF%"
if errorlevel 1 goto model_fail
set /p "BEDROCK_ARNS=" < "%TMPF%"
echo "!IN!" is a foundation model in %REGION%. The app policy will allow:
:model_save
set "BEDROCK_MODEL_ID=!IN!"
echo    !BEDROCK_ARNS!
echo Chosen model: !BEDROCK_MODEL_ID!  ARNs: !BEDROCK_ARNS! >> "%LOG%"
call :save_state
echo Saved. Run step 5 to create or update the app policy with this model.
exit /b 0
:model_fail
type "%ERRF%"
echo "!IN!" is neither an inference profile nor a foundation model visible to this account in %REGION%.
exit /b 1

rem -------------------------------------------------------------------------------------------------------------------
:step_budget
call :section "Step 4 - budget and email alerts, %BUDGET_REGION%"
call :identity
if errorlevel 1 exit /b 1
echo This creates or updates the AWS Budget "praetor-monthly" in account !ACCOUNT!, measured BEFORE credits,
echo with email alerts at 50, 80 and 100 percent of actual spend and 100 percent of forecast spend.
set "IN="
set /p "IN=Monthly limit in USD, well under your credit balance [!BUDGET_LIMIT!]: "
if not "!IN!"=="" set "BUDGET_LIMIT=!IN!"
set /a "LIMN=BUDGET_LIMIT" 2>nul
if not "!LIMN!"=="!BUDGET_LIMIT!" (
  echo "!BUDGET_LIMIT!" is not a whole number of dollars.
  exit /b 1
)
if !LIMN! LSS 1 (
  echo The limit must be at least 1.
  exit /b 1
)
set "IN="
set /p "IN=Alert email [!ALERT_EMAIL!]: "
if not "!IN!"=="" set "ALERT_EMAIL=!IN!"
if "!ALERT_EMAIL!"=="" (
  echo An alert email is required.
  exit /b 1
)
if "!ALERT_EMAIL:@=!"=="!ALERT_EMAIL!" (
  echo "!ALERT_EMAIL!" is not an email address.
  exit /b 1
)
call :save_state
call :confirm "create or update the budget: !BUDGET_LIMIT! USD a month, alerts to !ALERT_EMAIL!"
if errorlevel 1 exit /b 0
aws cloudformation validate-template --template-body file://infra/budget.yaml --region %BUDGET_REGION% --profile %PROFILE% > "%TMPF%" 2>&1
if errorlevel 1 (
  call :show
  echo The budget template did not validate; nothing was created.
  exit /b 1
)
aws cloudformation deploy --template-file infra/budget.yaml --stack-name %BUDGET_STACK% --region %BUDGET_REGION% --parameter-overrides MonthlyLimitUSD=!BUDGET_LIMIT! AlertEmail=!ALERT_EMAIL! --tags project=praetor-ai --no-fail-on-empty-changeset --profile %PROFILE%
set "RC=!errorlevel!"
echo budget stack deploy exit code !RC! >> "%LOG%"
if not "!RC!"=="0" (
  echo The budget stack did not deploy. See the CloudFormation console, stack %BUDGET_STACK% in %BUDGET_REGION%.
  exit /b 1
)
echo Budget ready. Emails go to !ALERT_EMAIL!.
exit /b 0

rem -------------------------------------------------------------------------------------------------------------------
:step_app
call :section "Step 5 - S3 bucket and app policy, %REGION%"
call :identity
if errorlevel 1 exit /b 1
set "PARAM=none"
if defined BEDROCK_ARNS set "PARAM=!BEDROCK_ARNS!"
if "!PARAM!"=="none" (
  echo No Bedrock model chosen yet: the policy will grant S3 access only. Run step 3, then this step again, to add
  echo the model. That is safe: the stack is updated in place.
)
echo This creates or updates stack %APP_STACK% in account !ACCOUNT!:
echo   - a private, encrypted, TLS-only, versioned S3 bucket; old versions expire after 7 days; the bucket is KEPT
echo     if the stack is ever deleted
echo   - the IAM managed policy "praetor-app": this bucket, plus invoke on: !PARAM!
call :confirm "create or update stack %APP_STACK%"
if errorlevel 1 exit /b 0
aws cloudformation validate-template --template-body file://infra/cloudformation.yaml --region %REGION% --profile %PROFILE% > "%TMPF%" 2>&1
if errorlevel 1 (
  call :show
  echo The app template did not validate; nothing was created.
  exit /b 1
)
aws cloudformation deploy --template-file infra/cloudformation.yaml --stack-name %APP_STACK% --region %REGION% --capabilities CAPABILITY_NAMED_IAM --parameter-overrides "BedrockResourceArns=!PARAM!" --tags project=praetor-ai --no-fail-on-empty-changeset --profile %PROFILE%
set "RC=!errorlevel!"
echo app stack deploy exit code !RC! >> "%LOG%"
if not "!RC!"=="0" (
  echo The app stack did not deploy. See the CloudFormation console, stack %APP_STACK% in %REGION%.
  exit /b 1
)
call :step_outputs
exit /b 0

rem -------------------------------------------------------------------------------------------------------------------
:step_attach
call :section "Step 6 - attach the app policy"
call :identity
if errorlevel 1 exit /b 1
set "POLICY_ARN="
aws cloudformation describe-stacks --stack-name %APP_STACK% --region %REGION% --profile %PROFILE% --query "Stacks[0].Outputs[?OutputKey=='AppPolicyArn'].OutputValue" --output text > "%TMPF%" 2> "%ERRF%"
set /p "POLICY_ARN=" < "%TMPF%"
if "!POLICY_ARN!"=="" (
  echo Stack %APP_STACK% has no policy yet: run step 5 first.
  exit /b 1
)
echo Policy: !POLICY_ARN!
echo For least privilege the app should run as an identity that has ONLY this policy. If "%PROFILE%" is an
echo administrator, attaching it adds nothing; create a separate IAM user or permission set for the app instead.
if "!CALLER_ARN:user/=!"=="!CALLER_ARN!" goto attach_sso
set "UNAME=!CALLER_ARN:*user/=!"
for %%n in ("!UNAME:/=" "!") do set "UNAME=%%~n"
call :confirm "attach praetor-app to IAM user !UNAME!"
if errorlevel 1 exit /b 0
aws iam attach-user-policy --user-name !UNAME! --policy-arn !POLICY_ARN! --profile %PROFILE%
if errorlevel 1 exit /b 1
echo Attached praetor-app to IAM user !UNAME!. >> "%LOG%"
echo Attached.
exit /b 0
:attach_sso
echo "%PROFILE%" signs in through a role, not an IAM user. In the IAM Identity Center console, open the permission
echo set you use for this account, add a customer managed policy named praetor-app, and re-provision the account.
exit /b 0

rem -------------------------------------------------------------------------------------------------------------------
:step_outputs
call :section "Stack outputs"
aws cloudformation describe-stacks --stack-name %APP_STACK% --region %REGION% --profile %PROFILE% --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table > "%TMPF%" 2>&1
call :show
set "BUCKET="
aws cloudformation describe-stacks --stack-name %APP_STACK% --region %REGION% --profile %PROFILE% --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text > "%TMPF%" 2>nul
set /p "BUCKET=" < "%TMPF%"
(
  echo # PRAETOR AI - paste these into .env; keep LLM_ANSWER=ollama until the Bedrock client and cost meter exist
  echo AWS_PROFILE=%PROFILE%
  echo AWS_REGION=%REGION%
  echo S3_BUCKET=!BUCKET!
  echo BEDROCK_MODEL_ID=!BEDROCK_MODEL_ID!
) > "%OUT%\env_lines.txt"
call :section ".env lines - also saved to %OUT%\env_lines.txt"
type "%OUT%\env_lines.txt"
type "%OUT%\env_lines.txt" >> "%LOG%"
exit /b 0

rem ------------------------------------------------------------------------------------------------ helpers --------
:identity
set "ACCOUNT="
set "CALLER_ARN="
aws sts get-caller-identity --profile %PROFILE% --query "[Account,Arn]" --output text > "%TMPF%" 2> "%ERRF%"
if errorlevel 1 (
  type "%ERRF%"
  echo Could not sign in as "%PROFILE%". Run step 1; for an SSO profile whose session expired run:
  echo     aws sso login --profile %PROFILE%
  exit /b 1
)
for /f "usebackq tokens=1,2" %%a in ("%TMPF%") do (
  set "ACCOUNT=%%a"
  set "CALLER_ARN=%%b"
)
exit /b 0

:confirm
echo.
echo About to %~1.
set "OK="
set /p "OK=Type YES to continue, anything else to cancel: "
if /i "!OK!"=="YES" exit /b 0
echo Cancelled; nothing was changed.
exit /b 1

:section
echo.
echo --- %~1 ---
echo. >> "%LOG%"
echo --- %~1 --- >> "%LOG%"
exit /b 0

:show
type "%TMPF%"
type "%TMPF%" >> "%LOG%"
exit /b 0

:save_state
(
  echo set "BEDROCK_MODEL_ID=!BEDROCK_MODEL_ID!"
  echo set "BEDROCK_ARNS=!BEDROCK_ARNS!"
  echo set "ALERT_EMAIL=!ALERT_EMAIL!"
  echo set "BUDGET_LIMIT=!BUDGET_LIMIT!"
) > "%STATE%"
exit /b 0

:done
if exist "%TMPF%" del "%TMPF%" >nul 2>&1
if exist "%ERRF%" del "%ERRF%" >nul 2>&1
echo Log: %LOG%
popd
endlocal
exit /b 0
