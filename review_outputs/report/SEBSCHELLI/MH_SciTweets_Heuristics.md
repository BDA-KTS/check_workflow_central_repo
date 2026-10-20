# Report: [SEBSCHELLI / MH_SciTweets_Heuristics](https://github.com/SEBSCHELLI/MH_SciTweets_Heuristics)

<small>created on 2026-10-20 09:28:34, 
 Review time: 0:00 (min/sec)

## Summary 

[Technical review framework](https://github.com/BDA-KTS/check_workflow_central_repo/blob/main/technical-review-framework.md) 
| Category | Level attained | Guidelines reference | 
| :--- | :--- | :--- | 
| Reusability and attribution | ![Reusability](https://img.shields.io/badge/Reusability-not%20reusable-orange) || Citation file not found [for more ...](#Transparency) | 
| Transparency | ![Transparency](https://img.shields.io/badge/Transparency-incomplete%20documentation-orange) |  README missing mandatory sections, [for more ...](#Transparency) | 
| Computational reproducibility | ![Reproducibility](https://img.shields.io/badge/Reproducibility-partially%20reproducible-yellow) |  programming language version not specified, [for more ...](#Computational-reproducibility) | 
| Resource consumption | not computed due to Repo2docker failure | | 


# Detailed Report 

## Reusability and Attribution (License, CITATION) 

The method is reusable if supported by a valid open-source licence and has citation metadata provided in supported CITATION.CFF file. 
-  ✅ **Information:** License MIT accepted as an open license 


-  ⛔ **Errors:** No valid CITATION.CFF file found, please consult the [documentation quality criteria in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/README.md#documentation-quality-criteria) 
## Transparency (Files, README Template) 

The method is fully transparent when it has all required documents and has README as per [Methods Hubtemplate](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md?plain=1). 
-  ✅ **Information:** license:license 
-  ✅ **Information:** requirements.txt 
-  ✅ **Information:** binder 
-  ✅ **Information:** All required documents found 


-  ⛔ **Errors:** Method has 5, i.e., more than 1 title cases., please consult the [README template in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md?plain=1) 
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

Computational reproducibility is supported if repo2docker successfully builds the execution environment and the programming language version is explicitly specified in the repository’s configuration files. 
-  ⛔ **Errors:** Repo2Docker test failed with unexpected error: name 'TEST_PATH' is not defined, please consult the [binder environment in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/README.md#binder-environment) 


-  ⚠️ **Warnings:** Python/R version is not specified for the method 


