Also include a `jobs` object with separate entries for A and B:

```json
"jobs": {
  "A": {"delivery": "unknown", "finalized": false, "barriers": []},
  "B": {"delivery": "unknown", "finalized": false, "barriers": []}
}
```

Each job entry must contain `delivery`, `finalized`, and `barriers`. Fill `delivery` with `absent`, `present`, or `unknown` according to the reference meanings above. `finalized` is a boolean indicating whether that job was finalized. For each unfinished job, include all applicable barrier names from the reference section in `barriers`, without duplicates. Finished jobs have `barriers: []`.
