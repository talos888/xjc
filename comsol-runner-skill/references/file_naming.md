# File Naming

Use separate folders for tests, formal runs, and exports.

```text
project/tests
project/runs
project/exports
```

Test files:

```text
test_YYYYMMDD_NN_short-purpose.mph
```

Formal setup files:

```text
sim_YYYYMMDD_NN_short-purpose_setup.mph
```

Formal solved files:

```text
sim_YYYYMMDD_NN_short-purpose_solved.mph
```

Exports:

```text
export_YYYYMMDD_NN_short-purpose_quantity.ext
```

For tests, overwriting is acceptable if the user agrees. For formal runs, keep
setup and solved files separate.

