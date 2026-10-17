# Exact late archive-verification failure

Initial invocation of the installed workflow.py verify succeeded:

{"verifiedFiles": 1234, "bytes": 230965430, "allSha256Match": true}

The final read-only invocation returned exit code 1 with this exact output:

```text
Traceback (most recent call last):
  File "C:\Users\10486\.codex\skills\animation-led-teaching-slides\scripts\workflow.py", line 272, in <module>
    main()
  File "C:\Users\10486\.codex\skills\animation-led-teaching-slides\scripts\workflow.py", line 263, in main
    elif args.command == 'verify': verify()
                                   ^^^^^^^^
  File "C:\Users\10486\.codex\skills\animation-led-teaching-slides\scripts\workflow.py", line 200, in verify
    raise ValueError('Archive integrity failure: ' + '; '.join(failures))
ValueError: Archive integrity failure: references/acceptance.md; references/failure-cases.md; references/mainline-branches.md
```

No installed skill file was edited by this run. The changing files are guidance
documents, not staged engine code. The observed mismatch is recorded in
skill-integrity-observation.json with the archive's expected and current hashes.
It does not identify who changed the files and is not silently waived as a pass.

Minimal in-workspace workaround: preserve the original successful start receipt,
record this failed end receipt, freeze the actual authoring source and staged
helper hashes, and finish validation of the actual packaged result with the
already staged engine. No archive index rewrite, environment change, destructive
cleanup, alternate animation backend, or simplified lesson was used.

Stage, build, review, numerical checks, package validation and the frame backend
did not fail. This verification failure is a distinct delivery limitation.
