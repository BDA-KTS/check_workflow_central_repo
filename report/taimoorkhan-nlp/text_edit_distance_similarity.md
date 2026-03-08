# Report for taimoorkhan-nlp of text_edit_distance_similarity
## Report generated at 2026-03-08 22:51:36
## Checking for required files
Found required file: citation 
Found required file: license 
Found required file: postbuild 
No duplicate files found.
Found required file: requirements.txt in  
All Binder Files found 
No duplicate files found.
## Checking License: 
Found one title: Accepted
Found subtitle: Description
Found subtitle: Use Cases
Found subtitle: Input Data
Found subtitle: Output Data
Found subtitle: Hardware
Found subtitle: Environment Setup
Found subtitle: How to Use
Found subtitle: Technical Details
Found subtitle: Publications
Found subtitle: Contact Details
Missing subtitle: Hardware Requirements
## Testing repository with repo2docker
Repo2Docker build failed.
### Repo2Docker Output:
```text
/opt/hostedtoolcache/Python/3.12.12/x64/lib/python3.12/site-packages/requests/__init__.py:113: RequestsDependencyWarning: urllib3 (2.6.3) or chardet (7.0.1)/charset_normalizer (3.4.5) doesn't match a supported version!
  warnings.warn(
[Repo2Docker] Looking for repo2docker_config in /home/runner/work/check_workflow_central_repo/check_workflow_central_repo
Picked Local content provider.
Using local repo testee.
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.12.12/x64/bin/repo2docker", line 6, in <module>
    sys.exit(main())
             ^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.12/x64/lib/python3.12/site-packages/repo2docker/__main__.py", line 476, in main
    r2d.start()
  File "/opt/hostedtoolcache/Python/3.12.12/x64/lib/python3.12/site-packages/repo2docker/app.py", line 846, in start
    self.build()
  File "/opt/hostedtoolcache/Python/3.12.12/x64/lib/python3.12/site-packages/repo2docker/app.py", line 790, in build
    picked_buildpack.render(build_args),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.12/x64/lib/python3.12/site-packages/repo2docker/buildpacks/base.py", line 496, in render
    for user, script in self.get_assemble_scripts():
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.12/x64/lib/python3.12/site-packages/repo2docker/buildpacks/python/__init__.py", line 193, in get_assemble_scripts
    if not self._should_preassemble_pip:
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.12/x64/lib/python3.12/site-packages/repo2docker/buildpacks/python/__init__.py", line 142, in _should_preassemble_pip
    with open_guess_encoding(requirements_txt) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.12/x64/lib/python3.12/contextlib.py", line 137, in __enter__
    return next(self.gen)
           ^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.12/x64/lib/python3.12/site-packages/repo2docker/utils.py", line 100, in open_guess_encoding
    detector = chardet.universaldetector.UniversalDetector()
               ^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: module 'chardet' has no attribute 'universaldetector'. Did you mean: 'UniversalDetector'?
\n```
