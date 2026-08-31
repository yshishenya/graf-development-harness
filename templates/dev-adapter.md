# Consumer Dev adapter contract

The portable harness does not know a product's runtime. A consumer adapter
must provide these bounded operations:

- `build(exact_sha)` — produce metadata and real component artifacts tied to
  that SHA;
- `promote(manifest)` — acquire one machine/repository-global lock, validate
  the manifest and atomically activate it;
- `smoke(manifest)` — check backend, frontend, worker/dependencies and the
  selected client target;
- `rollback(previous_manifest)` — restore the previous runtime and client,
  prove health, then publish the active pointer.

The adapter must be loopback/dev-only, keep credentials outside manifests and
evidence, refuse production-looking origins/data paths, and compensate a
partial promotion before changing the active pointer. A live idempotent build
is valid only when all expected artifacts exist and their digests match.
