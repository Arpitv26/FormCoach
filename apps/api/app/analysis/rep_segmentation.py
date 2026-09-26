"""Backend phase 1 home: smoothing and an explicit movement-phase state machine.

Count only completed reps. Cumulative live snapshots permit deterministic replay.
Do not turn missing landmarks into zero coordinates or assume a phase across long gaps.
"""
