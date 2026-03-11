# Brain Director Runtime Design

**Date:** 2026-03-12

## Goal

Pulihkan otak dasar live commerce dengan tiga fondasi:
- `ShowDirector` persistent sebagai source of truth runtime live
- `PromptRegistry` versioned untuk persona, prompt pack, dan script phases
- runtime contract agregat yang bisa dibaca UI tanpa bergantung pada variabel global di API

## Problem Statement

State live sekarang tersebar dan tidak bisa dipercaya sebagai control plane operator:
- pipeline state masih bergantung pada variabel global di [api.py](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/src/dashboard/api.py)
- prompt utama masih hardcoded di [persona.py](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/src/brain/persona.py)
- UI brain/orchestrator hanya melihat health dan test prompt, belum melihat active prompt pack, phase runtime, atau decision path
- runtime truth di [truth.py](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/src/dashboard/truth.py) masih membaca state privat dari API, bukan service runtime yang persistent

## Architecture

### 1. ShowDirector

Tambahkan service baru `src/orchestrator/show_director.py`.

Tanggung jawab:
- menyimpan state lifecycle live: `IDLE`, `SELLING`, `REACTING`, `ENGAGING`, `PAUSED`, `STOPPED`
- menyimpan history transition dan metadata uptime
- menyimpan runtime flags: `stream_running`, `emergency_stopped`, `manual_override`
- menyimpan current phase script dan current product context
- menyediakan runtime snapshot tunggal untuk API dan websocket

Service ini diinisialisasi sekali per proses server dan dipakai melalui getter singleton.

### 2. PromptRegistry

Tambahkan `src/brain/prompt_registry.py`.

Tanggung jawab:
- menyimpan prompt pack aktif dan draft versioned
- menyediakan revision metadata: `id`, `slug`, `version`, `status`, `created_at`
- menyediakan prompt template untuk:
  - system persona base
  - selling prompt
  - reacting prompt
  - engaging prompt
  - filler prompt
  - 7 phase selling structure
- menyediakan fallback bootstrap pack default agar sistem tetap hidup walaupun database kosong

Storage:
- gunakan SQLite melalui helper [database.py](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/src/data/database.py)
- secret tetap di env; registry hanya menyimpan content dan policy non-secret

### 3. PersonaEngine as Composer

[persona.py](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/src/brain/persona.py) tidak lagi menjadi pemilik prompt literal.

Peran baru:
- membaca active prompt pack dari `PromptRegistry`
- mengisi placeholder context: host name, product context, viewer count, additional context
- menyediakan API yang tetap kompatibel bagi caller lama

### 4. Runtime Contract

Tambahkan contract agregat untuk UI, misalnya `director_runtime_snapshot`:
- `director`: state, phase, uptime, history, stream/emergency/manual flags
- `brain`: active provider/model, routing table, health, fallback order, budget
- `prompt`: active pack, active revision, version, updated_at
- `persona`: name, tone, language, forbidden topics, catchphrases
- `script`: current phase, phase map, current product
- `evidence`: last decision, latency, cost, fallback path

Kontrak ini dipakai oleh:
- `GET /api/director/runtime`
- `GET /api/runtime/truth` untuk ringkasan
- websocket `/api/ws/dashboard`

### 5. UI Placement

IA 6-menu tetap dipertahankan.

Surface baru:
- `Setup & Validasi`
  - tambah section `Brain & Prompt`
  - tampilkan config, routing, active prompt pack, active revision, provider health
- `Konsol Live`
  - tampilkan `Director Runtime`
  - tampilkan current phase, phase history, active provider/model, active prompt version

Layout shell:
- content wrapper full-width tetapi centered
- sidebar fixed/sticky dan tidak ikut bergeser saat content tinggi
- panel-grid responsif untuk 375/768/1024/1440

## API Changes

Read-focused minimum:
- `GET /api/director/runtime`
- `GET /api/brain/config` diperluas dengan prompt registry metadata

Refactor existing endpoints:
- `/api/status`
- `/api/pipeline/state`
- `/api/pipeline/transition`
- `/api/emergency-stop`
- `/api/emergency-reset`
- websocket `/api/ws/dashboard`

Semua endpoint itu harus membaca `ShowDirector`, bukan variabel global privat.

## Safety Constraints

- API key dan secret provider tidak boleh tampil di UI
- prompt revision publish/rollback belum harus editable di fase pertama, tetapi contract harus siap
- jika registry gagal load, bootstrap pack default tetap dipakai dan surface UI harus memberi warning informatif

## Verification

Minimum evidence untuk fase implementasi pertama:
- unit tests untuk `ShowDirector`
- unit tests untuk `PromptRegistry` default bootstrap + version metadata
- dashboard API tests untuk `director/runtime` dan `pipeline transition`
- frontend tests untuk shell centering/fixed sidebar dan director runtime cards
- build frontend
- targeted Playwright validation untuk layout dan sidebar behavior
