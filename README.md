# Methods Hub Quality Assurance Workflow

## Description
This repostiory contains the Quality Assurance workflow for the methodhub platform.
It is used to test other repositories how well they fullfill the technical conditions of the methodhub Platform.
A direct access of the workflow via Github or Mybinder is not planned at the moment.
The workflow can either be triggered manually or via the Methodshub Platform (as soon as implemented).

## Use Cases
Every Tutorial or Method will be tested via this workflow. A workflow that does not pass the workflow is not fit to be 
published and corrections are needed given the feedback of the report or reviewer.

Another Use Case is an optional test whether your repository passes this workflow. This can also be triggered on the 
Methodshub platform (as soon as implemented).

## Input Data
The Input Data itself needs to be put inside a Post request. It is the repository that needs to be tested. As well as
some additional information. The request can as an example look like this via curl:

curl -X POST \
  -H "Authorization: Bearer {{secret.PAT}}" \       <--- Given by the repository owner
  -H "Accept: application/vnd.github.v3+json" \     
  -H "Content-Type: application/json" \
  https://api.github.com/repos/BDA-KTS/check_workflow_central_repo/dispatches \
  -d '{
    "event_type": "report_creator",  <--- Can alsp be report_creator_tester for the test version
    "client_payload": {
      "repository_full_name": "owner/repo", <--- Payload can be altered for different purposes.
      "repo_hash": "your_hash_here",
      "readme": "README.md"
    }
  }'

## Output Data
The Output Data is found in the directory "report". There you find a directory with the name of the owner with 
the result of the workflow run is stored inside the "repository_name".md. A workflow that aggregates all the results
of every test can be triggered if wished. The workflow can be modified to send emails or other notifications like
raising an issue in the tested repository. 

If the event type was "report_creator_tester" the results will be in the directory 
"Public Testing/reports/owner/repository_name.md" instead.
A top level aggregation of those is not in the scope at the moment (does it even make sense?).

## Hardware Requirements

Given the workflow is running on a GitHub Actions runner, you just need to be able to open a browser to trigger
the workflow via the Methodshub platform.

## Environment Setup

The workflow runs on Github Actions. There is no need for an environment setup.

## How to Use

As already mentioned, you can test your repositories via the Methodshub platform. How to do it will be documented 
as soon as it is implemented.

## Technical Details

The QA workflow is implemented as a GitHub Actions based report generator. 
It is triggered through a "repository_dispatch" event and uses the information provided in the "client_payload"
to identify the repository and commit that should be tested.

The workflow performs the following main steps:

1. Checkout of the central repository  
   The central QA workflow repository is checked out into the "central" directory.
   This repository contains the report generation scripts, configuration files, test definitions, and output directories.

2. Checkout of the repository under test
   The target repository is checked out into the "testee" directory. 
   The repository name and commit hash are taken from the dispatch payload:
   - "repository_full_name"
   - "repo_hash"

3. Python environment setup  
   The workflow uses Python 3.12 and installs the dependencies listed in "requirements.txt".

4. Report generation  
   Depending on the dispatch event type, one of the report generation scripts is executed:
   - "report_creator.py" for regular Methodshub QA reports
   - "public_report_creator.py" for public test reports

   The scripts read the GitHub event payload, inspect the checked-out repository, run the defined QA checks, and create a Markdown report.

5. Report storage  
   Generated reports are written to repository-specific output paths:
   - regular reports: "report/<owner>/<repository>.md"
   - public test reports: "public_testing/report/<owner>/<repository>.md"

6. Aggregation data  
   In addition to the Markdown report, machine-readable aggregation data is created in JSONL format. 
   This data can be used for later summaries, statistics, dashboards, or cross-repository analysis.

7. Commit and push results  
   If a new or changed report or aggregation file was generated, the workflow commits the result back to the central 
   repository. To reduce conflicts from parallel workflow runs, the push step uses "git pull --rebase --autostash" and 
   retries the push several times before failing.

The workflow therefore acts as a central QA service: it receives a repository reference, checks out the exact requested 
revision, generates a report, stores the result, and updates aggregation data for further processing.

## Contact Details

For further inquiries, please contact Taimoor Khan (methodshub@gesis.org).
