#check_workflow_central_repo
The central workflow will be created here. Description follows up on tuesday.

## Description
The Central Workflow can be used to test other repositories how well they fullfill the technical conditions of the methodhub Platform.

## Use Cases
Use Case can be every Method or Tutorial, that will be submitted via the methodhub
## Input Data
Input Data is a Curl request. It needs to be structured like this:

curl -X POST \
  -H "Authorization: Bearer {{secret.PAT}}" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/BDA-KTS/check_workflow_central_repo/dispatches \
  -d '{
    "event_type": "method",
    "client_payload": {
      "repository_full_name": "owner/repo",
      "repo_hash": "1ddf824",
      "readme": "README.md"
    }
  }'

The secret Pat can be contained via contacting me (See Contact Details)

## Output Data
Output Data will be inside the Repository itself in the directory report. It is still under construction

## Hardware Requirements

If your toaster can handle to open a console or something similar. It can use this function.

## Environment Setup

A PAT is needed, get it via contacting me (at the moment)
## How to Use

Use anything that is able to send a POST Request, build like:

curl -X POST \
  -H "Authorization: Bearer {{secret.PAT}}" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/BDA-KTS/check_workflow_central_repo/dispatches \
  -d '{
    "event_type": "method",
    "client_payload": {
      "repository_full_name": "owner/repo",
      "repo_hash": "1ddf824",
      "readme": "README.md"
    }
  }'

## Technical Details

Under construction

## Contact Details
