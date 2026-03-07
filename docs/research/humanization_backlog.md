# Humanization Backlog

> **Status**: Backlog (prioritized after operational stability)
> **Date**: 2026-03-07

## Backlog Items

| Priority | Item | Description | Complexity |
|----------|------|-------------|------------|
| P1 | Response delay variance | Add 0.5-2s random delay before responding | Low |
| P1 | Safe fallback phrases | Pre-defined responses when LLM fails | Low |
| P2 | Filler token insertion | Add "ehm", "nah", "jadi" between sentences | Medium |
| P2 | Pacing variation | Vary speech speed per sentence | Medium |
| P2 | Natural silence windows | 2-5s pauses between topics | Low |
| P3 | Script segmentation | Break long scripts into natural chunks | Medium |
| P3 | Emotional pacing | Match speech pace to emotional content | High |
| P3 | Breathing simulation | Add subtle breathing sounds | Medium |

## Implementation Notes

- All humanization features should be toggleable via config
- Start with P1 items (low complexity, high impact)
- Do NOT implement before vertical slice is stable
