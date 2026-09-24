# PRAETOR AI — AWS setup runbook (Phase 3 preparation)

Work through this with `infra\aws_setup.cmd`. Tick the boxes as you go and fill in the tables; this file is yours to
edit. Nothing here spends money on AI models: the first Bedrock call is made later by the app, through its cost meter,
after you say "go" for Phase 3.

Background: [AWS plan and cost controls](../docs/topics/ops/aws-cost-plan.md) · decisions D43 and V38 in
[DECISIONS.md](../docs/DECISIONS.md).

---

## 0. What you will end up with

| Where | What | Stack | Cost while idle |
|---|---|---|---|
| ap-south-1 (Mumbai) | a private, encrypted S3 bucket for the database, index and reports | `praetor-app` | storage only, tiny at this size |
| global IAM | the `praetor-app` policy: that bucket plus the one Bedrock model you choose | `praetor-app` | free |
| us-east-1 (AWS Budgets' home region) | the `praetor-monthly` budget with email alerts | `praetor-budget` | check the AWS Budgets pricing page |
| your PC | the `praetor` CLI profile and a few `.env` lines | — | — |

Not created: no servers, databases, VPCs, Lambda functions or Bedrock calls.

**Safety rules**
- Never paste access keys, secrets or SSO tokens into chat, into this file, or into `.env`. You type them only into
  the AWS CLI's own prompts.
- Never use the root user for this. Use IAM Identity Center (SSO) or an IAM user.
- Keep `LLM_ANSWER=ollama` in `.env` until Phase 3 builds the Bedrock client and cost meter.

---

## 1. Before you start

- [ ] You can sign in to the AWS console for the account holding your credits.
- [ ] You know how you sign in from the CLI:
  - **SSO / IAM Identity Center** (recommended): you need the SSO start URL (something like
    `https://<name>.awsapps.com/start`) and the SSO region.
  - **IAM user with an access key**: create the key in the IAM console for that user (not root).
- [ ] The identity you set up with can create CloudFormation stacks, S3 buckets, IAM policies and budgets
  (an administrator or power-user permission set is fine for *setup*; the app later runs with the narrow policy).
- [ ] Open **CMD** (not PowerShell) in the repo:

```bat
cd /d C:\dev\praetor-ai
infra\aws_setup.cmd
```

The menu shows the profile (`praetor`), region (`ap-south-1`) and a log file under `data\scratch\aws\`. Your answers
(model, email, limit) are remembered in `data\scratch\aws\state.cmd`, so you can quit and come back.

---

## 2. Step 1 — AWS CLI and the `praetor` profile  *(local only)*

- [ ] Choose **1**. It checks for AWS CLI version 2 (installed: 2.34.4).
- [ ] If the profile doesn't exist, answer **S** (SSO) or **K** (access key):
  - **S** runs `aws configure sso --profile praetor`: enter a session name (anything, e.g. `praetor`), the start URL,
    the SSO region, then approve in the browser and pick the account and role. When asked for the
    *CLI default client Region*, enter `ap-south-1`; output format `json`.
  - **K** runs `aws configure --profile praetor`: enter the key ID, the secret, region `ap-south-1`, output `json`.
- [ ] If the profile's region isn't `ap-south-1`, answer **Y** to fix it.
- [ ] It ends with "Signed in as arn:aws:...". If that ARN ends in `:root`, stop and use a non-root identity.

Later, if an SSO session expires, run: `aws sso login --profile praetor`

---

## 3. Step 2 — Pre-flight  *(read-only, free)*

- [ ] Choose **2**. It prints your account and caller, the region, the **Bedrock text models** and
  **inference profiles** available in ap-south-1, and any existing budgets. Everything is also written to the log.
- [ ] Then do these checks **in the AWS console** and fill in the table:

| Check | Where in the console | Your answer |
|---|---|---|
| Credit balance | Billing and Cost Management → Credits | |
| Credit expiry date | same page | |
| Is Amazon Bedrock an eligible service for the credits? | same page (credit details) | |
| Are Anthropic models billed through AWS Marketplace instead? | credit terms / Bedrock model page | |
| Is your chosen model available to this account? | Amazon Bedrock → Model catalog / Model access, region **Asia Pacific (Mumbai)** | |
| One-time use-case form needed (Anthropic)? | shown on the model's page if required | |
| Model input price per 1,000 tokens (and date checked) | the Amazon Bedrock pricing page, region Mumbai | |
| Model output price per 1,000 tokens (and date checked) | same page | |
| AWS Budgets price for 1 budget | the AWS Budgets pricing page | |

The script does **not** call Cost Explorer (it charges per request), so credits are read in the console only.

---

## 4. Step 3 — Choose the Bedrock model  *(read-only)*

- [ ] Choose **3** and paste an id **exactly** as listed in step 2:
  - an **inference profile id** (cross-region profiles carry a geography prefix, for example `apac.`; use whatever
    step 2 lists), or
  - a **foundation model id** that is listed as on-demand in ap-south-1.
- [ ] The script resolves the exact ARNs the policy needs (for a profile: the profile plus the model in each region it
  routes to) and saves them.

| Chosen id (BEDROCK_MODEL_ID) | Type (profile / model) | Why this one |
|---|---|---|
| | | |

Pick one model for now; Phase 3 compares it with the local model on the eval subset and keeps it only if it wins.

---

## 5. Step 4 — Budget and alerts  *(creates a resource; type YES)*

- [ ] Choose **4**. Enter a **monthly limit in whole USD**, well under the credit balance (default 20), and the
  **alert email**.
- [ ] Type `YES`. It validates `infra\budget.yaml`, then creates stack `praetor-budget` in **us-east-1**.
- [ ] Check: AWS console → Billing → Budgets → `praetor-monthly` exists, with 4 alerts
  (50%, 80%, 100% actual; 100% forecast).

Why "before credits": the budget has `IncludeCredit: false`. The AWS default subtracts credits, so the budget would
sit near $0 and never alert while credits last; this way the alerts track what you actually use.

| Monthly limit (USD) | Alert email | Stack status |
|---|---|---|
| | | |

---

## 6. Step 5 — S3 bucket and app policy  *(creates resources; type YES)*

- [ ] Choose **5**. It shows what it will create and which Bedrock ARNs the policy will allow (`none` if you skipped
  step 3 — that is fine; re-run step 5 after choosing a model and the stack updates in place).
- [ ] Type `YES`. It validates `infra\cloudformation.yaml`, then creates or updates stack `praetor-app` in
  **ap-south-1** and prints the outputs.
- [ ] Check in the console:
  - S3 → the new bucket: *Block all public access* on, default encryption on, versioning enabled.
  - IAM → Policies → `praetor-app`: S3 actions on that bucket only; `bedrock:InvokeModel` only on your model.

The bucket is **kept** even if the stack is deleted, so data can't be lost by accident.

| Bucket name (S3_BUCKET) | Policy ARN | Bedrock access in the policy |
|---|---|---|
| | | |

---

## 7. Step 6 — Give the app its policy  *(changes IAM; only for an IAM-user profile)*

- [ ] **IAM user profile:** choose **6**, check the user name, type `YES` to attach `praetor-app`.
- [ ] **SSO profile:** step 6 only prints instructions. In IAM Identity Center → Permission sets, either add the
  customer managed policy `praetor-app` to your set, or (better) create a small permission set that has **only**
  `praetor-app` for the app to use, and re-provision the account.

If your profile is an administrator, attaching `praetor-app` adds nothing — least privilege needs a separate
identity for the app. Setting that up is optional for the demo; note what you chose:

| Identity the app will use | Has only `praetor-app`? |
|---|---|
| | |

---

## 8. Step 7 — `.env` lines

- [ ] Choose **7**. It prints the stack outputs and writes `data\scratch\aws\env_lines.txt`:

```text
AWS_PROFILE=praetor
AWS_REGION=ap-south-1
S3_BUCKET=<your bucket>
BEDROCK_MODEL_ID=<your model or profile id>
```

- [ ] Paste these four into `.env` (replace the existing empty `S3_BUCKET=` and `BEDROCK_MODEL_ID=`).
- [ ] Leave `LLM_ANSWER=ollama` and `BEDROCK_DAILY_BUDGET_USD=2.00` as they are.

---

## 9. What to send me when you're done

- [ ] The log: `data\scratch\aws\setup_<date>.log` (it contains your account id and ARNs, no secrets)
- [ ] The filled tables above (or just this file)
- [ ] Your "go" for Phase 3, if you're ready

I will then record the account checks, model id and prices (with dates) in `docs/DECISIONS.md` and
`app/config/prices.yaml`, and build the Phase 3 code: the Bedrock client behind the cost meter (reserve the worst-case
cost before each call, reconcile after, refuse unknown prices), `s3-sync`, and the local-versus-Bedrock comparison.

---

## 10. Troubleshooting

| You see | Do |
|---|---|
| `The config profile (praetor) could not be found` | run step 1 |
| `Token has expired` / `SSO session ... expired` | `aws sso login --profile praetor`, then retry the step |
| `AccessDenied` / `not authorized to perform` | the identity lacks that permission for setup; use an admin or power-user permission set for steps 2–6 |
| A model you expected isn't in the step 2 list | it may be offered in ap-south-1 only through an inference profile (check the profile list), or not yet enabled for your account (Bedrock console, Model access) |
| Step 3: "neither an inference profile nor a foundation model" | copy the id exactly from the step 2 tables; check the region is ap-south-1 |
| Stack `ROLLBACK_COMPLETE` | open CloudFormation → the stack → *Events* to see why, fix it, delete the failed stack, re-run the step. If the bucket had already been created it is kept; delete that empty bucket in S3 |
| `Budget ... already exists` | a budget named `praetor-monthly` was made by hand; delete it (Billing → Budgets) or keep it and skip step 4 |
| The window closes or nothing happens | run it from an open CMD window (not by double-click) so you can read errors; check the log in `data\scratch\aws\` |
| `aws` is not version 2 | `winget install -e --id Amazon.AWSCLI`, open a new CMD window |

---

## 11. Removing everything later

```bat
infra\aws_teardown.cmd
```

- [ ] Type `DELETE`. It detaches `praetor-app` from IAM users, then deletes `praetor-app` and `praetor-budget`.
  (If you attached the policy to an SSO permission set, remove it there first.)
- [ ] The bucket is kept. Back it up if needed — `aws s3 sync s3://<bucket> data\scratch\s3-backup --profile praetor` —
  then in the S3 console choose the bucket → **Empty** (this also removes old versions) → **Delete**.
