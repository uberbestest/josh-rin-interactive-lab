# Round 09 reproduction card

This card points to the existing release instructions. It adds no scientific evidence and changes no archived files.

1. Extract `round-09.zip` into a new working directory and enter `continuation-repair`.
2. Read its `README.md`, including the distinction between the main study and the exploratory diagnostics.
3. With Python 3.12 and Node.js available on a POSIX system, run `python3 verify.py --reproduce --output main-verification.json`. The command performs new scripted executions as well as checking saved evidence.
4. Check the separately retained exploratory diagnostics with `python3 -B verify_posthoc.py --output exploratory-verification.json`. Keep these outside the main-study denominator.
5. Preserve your new command output and generated receipts. Consult `results/summary.json`, `provenance/RESULT_AUDIT.md`, and `CONTROLLER_DESIGN.md` to explain the results and assumptions.
6. A successful local reproduction is a same-lab check of this finite study. Describe its scope accurately.
