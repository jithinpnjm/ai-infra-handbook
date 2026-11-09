# Post-mortem: the outage

- Owner: SRE team
- Status: draft

## Summary

Human error during a config push broke the endpoint.

## Impact

Users were unhappy.

## Timeline

Things happened in the morning.

## Root cause

An engineer forgot to check the canary.

## Action items

| Action | Type | Owner | Due | Measure |
|---|---|---|---|---|
| Improve monitoring | detect | everyone | soon | better |
| Be more careful with config pushes | prevent | Sam | 2026-05-01 | |
