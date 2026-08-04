Reference expectation for T18 (launch: none — graders only).

The three state_check graders pipe canned PostToolUse events through the plugin's lint script and assert the VERDICT line and exit code for the block, pass, and skip paths. A correct implementation of skills/advise/scripts/lint_outputs.py satisfies all three; no workspace artifacts are involved.
