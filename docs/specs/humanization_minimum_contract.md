# Humanization Minimum Contract

> Date: 2026-03-09
> Prerequisite: `LOCAL_VERTICAL_SLICE_REAL_MUSETALK` milestone must be complete before starting humanization work.
> Scope: First mandatory realism package for avatar presence.

## Goal

Make the AI avatar visually indistinguishable from a real person in casual TikTok Live viewing at 480p-720p resolution, for the first 30 seconds of exposure.

## Required Behaviors

### 1. Blink

- Natural blink rate: 15-20 blinks per minute
- Blink duration: 100-400ms
- Randomized interval (not periodic)
- Both eyes blink together

### 2. Eye Drift

- Subtle horizontal/vertical gaze shifts during idle and speaking
- Gaze returns to approximate center within 1-2 seconds
- No fixed stare for more than 3 seconds
- Amplitude: 2-5% of face width

### 3. Idle Head Micro-Motion

- Continuous subtle head movement when not speaking
- Amplitude: 1-3 degrees rotation, 1-2px translation
- Frequency: slow, organic (0.2-0.5 Hz base with noise)
- Must not look robotic or periodic

### 4. Idle Non-Speaking Presence

- Avatar must not freeze when not speaking
- Breathing motion (subtle chest/shoulder rise)
- Occasional lip press or slight mouth movement
- Occasional small head tilt

### 5. Pacing / Response Delay Policy

- Do not respond instantly to chat messages
- Minimum thinking delay: 500ms-1500ms (randomized)
- Occasional longer pauses (2-3s) as if reading
- Typing indicator or "hmm" sounds during delay

## Acceptance Criteria

Each behavior must be:

1. **Visible** in recorded output at 30fps, 720p
2. **Randomized** -- no two 10-second segments should look identical
3. **Configurable** -- intensity parameters exposed in config
4. **Independent** -- each behavior can be enabled/disabled separately
5. **Tested** -- at least one unit test proving the behavior fires

## Out of Scope (This Contract)

- Emotion-driven facial expression changes
- Hand gestures
- Body posture shifts
- Lip sync quality improvements (covered by MuseTalk)
- Voice prosody / intonation changes
- Multi-camera angle simulation

## Implementation Approach

These behaviors should be implemented as post-processing overlays on top of the MuseTalk output frames, not as modifications to the MuseTalk model itself. This keeps the humanization layer decoupled from the face engine.

## Measurement

Record a 30-second clip and ask 3 people: "Is this a real person or AI?" If 2/3 say "not sure" or "real person" at 480p, the humanization package meets minimum bar.
