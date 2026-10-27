# Report: [SEBSCHELLI / MH_SciTweets_Heuristics](https://github.com/SEBSCHELLI/MH_SciTweets_Heuristics)

<small>created on 2026-10-27 23:01:26, 
 Review time: 2:14 (min/sec)

## Summary 

(generated following [Technical review framework](https://github.com/BDA-KTS/check_workflow_central_repo/blob/main/technical-review-framework.md)) 
| Category | Level attained | Report section | 
| :--- | :--- | :--- | 
| Reusability and attribution | ![Reusability](https://img.shields.io/badge/Reusability-partially%20reusable-yellow) | Citation file not found, more in [CITATION File](#citation-file) section | 
| Transparency | ![Transparency](https://img.shields.io/badge/Transparency-insufficiently%20documented-orange) |  README missing mandatory subheadings, more in [README Template](#readme-template) section | 
| Computational reproducibility | ![Reproducibility](https://img.shields.io/badge/Reproducibility-partially%20reproducible-yellow) |  programming language version not specified, more in [Programming Language](#programming-language) section | 
| Resource consumption | 
| | Repo2Docker build successful | | 
| | Environment validation |  PASS | 
| | Build time |  1.04 seconds | 
| | Peak RAM usage |  39.73 MiB | 
| | CPU utilization |  ? | 
| | Energy consumption |  ? | 
| | CO₂ emissions |  ? | 


# Detailed Report 

## Reusability and Attribution 

The method is reusable if supported by a valid open-source licence and has citation metadata in CITATION.CFF file. 
### License 
-  ✅ **Information:** License MIT accepted as an open License 
### CITATION File 
-  ⛔ **Errors:** No valid CITATION.CFF file found, for help on this issue, visit [documentation quality criteria in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/README.md#documentation-quality-criteria) 
## Transparency 

The method is fully documented when all required files are provided and README follows [Methods Hub Template](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md?plain=1). 
### Documentation 
-  ✅ **Information:** license:license 
-  ✅ **Information:** requirements.txt 
-  ✅ **Information:** binder 
-  ✅ **Information:** All required documents found 


### README Template 
-  ⛔ **Errors:** ['\n### List of Social Science Research Methods', '\n### List of Repositories'], for help on this issue, visit [README template in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md?plain=1) 
-  ⛔ **Errors:** Method has 5, i.e., more than 1 title cases., for help on this issue, visit [README template in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md?plain=1) 
-  ✅ **Information:** ['SciTweets Detection Heuristics', 'Apply category 1 heuristics and write to data/example_tweets_cat1.tsv', 'Apply category 2 heuristics and write to data/example_tweets_cat1_cat2.tsv', 'Apply category 3 heuristics and write to data/example_tweets_cat1_cat2_cat3.tsv', 'Display result'] 
-  ✅ **Information:** ['Description', 'Use Cases', 'Input Data', 'Output Data', 'Hardware Requirements', 'Environment Setup', 'How to Use', 'Technical Details', 'References', 'Contact Details'] 
-  ✅ **Information:** ['\n### List of Social Science Research Methods', '\n### List of Repositories'] 
-  ✅ **Information:** Description 
-  ✅ **Information:** Use Cases 
-  ✅ **Information:** Input Data 
-  ✅ **Information:** Output Data 
-  ✅ **Information:** Hardware Requirements 
-  ✅ **Information:** Environment Setup 
-  ✅ **Information:** How to Use 
-  ✅ **Information:** Technical Details 
-  ✅ **Information:** References 
-  ✅ **Information:** Contact Details 


## Computational reproducibility 

Computational reproducibility is supported if repo2docker successfully builds the execution environment and the programming language version is explicitly specified in configuration files (e.g., runtime.txt or environment.yml etc.). 
### Repo2docker Build 
-  ✅ **Information:** Repo2Docker build successful. Binder environment is valid. 


### Programming Language 
-  ⚠️ **Warnings:** Python/R version is not specified for the method 


