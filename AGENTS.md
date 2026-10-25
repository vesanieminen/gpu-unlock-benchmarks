# Benchmark work rules

For benchmark preparation, dependency installation, driver/boot configuration,
gpu-unlock installation, verification, rollback and benchmark commands, use
`python3 record.py --system SYSTEM --phase PHASE -- COMMAND ARG...`.
The benchmark launcher run.sh records itself; do not wrap it twice.
For shell constructs, record `bash -x -c '...'` so the expanded commands appear
in the transcript. Preserve failures as well as successes. Use pkexec through
the recorder if elevated permissions are required and authorized.

Record commands immediately, not as reconstructed history later. Prior commands
may only be documented as reconstructed, with known outcomes and unknown times
or output clearly identified. Never invent command output or test results.

Keep systems separate: rtx3080 is this machine, dual-rtx3090 is another host.
Do not modify power limits or clocks unless specifically requested. Preserve
identical software, scripts, model revision and runtime settings across each
system's before/after comparison. Record any unavoidable differences.

Keep downloaded weights, caches and credentials out of Git. Review transcripts
for credentials before committing; do not place tokens or passwords in command
arguments. Retain raw benchmark samples and GPU telemetry. Benchmark execution
is not authorization to install gpu-unlock or change boot/driver settings.
