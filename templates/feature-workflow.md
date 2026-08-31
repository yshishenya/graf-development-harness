# Feature workflow

1. Create a clean disposable worktree from the integration branch.
2. Atomically claim the next Feature ID against local specs, all refs, the
   tracker and the umbrella issue. A local maximum is not a reservation.
3. Create the branch and Spec Kit directory only after the claim succeeds.
4. Keep the root agent guide and root changelog immutable during feature work.
   Write only the feature-owned `changes/unreleased/F<id>.yaml` fragment.
5. Run the risk-lane Spec Kit sequence and sync executable tasks to the tracker.
6. Run focused tests, then fast CI on the exact PR SHA. If the SHA changes,
   invalidate the old evidence and rerun; never attach stale results. The
   checked worktree must be clean so the SHA identifies the tested bytes.
7. Freeze a release candidate containing exact SHA and changelog digest. Run
   one authoritative Full CI for that candidate, then prepare tag/release notes.

Parallel feature work is allowed; promotion to one shared Dev target and the
release train are serialized by an explicit lock and immutable manifest.
