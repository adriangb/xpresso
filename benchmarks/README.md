# Benchmarks

## Usage

Open two terminals and start an app in one of them:

```shell
# or . ./benchmarks/run_app.sh fastapi
. ./benchmarks/run_app.sh xpresso
```

In the other terminal, start the benchmarks:

```shell
. ./benchmarks/run_wrk.sh /fast_deps
```

The options are:

- `/simple`: an endpoint that does nothing, this measures framework overhead mainly.
- `/slow_deps`: a largish dependency graph where each dependency calls `asyncio.sleep(<random number between 1e-3 and 1e-1>)`.
- `/fast_deps`: a largish dependency graph where each dependency is an async dependency that just calls `asyncio.sleep(0)`.
- `/routing/one/two-one/one-two-one`: test routing performance on an endpoint that does nothing but is nested within a large routing table.
