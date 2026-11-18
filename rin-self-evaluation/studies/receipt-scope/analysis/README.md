# Joined and descriptive analysis

These scripts derive additional views from the completed 32-run native record. They do not launch participants, alter source evidence, replace the frozen mechanical scorer or revise semantic judgments. The source is written before native outcomes are available.

After all native records and `results/observed.json` exist, run:

```sh
python3 -B delivery-study/analysis/describe_runs.py
```

After the fresh reviewer returns an actual `REVIEW SEALED <digest>` acknowledgement, record that exact line in `review/native_review_receipt.txt`. Only then reveal the identity map using the frozen review tool. Join the sealed review afterward:

```sh
python3 -B delivery-study/analysis/join_review.py
```

The scripts recompute the frozen mechanical results and reject a different `observed.json`. The review join also verifies the exact packet, raw judgments, actual retained acknowledgement and identity-map bindings. It preserves every raw judgment and leaves `substantive_adjudications` empty. Any later adjudication requires a separate record.

Outputs retain exact source/input hashes, all eight assigned contexts per selector/receipt-scope cell, and the four original/four reflected strata. Paired scope and paired selector comparisons reuse those same native contexts. Conditional unfinished-work counts retain their own denominator. Repeated contexts in this selected family do not become independently sampled task families or population reliability estimates.

Trace descriptions include service/wait and free-status sequences, opening choice, resources and report size. Client stdout byte counts measure supplied execution-path output, not model tokens, awareness or independent platform telemetry. Orchestration source and parser-choice prevalence are not measured by the native records. All derived output files are either newly created or verified byte-identical; the scripts refuse to overwrite a different result.
