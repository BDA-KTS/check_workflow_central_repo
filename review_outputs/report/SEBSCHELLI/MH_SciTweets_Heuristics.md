# Report: [SEBSCHELLI / MH_SciTweets_Heuristics](https://github.com/SEBSCHELLI/MH_SciTweets_Heuristics)

<small>created on 2026-10-09 21:47:01, taking 0:31 (min/sec)

### ![Reusability](https://img.shields.io/badge/Reusability-supported-green) 

 -  ✅ **Information:** Citation file exists 
### ![Transparency](https://img.shields.io/badge/Transparency-not%20supported-orange) 

 -  ⛔ **Errors:** Method has 5, more than 1 titles. 
### ![Reproducibility](https://img.shields.io/badge/Reproducibility-not%20supported-orange) 

 -  ⛔ **Errors:** Repo2Docker build failed. 
 -  ⛔ **Errors:** _PYTHON_PREFIX}
# Run pre-assemble scripts! These are instructions that depend on the content
# of the repository but don't access any files in the repository. By executing
# them before copying the repository itself we can cache these steps. For
# example installing APT packages.
# If scripts required during build are present, copy them

COPY --chown=1001:1001 src/requirements.txt ${REPO_DIR}/requirements.txt
USER ${NB_USER}
RUN ${KERNEL_PYTHON_PREFIX}/bin/pip install --no-cache-dir -r "requirements.txt"

# ensure root user after preassemble scripts
USER root

# Copy stuff.
COPY --chown=1001:1001 src/ ${REPO_DIR}/

# Run assemble scripts! These will actually turn the specification
# in the repository into an image.


# Container image Labels!
# Put these at the end, since we don't want to rebuild everything
# when these change! Did I mention I hate Dockerfile cache semantics?

LABEL repo2docker.ref="None"
LABEL repo2docker.repo="testee"
LABEL repo2docker.version="2026.4.0"

# We always want containers to run as non-root
USER ${NB_USER}

# Make sure that postBuild scripts are marked executable before executing them
RUN chmod +x postBuild
RUN ./postBuild

# Add start script
# Add entrypoint
ENV PYTHONUNBUFFERED=1
COPY --chmod=0755 /python3-login /usr/local/bin/python3-login
COPY --chmod=0755 /repo2docker-entrypoint /usr/local/bin/repo2docker-entrypoint
ENTRYPOINT ["/usr/local/bin/repo2docker-entrypoint"]

# Specify the default command to run
CMD ["jupyter", "notebook", "--ip", "0.0.0.0"]

Using PythonBuildPack builder
#0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 5.79kB done
#1 DONE 0.0s

#2 [auth] library/buildpack-deps:pull token for registry-1.docker.io
#2 DONE 0.0s

#3 [internal] load metadata for docker.io/library/buildpack-deps:24.04
#3 ERROR: failed to authorize: failed to fetch oauth token: unexpected status from POST request to https://auth.docker.io/token: 504 Gateway Timeout: error code: 504

------
 > [internal] load metadata for docker.io/library/buildpack-deps:24.04:
------
Dockerfile:2
--------------------
   1 |     
   2 | >>> FROM docker.io/library/buildpack-deps:24.04
   3 |     
   4 |     # Avoid prompts from apt
--------------------
ERROR: failed to build: failed to solve: docker.io/library/buildpack-deps:24.04: failed to resolve source metadata for docker.io/library/buildpack-deps:24.04: failed to authorize: failed to fetch oauth token: unexpected status from POST request to https://auth.docker.io/token: 504 Gateway Timeout: error code: 504

Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.12.15/x64/bin/repo2docker", line 6, in <module>
    sys.exit(main())
             ^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/repo2docker/__main__.py", line 476, in main
    r2d.start()
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/repo2docker/app.py", line 856, in start
    self.build()
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/repo2docker/app.py", line 819, in build
    for l in picked_buildpack.build(
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/repo2docker/buildpacks/base.py", line 685, in build
    yield from client.build(**build_kwargs)
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/repo2docker/docker.py", line 204, in build
    yield from execute_cmd(args, True)
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/repo2docker/utils.py", line 76, in execute_cmd
    raise subprocess.CalledProcessError(ret, cmd)
subprocess.CalledProcessError: Command '['docker', 'buildx', 'build', '--progress', 'plain', '--build-arg', 'NB_USER=runner', '--build-arg', 'NB_UID=1001', '--tag', 'r2dtestee1791582390', '--platform', 'linux/amd64', '/tmp/tmp49zzkeme']' returned non-zero exit status 1.
 
 Binder Test 
  ⛔ **Errors:** ['Repo2Docker build failed.', ' Timeout: error code: 504\n\n------\n > [internal] load metadata for docker.io/library/buildpack-deps:24.04:\n------\nDockerfile:2\n--------------------\n   1 |     \n   2 | >>> FROM docker.io/library/buildpack-deps:24.04\n   3 |     \n   4 |     # Avoid prompts from apt\n--------------------\nERROR: failed to build: failed to solve: docker.io/library/buildpack-deps:24.04: failed to resolve source metadata for docker.io/library/buildpack-deps:24.04: failed to authorize: failed to fetch oauth token: unexpected status from POST request to https://auth.docker.io/token: 504 Gateway Timeout: error code: 504\n\nTraceback (most recent call last):\n  File "/opt/hostedtoolcache/Python/3.12.15/x64/bin/repo2docker", line 6, in <module>\n    sys.exit(main())\n             ^^^^^^\n  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/repo2docker/__main__.py", line 476, in main\n    r2d.start()\n  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/repo2docker/app.py", line 856, in start\n    self.build()\n  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/repo2docker/app.py", line 819, in build\n    for l in picked_buildpack.build(\n             ^^^^^^^^^^^^^^^^^^^^^^^\n  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/repo2docker/buildpacks/base.py", line 685, in build\n    yield from client.build(**build_kwargs)\n  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/repo2docker/docker.py", line 204, in build\n    yield from execute_cmd(args, True)\n  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/site-packages/repo2docker/utils.py", line 76, in execute_cmd\n    raise subprocess.CalledProcessError(ret, cmd)\nsubprocess.CalledProcessError: Command \'[\'docker\', \'buildx\', \'build\', \'--progress\', \'plain\', \'--build-arg\', \'NB_USER=runner\', \'--build-arg\', \'NB_UID=1001\', \'--tag\', \'r2dtestee1791582422\', \'--platform\', \'linux/amd64\', \'/tmp/tmppfthhp6v\']\' returned non-zero exit status 1.\n'] 
### Resource Consumption 

Environment validation: FAILBuild time: 30.62 secondsPeak Python process memory: 57724CPU utilization: Not measuredEnergy consumption: Not measuredCO₂ emissions: Not measured