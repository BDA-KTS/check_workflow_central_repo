# Report for YSKartal of reference_disam

## Report generated at 2026-07-13 12:05:34

## Link to the repository: [GitHub Repository](https://github.com/YSKartal/reference_disam)

## Summary

### Errors ⛔ 

Major Flaws, Error in at least one Check

## File Check

### Information ✅ 

Found required file: citation<br>Found required file: license<br>Found required file: postbuild<br>All required files found

## License Check

### Information ✅ 

Found MIT License, License accepted 

## Readme Check

### Information ✅ 

Found one title: Accepted<br>Found subtitle: Description<br>Found subtitle: Use Cases<br>Found subtitle: Input Data<br>Found subtitle: Output Data<br>Found subtitle: Hardware Requirements<br>Found subtitle: Environment Setup<br>Found subtitle: How to Use<br>Found subtitle: Technical Details<br>Found subtitle: Contact Details

## Binder Test

### Errors ⛔ 

Repo2Docker build failed.<br> Repo2Docker Output:<br>0.0, 2.0.1, 2.0.2, 2.1.0, 2.1.1, 2.1.2, 2.1.3, 2.2.0, 2.2.1, 2.2.2, 2.2.3, 2.2.4, 2.2.5, 2.2.6)
#21 0.795 ERROR: No matching distribution found for numpy==2.4.6
#21 ERROR: process "/bin/sh -c ${KERNEL_PYTHON_PREFIX}/bin/pip install --no-cache-dir -r \"requirements.txt\"" did not complete successfully: exit code: 1
------
 > [16/21] RUN /srv/conda/envs/notebook/bin/pip install --no-cache-dir -r "requirements.txt":
0.743 ERROR: Ignored the following versions that require a different python version: 2.3.0 Requires-Python >=3.11; 2.3.1 Requires-Python >=3.11; 2.3.2 Requires-Python >=3.11; 2.3.3 Requires-Python >=3.11; 2.3.4 Requires-Python >=3.11; 2.3.5 Requires-Python >=3.11; 2.4.0 Requires-Python >=3.11; 2.4.0rc1 Requires-Python >=3.11; 2.4.1 Requires-Python >=3.11; 2.4.2 Requires-Python >=3.11; 2.4.3 Requires-Python >=3.11; 2.4.4 Requires-Python >=3.11; 2.4.5 Requires-Python >=3.11; 2.4.6 Requires-Python >=3.11; 2.5.0 Requires-Python >=3.12; 2.5.0rc1 Requires-Python >=3.12; 2.5.1 Requires-Python >=3.12
0.743 ERROR: Could not find a version that satisfies the requirement numpy==2.4.6 (from versions: 1.3.0, 1.4.1, 1.5.0, 1.5.1, 1.6.0, 1.6.1, 1.6.2, 1.7.0, 1.7.1, 1.7.2, 1.8.0, 1.8.1, 1.8.2, 1.9.0, 1.9.1, 1.9.2, 1.9.3, 1.10.0.post2, 1.10.1, 1.10.2, 1.10.4, 1.11.0, 1.11.1, 1.11.2, 1.11.3, 1.12.0, 1.12.1, 1.13.0, 1.13.1, 1.13.3, 1.14.0, 1.14.1, 1.14.2, 1.14.3, 1.14.4, 1.14.5, 1.14.6, 1.15.0, 1.15.1, 1.15.2, 1.15.3, 1.15.4, 1.16.0, 1.16.1, 1.16.2, 1.16.3, 1.16.4, 1.16.5, 1.16.6, 1.17.0, 1.17.1, 1.17.2, 1.17.3, 1.17.4, 1.17.5, 1.18.0, 1.18.1, 1.18.2, 1.18.3, 1.18.4, 1.18.5, 1.19.0, 1.19.1, 1.19.2, 1.19.3, 1.19.4, 1.19.5, 1.20.0, 1.20.1, 1.20.2, 1.20.3, 1.21.0, 1.21.1, 1.21.2, 1.21.3, 1.21.4, 1.21.5, 1.21.6, 1.22.0, 1.22.1, 1.22.2, 1.22.3, 1.22.4, 1.23.0, 1.23.1, 1.23.2, 1.23.3, 1.23.4, 1.23.5, 1.24.0, 1.24.1, 1.24.2, 1.24.3, 1.24.4, 1.25.0, 1.25.1, 1.25.2, 1.26.0, 1.26.1, 1.26.2, 1.26.3, 1.26.4, 2.0.0, 2.0.1, 2.0.2, 2.1.0, 2.1.1, 2.1.2, 2.1.3, 2.2.0, 2.2.1, 2.2.2, 2.2.3, 2.2.4, 2.2.5, 2.2.6)
0.795 ERROR: No matching distribution found for numpy==2.4.6
------
Dockerfile:131
--------------------
 129 |     COPY --chown=1001:1001 src/requirements.txt ${REPO_DIR}/requirements.txt
 130 |     USER ${NB_USER}
 131 | >>> RUN ${KERNEL_PYTHON_PREFIX}/bin/pip install --no-cache-dir -r "requirements.txt"
 132 |     
 133 |     # ensure root user after preassemble scripts
--------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c ${KERNEL_PYTHON_PREFIX}/bin/pip install --no-cache-dir -r \"requirements.txt\"" did not complete successfully: exit code: 1
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.12.13/x64/bin/repo2docker", line 6, in <module>
    sys.exit(main())
             ^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/repo2docker/__main__.py", line 476, in main
    r2d.start()
  File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/repo2docker/app.py", line 856, in start
    self.build()
  File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/repo2docker/app.py", line 819, in build
    for l in picked_buildpack.build(
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/repo2docker/buildpacks/base.py", line 685, in build
    yield from client.build(**build_kwargs)
  File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/repo2docker/docker.py", line 204, in build
    yield from execute_cmd(args, True)
  File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/repo2docker/utils.py", line 76, in execute_cmd
    raise subprocess.CalledProcessError(ret, cmd)
subprocess.CalledProcessError: Command '['docker', 'buildx', 'build', '--progress', 'plain', '--build-arg', 'NB_USER=runner', '--build-arg', 'NB_UID=1001', '--tag', 'r2dtestee1783944265', '--platform', 'linux/amd64', '/tmp/tmpi2voetcx']' returned non-zero exit status 1.


## Taxonomie

### Information ✅ 

Predicted labels: Data Analysis<br>Probability: 66.04%

#### Duration 

Time to complete 1 min 8 sec

