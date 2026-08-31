# Legacy Impact

Every feature and pull request must contain exactly one classification:

```text
Classification: remove | retain-with-exception | untouched
```

`remove` deletes the old path in the same slice. `untouched` is valid only when
the feature does not change compatibility behavior. `retain-with-exception`
requires all fields below and a separate retirement task:

```text
Owner: <person or team>
Expiry: <YYYY-MM-DD>
Removal trigger: <observable condition>
Risk: <bounded risk>
Validation: <proof command or scenario>
Retirement task: <issue or task id>
```

New aliases, fallback names, flags, dependencies, fixtures and documentation
paths that preserve an old behavior are legacy and must be rejected or removed.
