"""SQLite-backed dashboard control plane for single-host live operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.data import database as data_database
from src.utils.logging import get_logger

logger = get_logger("control_plane.store")


def _json_dumps(value: Any) -> str:
    return json.dumps({} if value is None else value, ensure_ascii=True)


def _json_loads(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


class ControlPlaneStore:
    """Durable controller state for products, stream targets, and live session flow."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else data_database.DB_PATH
        data_database.init_database(self.db_path)

    def _connection(self):
        return data_database.get_connection(self.db_path)

    def _record_command(
        self,
        command_name: str,
        status: str,
        payload: dict[str, Any] | None = None,
        session_id: int | None = None,
        actor: str = "operator",
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO operator_commands (session_id, command_name, payload_json, status, actor)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, command_name, _json_dumps(payload or {}), status, actor),
            )

    def _record_event(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        session_id: int | None = None,
        severity: str = "info",
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO runtime_events (session_id, event_type, payload_json, severity)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, event_type, _json_dumps(payload or {}), severity),
            )

    @staticmethod
    def _mask_stream_key(stream_key: str) -> str:
        if not stream_key:
            return ""
        if len(stream_key) <= 3:
            return "*" * len(stream_key)
        return f"{'*' * max(len(stream_key) - 3, 3)}{stream_key[-3:]}"

    def _product_from_row(self, row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "price": float(row["price"]),
            "price_formatted": f"Rp {float(row['price']):,.0f}",
            "image_path": row["image_path"] or "",
            "description": row["description"] or "",
            "stock": int(row["stock"] or 0),
            "category": row["category"] or "general",
            "margin_percent": float(row["margin_percent"] or 0.0),
            "is_active": bool(row["is_active"]),
            "affiliate_links": _json_loads(row["affiliate_links_json"], {}),
            "selling_points": _json_loads(row["selling_points_json"], []),
            "commission_rate": float(row["commission_rate"] or 0.0),
            "objection_handling": _json_loads(row["objection_handling_json"], {}),
            "compliance_notes": row["compliance_notes"] or "",
        }

    def _stream_target_from_row(self, row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "platform": row["platform"],
            "label": row["label"],
            "rtmp_url": row["rtmp_url"],
            "stream_key_masked": self._mask_stream_key(row["stream_key"]),
            "is_active": bool(row["is_active"]),
            "enabled": bool(row["enabled"]),
            "validation_status": row["validation_status"],
            "validation_checks": _json_loads(row["validation_checks_json"], []),
            "last_validated_at": row["last_validated_at"],
        }

    def _session_row_to_payload(self, row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "platform": row["platform"],
            "status": row["status"],
            "stream_target_id": row["stream_target_id"],
            "rotation_mode": row["rotation_mode"],
            "qna_mode": row["qna_mode"],
            "pause_reason": row["pause_reason"] or "",
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
        }

    def _session_state_from_row(self, row: Any | None) -> dict[str, Any]:
        if row is None:
            return {
                "current_mode": "ROTATING",
                "current_phase": "IDLE",
                "rotation_paused": False,
                "pause_reason": "",
                "current_focus_product_id": None,
                "current_focus_session_product_id": None,
                "pending_question": None,
                "awaiting_operator": False,
                "active_prompt_revision": "",
                "active_provider": "",
                "active_model": "",
                "stream_status": "idle",
            }
        return {
            "current_mode": row["current_mode"],
            "current_phase": row["current_phase"],
            "rotation_paused": bool(row["rotation_paused"]),
            "pause_reason": row["pause_reason"] or "",
            "current_focus_product_id": row["current_focus_product_id"],
            "current_focus_session_product_id": row["current_focus_session_product_id"],
            "pending_question": _json_loads(row["pending_question_json"], None),
            "awaiting_operator": bool(row["awaiting_operator"]),
            "active_prompt_revision": row["active_prompt_revision"] or "",
            "active_provider": row["active_provider"] or "",
            "active_model": row["active_model"] or "",
            "stream_status": row["stream_status"] or "idle",
        }

    def _voice_profile_from_row(self, row: Any | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "engine": row["engine"] or "fish_speech",
            "profile_type": row["profile_type"] or "quick_clone",
            "reference_wav_path": row["reference_wav_path"] or "",
            "reference_text": row["reference_text"] or "",
            "language": row["language"] or "id",
            "supported_languages": _json_loads(row["supported_languages_json"], [row["language"] or "id"]),
            "quality_tier": row["quality_tier"] or "quick",
            "guidance": _json_loads(row["guidance_json"], {}),
            "notes": row["notes"] or "",
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _voice_lab_state_from_row(self, row: Any | None) -> dict[str, Any]:
        if row is None:
            return {
                "mode": "standalone",
                "active_profile_id": None,
                "preview_session_id": "",
                "selected_avatar_id": "",
                "selected_language": "id",
                "selected_profile_type": "quick_clone",
                "selected_revision_id": None,
                "selected_style_preset": "natural",
                "selected_stability": 0.75,
                "selected_similarity": 0.8,
                "draft_text": "",
                "last_generation_id": None,
            }
        return {
            "mode": row["mode"] or "standalone",
            "active_profile_id": row["active_profile_id"],
            "preview_session_id": row["preview_session_id"] or "",
            "selected_avatar_id": row["selected_avatar_id"] or "",
            "selected_language": row["selected_language"] or "id",
            "selected_profile_type": row["selected_profile_type"] or "quick_clone",
            "selected_revision_id": row["selected_revision_id"],
            "selected_style_preset": row["selected_style_preset"] or "natural",
            "selected_stability": float(row["selected_stability"] or 0.75),
            "selected_similarity": float(row["selected_similarity"] or 0.8),
            "draft_text": row["draft_text"] or "",
            "last_generation_id": row["last_generation_id"],
            "updated_at": row["updated_at"],
        }

    def _voice_generation_from_row(self, row: Any | None) -> dict[str, Any] | None:
        if row is None:
            return None
        generation_id = int(row["id"])
        audio_filename = row["audio_filename"] or Path(row["audio_path"] or "").name
        download_name = row["download_name"] or audio_filename or f"voice-{generation_id}.wav"
        return {
            "id": generation_id,
            "mode": row["mode"],
            "profile_id": row["profile_id"],
            "profile_name": row["profile_name"] if "profile_name" in row.keys() else None,
            "source_type": row["source_type"] or "manual_text",
            "input_text": row["input_text"] or "",
            "language": row["language"] or "id",
            "emotion": row["emotion"] or "neutral",
            "style_preset": row["style_preset"] or "natural",
            "stability": float(row["stability"] or 0.75),
            "similarity": float(row["similarity"] or 0.8),
            "speed": float(row["speed"] or 1.0),
            "status": row["status"],
            "audio_path": row["audio_path"] or "",
            "audio_filename": audio_filename,
            "download_name": download_name,
            "audio_url": f"/api/voice/audio/{generation_id}",
            "download_url": f"/api/voice/audio/{generation_id}/download",
            "audio_size_bytes": int(row["audio_size_bytes"] or 0),
            "latency_ms": float(row["latency_ms"] or 0.0),
            "duration_ms": float(row["duration_ms"] or 0.0),
            "attached_to_avatar": bool(row["attached_to_avatar"]),
            "avatar_session_id": row["avatar_session_id"] or "",
            "created_at": row["created_at"],
        }

    def _voice_training_job_from_row(self, row: Any | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {
            "id": row["id"],
            "profile_id": row["profile_id"],
            "profile_name": row["profile_name"] if "profile_name" in row.keys() else None,
            "job_type": row["job_type"] or "studio_voice_training",
            "status": row["status"] or "queued",
            "current_stage": row["current_stage"] or "queued",
            "progress_pct": float(row["progress_pct"] or 0.0),
            "dataset_path": row["dataset_path"] or "",
            "log_path": row["log_path"] or "",
            "meta": _json_loads(row["meta_json"], {}),
            "error_text": row["error_text"] or "",
            "queued_at": row["queued_at"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_products(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        query = """
            SELECT * FROM products
            {where_clause}
            ORDER BY id ASC
        """.format(where_clause="" if include_inactive else "WHERE is_active = 1")
        with self._connection() as conn:
            rows = conn.execute(query).fetchall()
        return [self._product_from_row(row) for row in rows]

    def get_product(self, product_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM products WHERE id = ?",
                (product_id,),
            ).fetchone()
        return self._product_from_row(row) if row else None

    def create_product(
        self,
        name: str,
        price: float,
        category: str = "general",
        stock: int = 0,
        margin_percent: float = 0.0,
        description: str = "",
        image_path: str = "",
        affiliate_links: dict[str, str] | None = None,
        selling_points: list[str] | None = None,
        commission_rate: float = 0.0,
        objection_handling: dict[str, str] | None = None,
        compliance_notes: str = "",
    ) -> dict[str, Any]:
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO products (
                    name, price, image_path, description, stock, category, margin_percent,
                    affiliate_links_json, selling_points_json, commission_rate,
                    objection_handling_json, compliance_notes, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    name,
                    float(price),
                    image_path,
                    description,
                    int(stock),
                    category,
                    float(margin_percent),
                    _json_dumps(affiliate_links or {}),
                    _json_dumps(selling_points or []),
                    float(commission_rate),
                    _json_dumps(objection_handling or {}),
                    compliance_notes,
                ),
            )
            product_id = int(cursor.lastrowid)
        product = self.get_product(product_id)
        self._record_command("product.create", "completed", {"product_id": product_id, "name": name})
        return product or {}

    def update_product(
        self,
        product_id: int,
        *,
        name: str,
        price: float,
        category: str = "general",
        stock: int = 0,
        margin_percent: float = 0.0,
        description: str = "",
        image_path: str = "",
        affiliate_links: dict[str, str] | None = None,
        selling_points: list[str] | None = None,
        commission_rate: float = 0.0,
        objection_handling: dict[str, str] | None = None,
        compliance_notes: str = "",
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE products
                SET name = ?, price = ?, image_path = ?, description = ?, stock = ?,
                    category = ?, margin_percent = ?, affiliate_links_json = ?,
                    selling_points_json = ?, commission_rate = ?,
                    objection_handling_json = ?, compliance_notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
                """,
                (
                    name,
                    float(price),
                    image_path,
                    description,
                    int(stock),
                    category,
                    float(margin_percent),
                    _json_dumps(affiliate_links or {}),
                    _json_dumps(selling_points or []),
                    float(commission_rate),
                    _json_dumps(objection_handling or {}),
                    compliance_notes,
                    product_id,
                ),
            )
        product = self.get_product(product_id)
        if product is None:
            raise RuntimeError(f"Product {product_id} not found")
        self._record_command("product.update", "completed", {"product_id": product_id})
        return product

    def delete_product(self, product_id: int) -> dict[str, Any]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id, name FROM products WHERE id = ? AND is_active = 1",
                (product_id,),
            ).fetchone()
            if row is None:
                raise RuntimeError(f"Product {product_id} not found")
            conn.execute(
                """
                UPDATE products
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (product_id,),
            )
        self._record_command("product.delete", "completed", {"product_id": product_id})
        return {"status": "deleted", "id": product_id, "name": row["name"]}

    def seed_products_if_empty(self, products: list[dict[str, Any]]) -> int:
        with self._connection() as conn:
            count = int(conn.execute("SELECT COUNT(*) FROM products WHERE is_active = 1").fetchone()[0])
        if count > 0:
            return 0
        created = 0
        for product in products:
            self.create_product(
                name=product.get("name", ""),
                price=float(product.get("price", 0.0)),
                category=product.get("category", "general"),
                stock=int(product.get("stock", 0)),
                margin_percent=float(product.get("margin_percent", 0.0)),
                description=product.get("description", ""),
                image_path=product.get("image_path", product.get("image", "")),
                affiliate_links=product.get("affiliate_links", {}),
                selling_points=product.get("selling_points", product.get("features", [])),
                commission_rate=float(product.get("commission_rate", 0.0)),
                objection_handling=product.get("objection_handling", {}),
                compliance_notes=product.get("compliance_notes", ""),
            )
            created += 1
        return created

    def seed_products_from_json_if_empty(self, path: Path) -> int:
        if not path.exists():
            return 0
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return 0
        if not isinstance(payload, list):
            return 0
        return self.seed_products_if_empty(payload)

    def create_stream_target(
        self,
        *,
        platform: str,
        label: str,
        rtmp_url: str,
        stream_key: str,
        enabled: bool = True,
    ) -> dict[str, Any]:
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO stream_targets (
                    platform, label, rtmp_url, stream_key, enabled, is_active,
                    validation_status, validation_checks_json
                )
                VALUES (?, ?, ?, ?, ?, 0, 'unvalidated', '[]')
                """,
                (platform, label, rtmp_url, stream_key, int(enabled)),
            )
            target_id = int(cursor.lastrowid)
        self._record_command("stream_target.create", "completed", {"stream_target_id": target_id})
        return self.get_stream_target(target_id) or {}

    def get_stream_target(self, target_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM stream_targets WHERE id = ?",
                (target_id,),
            ).fetchone()
        return self._stream_target_from_row(row) if row else None

    def get_stream_target_secret(self, target_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM stream_targets WHERE id = ?",
                (target_id,),
            ).fetchone()
        if row is None:
            return None
        payload = self._stream_target_from_row(row)
        payload["stream_key"] = row["stream_key"]
        return payload

    def list_stream_targets(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM stream_targets ORDER BY is_active DESC, id ASC"
            ).fetchall()
        return [self._stream_target_from_row(row) for row in rows]

    def update_stream_target(
        self,
        target_id: int,
        *,
        platform: str,
        label: str,
        rtmp_url: str,
        stream_key: str,
        enabled: bool = True,
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE stream_targets
                SET platform = ?, label = ?, rtmp_url = ?, stream_key = ?, enabled = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (platform, label, rtmp_url, stream_key, int(enabled), target_id),
            )
        self._record_command("stream_target.update", "completed", {"stream_target_id": target_id})
        target = self.get_stream_target(target_id)
        if target is None:
            raise RuntimeError(f"Stream target {target_id} not found")
        return target

    def save_stream_target_validation(
        self,
        target_id: int,
        *,
        status: str,
        checks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE stream_targets
                SET validation_status = ?, validation_checks_json = ?,
                    last_validated_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, _json_dumps(checks), target_id),
            )
        self._record_event("stream_target.validated", {"stream_target_id": target_id, "status": status})
        target = self.get_stream_target(target_id)
        if target is None:
            raise RuntimeError(f"Stream target {target_id} not found")
        return target

    def activate_stream_target(self, target_id: int) -> dict[str, Any]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id FROM stream_targets WHERE id = ? AND enabled = 1",
                (target_id,),
            ).fetchone()
            if row is None:
                raise RuntimeError(f"Stream target {target_id} not found")
            conn.execute("UPDATE stream_targets SET is_active = 0, updated_at = CURRENT_TIMESTAMP")
            conn.execute(
                """
                UPDATE stream_targets
                SET is_active = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (target_id,),
            )
        self._record_command("stream_target.activate", "completed", {"stream_target_id": target_id})
        target = self.get_stream_target(target_id)
        if target is None:
            raise RuntimeError(f"Stream target {target_id} not found")
        return target

    def get_active_stream_target(self, platform: str | None = None) -> dict[str, Any] | None:
        query = "SELECT * FROM stream_targets WHERE is_active = 1"
        params: tuple[Any, ...] = ()
        if platform:
            query += " AND platform = ?"
            params = (platform,)
        query += " ORDER BY id DESC LIMIT 1"
        with self._connection() as conn:
            row = conn.execute(query, params).fetchone()
        return self._stream_target_from_row(row) if row else None

    def start_live_session(self, *, platform: str, stream_target_id: int) -> dict[str, Any]:
        with self._connection() as conn:
            active = conn.execute(
                "SELECT id FROM live_sessions WHERE status = 'active' LIMIT 1"
            ).fetchone()
            if active is not None:
                raise RuntimeError("There is already an active live session")

            target = conn.execute(
                "SELECT id FROM stream_targets WHERE id = ? AND enabled = 1",
                (stream_target_id,),
            ).fetchone()
            if target is None:
                raise RuntimeError(f"Stream target {stream_target_id} not found")

            cursor = conn.execute(
                """
                INSERT INTO live_sessions (platform, status, stream_target_id)
                VALUES (?, 'active', ?)
                """,
                (platform, stream_target_id),
            )
            session_id = int(cursor.lastrowid)
            conn.execute(
                """
                INSERT INTO session_state (
                    session_id, current_mode, current_phase, rotation_paused,
                    pause_reason, stream_status
                )
                VALUES (?, 'ROTATING', 'IDLE', 0, '', 'ready')
                """,
                (session_id,),
            )
        self._record_command("live_session.start", "completed", {"session_id": session_id}, session_id=session_id)
        self._record_event("live_session.started", {"session_id": session_id}, session_id=session_id)
        return self.get_active_live_session()["session"]

    def stop_live_session(self, session_id: int | None = None) -> dict[str, Any]:
        live = self.get_active_live_session()
        session = live["session"]
        if session is None:
            raise RuntimeError("No active live session")
        target_session_id = session_id or session["id"]
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE live_sessions
                SET status = 'stopped', ended_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (target_session_id,),
            )
            conn.execute(
                """
                UPDATE session_state
                SET stream_status = 'stopped', updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (target_session_id,),
            )
        self._record_command("live_session.stop", "completed", {"session_id": target_session_id}, session_id=target_session_id)
        self._record_event("live_session.stopped", {"session_id": target_session_id}, session_id=target_session_id)
        return {"status": "stopped", "session_id": target_session_id}

    def set_session_stream_status(self, *, session_id: int, stream_status: str) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE session_state
                SET stream_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (stream_status, session_id),
            )
        self._record_event(
            "live_session.stream_status",
            {"session_id": session_id, "stream_status": stream_status},
            session_id=session_id,
        )
        return self.get_active_live_session()["state"]

    def add_session_products(self, *, session_id: int, product_ids: list[int]) -> list[dict[str, Any]]:
        if not product_ids:
            return []
        with self._connection() as conn:
            session = conn.execute(
                "SELECT id FROM live_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            if session is None:
                raise RuntimeError(f"Live session {session_id} not found")

            max_queue = int(
                conn.execute(
                    "SELECT COALESCE(MAX(queue_order), 0) FROM session_products WHERE session_id = ?",
                    (session_id,),
                ).fetchone()[0]
            )
            for offset, product_id in enumerate(product_ids, start=1):
                exists = conn.execute(
                    "SELECT id FROM products WHERE id = ? AND is_active = 1",
                    (product_id,),
                ).fetchone()
                if exists is None:
                    raise RuntimeError(f"Product {product_id} not found")
                conn.execute(
                    """
                    INSERT OR IGNORE INTO session_products (
                        session_id, product_id, queue_order, enabled_for_rotation, state, updated_at
                    )
                    VALUES (?, ?, ?, 1, 'ready', CURRENT_TIMESTAMP)
                    """,
                    (session_id, product_id, max_queue + offset),
                )
        self._record_command(
            "live_session.products.add",
            "completed",
            {"session_id": session_id, "product_ids": product_ids},
            session_id=session_id,
        )
        self._record_event(
            "live_session.products_added",
            {"session_id": session_id, "product_ids": product_ids},
            session_id=session_id,
        )
        return self.list_session_products(session_id)

    def list_session_products(self, session_id: int) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    sp.id,
                    sp.session_id,
                    sp.product_id,
                    sp.queue_order,
                    sp.enabled_for_rotation,
                    sp.operator_priority,
                    sp.ai_score,
                    sp.cooldown_until,
                    sp.last_pitched_at,
                    sp.times_pitched,
                    sp.last_question_at,
                    sp.state,
                    p.name,
                    p.price,
                    p.category,
                    p.affiliate_links_json,
                    p.selling_points_json,
                    p.commission_rate,
                    p.objection_handling_json,
                    p.compliance_notes
                FROM session_products sp
                JOIN products p ON p.id = sp.product_id
                WHERE sp.session_id = ?
                ORDER BY sp.queue_order ASC, sp.id ASC
                """,
                (session_id,),
            ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            items.append(
                {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "product_id": row["product_id"],
                    "queue_order": row["queue_order"],
                    "enabled_for_rotation": bool(row["enabled_for_rotation"]),
                    "operator_priority": int(row["operator_priority"] or 0),
                    "ai_score": float(row["ai_score"] or 0.0),
                    "cooldown_until": row["cooldown_until"],
                    "last_pitched_at": row["last_pitched_at"],
                    "times_pitched": int(row["times_pitched"] or 0),
                    "last_question_at": row["last_question_at"],
                    "state": row["state"],
                    "product": {
                        "id": row["product_id"],
                        "name": row["name"],
                        "price": float(row["price"]),
                        "price_formatted": f"Rp {float(row['price']):,.0f}",
                        "category": row["category"] or "general",
                        "affiliate_links": _json_loads(row["affiliate_links_json"], {}),
                        "selling_points": _json_loads(row["selling_points_json"], []),
                        "commission_rate": float(row["commission_rate"] or 0.0),
                        "objection_handling": _json_loads(row["objection_handling_json"], {}),
                        "compliance_notes": row["compliance_notes"] or "",
                    },
                }
            )
        return items

    def set_focus_product(self, *, session_id: int, session_product_id: int, reason: str) -> dict[str, Any]:
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT id, product_id
                FROM session_products
                WHERE id = ? AND session_id = ?
                """,
                (session_product_id, session_id),
            ).fetchone()
            if row is None:
                raise RuntimeError(f"Session product {session_product_id} not found")
            conn.execute(
                """
                UPDATE session_state
                SET current_focus_product_id = ?,
                    current_focus_session_product_id = ?,
                    current_mode = 'ROTATING',
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (row["product_id"], session_product_id, session_id),
            )
        self._record_command(
            "live_session.focus.set",
            "completed",
            {"session_product_id": session_product_id, "reason": reason},
            session_id=session_id,
        )
        self._record_event(
            "live_session.focus_changed",
            {"session_product_id": session_product_id, "product_id": row["product_id"], "reason": reason},
            session_id=session_id,
        )
        return self.get_active_live_session()["state"]

    def pause_rotation(self, *, session_id: int, reason: str, question: str | None = None) -> dict[str, Any]:
        current_mode = "SOFT_PAUSED_FOR_QNA" if question else "MANUAL_PAUSED"
        pending_question = {"text": question, "reason": reason} if question else None
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE session_state
                SET rotation_paused = 1,
                    pause_reason = ?,
                    current_mode = ?,
                    pending_question_json = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (reason, current_mode, _json_dumps(pending_question) if pending_question else None, session_id),
            )
        self._record_command(
            "live_session.pause",
            "completed",
            {"reason": reason, "question": question},
            session_id=session_id,
        )
        self._record_event(
            "live_session.paused",
            {"reason": reason, "question": question},
            session_id=session_id,
        )
        return self.get_active_live_session()["state"]

    def update_pending_question(self, *, session_id: int, pending_question: dict[str, Any] | None) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE session_state
                SET pending_question_json = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (_json_dumps(pending_question) if pending_question else None, session_id),
            )
        self._record_event(
            "live_session.pending_question_updated",
            {"pending_question": pending_question or {}},
            session_id=session_id,
        )
        return self.get_active_live_session()["state"]

    def resume_rotation(self, *, session_id: int) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE session_state
                SET rotation_paused = 0,
                    pause_reason = '',
                    current_mode = 'ROTATING',
                    pending_question_json = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (session_id,),
            )
        self._record_command("live_session.resume", "completed", session_id=session_id)
        self._record_event("live_session.resumed", session_id=session_id)
        return self.get_active_live_session()["state"]

    def get_active_live_session(self) -> dict[str, Any]:
        with self._connection() as conn:
            session_row = conn.execute(
                """
                SELECT *
                FROM live_sessions
                WHERE status = 'active'
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
            if session_row is None:
                return {"session": None, "stream_target": None, "state": None, "products": []}

            state_row = conn.execute(
                "SELECT * FROM session_state WHERE session_id = ?",
                (session_row["id"],),
            ).fetchone()
            target_row = conn.execute(
                "SELECT * FROM stream_targets WHERE id = ?",
                (session_row["stream_target_id"],),
            ).fetchone()

        return {
            "session": self._session_row_to_payload(session_row),
            "stream_target": self._stream_target_from_row(target_row) if target_row else None,
            "state": self._session_state_from_row(state_row),
            "products": self.list_session_products(session_row["id"]),
        }

    def get_operator_command_count(self, session_id: int | None = None) -> int:
        query = "SELECT COUNT(*) FROM operator_commands"
        params: tuple[Any, ...] = ()
        if session_id is not None:
            query += " WHERE session_id = ?"
            params = (session_id,)
        with self._connection() as conn:
            return int(conn.execute(query, params).fetchone()[0])

    def get_runtime_event_count(self, session_id: int | None = None) -> int:
        query = "SELECT COUNT(*) FROM runtime_events"
        params: tuple[Any, ...] = ()
        if session_id is not None:
            query += " WHERE session_id = ?"
            params = (session_id,)
        with self._connection() as conn:
            return int(conn.execute(query, params).fetchone()[0])

    def list_voice_profiles(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM voice_profiles ORDER BY is_active DESC, id ASC"
            ).fetchall()
        return [self._voice_profile_from_row(row) or {} for row in rows]

    def get_voice_profile(self, profile_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM voice_profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()
        return self._voice_profile_from_row(row)

    def create_voice_profile(
        self,
        *,
        name: str,
        reference_wav_path: str,
        reference_text: str,
        language: str = "id",
        notes: str = "",
        engine: str = "fish_speech",
        profile_type: str = "quick_clone",
        supported_languages: list[str] | None = None,
        quality_tier: str = "quick",
        guidance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resolved_languages = supported_languages or [language or "id"]
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO voice_profiles (
                    name, engine, profile_type, reference_wav_path, reference_text, language,
                    supported_languages_json, quality_tier, guidance_json, notes, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    name,
                    engine,
                    profile_type,
                    reference_wav_path,
                    reference_text,
                    language,
                    _json_dumps(resolved_languages),
                    quality_tier,
                    _json_dumps(guidance or {}),
                    notes,
                ),
            )
            profile_id = int(cursor.lastrowid)
        self._record_command("voice.profile.create", "completed", {"profile_id": profile_id, "name": name})
        return self.get_voice_profile(profile_id) or {}

    def update_voice_profile(
        self,
        profile_id: int,
        *,
        name: str,
        reference_wav_path: str,
        reference_text: str,
        language: str = "id",
        notes: str = "",
        engine: str = "fish_speech",
        profile_type: str = "quick_clone",
        supported_languages: list[str] | None = None,
        quality_tier: str = "quick",
        guidance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resolved_languages = supported_languages or [language or "id"]
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE voice_profiles
                SET name = ?, engine = ?, profile_type = ?, reference_wav_path = ?, reference_text = ?,
                    language = ?, supported_languages_json = ?, quality_tier = ?, guidance_json = ?,
                    notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    name,
                    engine,
                    profile_type,
                    reference_wav_path,
                    reference_text,
                    language,
                    _json_dumps(resolved_languages),
                    quality_tier,
                    _json_dumps(guidance or {}),
                    notes,
                    profile_id,
                ),
            )
        profile = self.get_voice_profile(profile_id)
        if profile is None:
            raise RuntimeError(f"Voice profile {profile_id} not found")
        self._record_command("voice.profile.update", "completed", {"profile_id": profile_id})
        return profile

    def delete_voice_profile(self, profile_id: int) -> dict[str, Any]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id, name FROM voice_profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()
            if row is None:
                raise RuntimeError(f"Voice profile {profile_id} not found")
            conn.execute(
                """
                UPDATE voice_lab_state
                SET active_profile_id = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE active_profile_id = ?
                """,
                (profile_id,),
            )
            conn.execute("DELETE FROM voice_profiles WHERE id = ?", (profile_id,))
        self._record_command("voice.profile.delete", "completed", {"profile_id": profile_id})
        return {"status": "deleted", "id": profile_id, "name": row["name"]}

    def activate_voice_profile(self, profile_id: int) -> dict[str, Any]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id FROM voice_profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()
            if row is None:
                raise RuntimeError(f"Voice profile {profile_id} not found")
            conn.execute("UPDATE voice_profiles SET is_active = 0, updated_at = CURRENT_TIMESTAMP")
            conn.execute(
                """
                UPDATE voice_profiles
                SET is_active = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (profile_id,),
            )
            conn.execute(
                """
                INSERT INTO voice_lab_state (id, active_profile_id, updated_at)
                VALUES (1, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    active_profile_id = excluded.active_profile_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (profile_id,),
            )
        self._record_command("voice.profile.activate", "completed", {"profile_id": profile_id})
        profile = self.get_voice_profile(profile_id)
        if profile is None:
            raise RuntimeError(f"Voice profile {profile_id} not found")
        return profile

    def get_voice_lab_state(self) -> dict[str, Any]:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM voice_lab_state WHERE id = 1").fetchone()
        return self._voice_lab_state_from_row(row)

    def update_voice_lab_state(
        self,
        *,
        mode: str,
        active_profile_id: int | None = None,
        preview_session_id: str = "",
        selected_avatar_id: str = "",
        selected_language: str = "id",
        selected_profile_type: str = "quick_clone",
        selected_revision_id: int | None = None,
        selected_style_preset: str = "natural",
        selected_stability: float = 0.75,
        selected_similarity: float = 0.8,
        draft_text: str = "",
        last_generation_id: int | None = None,
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO voice_lab_state (
                    id, mode, active_profile_id, preview_session_id,
                    selected_avatar_id, selected_language, selected_profile_type,
                    selected_revision_id, selected_style_preset, selected_stability,
                    selected_similarity, draft_text, last_generation_id, updated_at
                )
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    mode = excluded.mode,
                    active_profile_id = excluded.active_profile_id,
                    preview_session_id = excluded.preview_session_id,
                    selected_avatar_id = excluded.selected_avatar_id,
                    selected_language = excluded.selected_language,
                    selected_profile_type = excluded.selected_profile_type,
                    selected_revision_id = excluded.selected_revision_id,
                    selected_style_preset = excluded.selected_style_preset,
                    selected_stability = excluded.selected_stability,
                    selected_similarity = excluded.selected_similarity,
                    draft_text = excluded.draft_text,
                    last_generation_id = excluded.last_generation_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    mode,
                    active_profile_id,
                    preview_session_id,
                    selected_avatar_id,
                    selected_language,
                    selected_profile_type,
                    selected_revision_id,
                    selected_style_preset,
                    float(selected_stability),
                    float(selected_similarity),
                    draft_text,
                    last_generation_id,
                ),
            )
        self._record_command(
            "voice.lab.update",
            "completed",
            {
                "mode": mode,
                "active_profile_id": active_profile_id,
                "preview_session_id": preview_session_id,
                "selected_avatar_id": selected_avatar_id,
                "selected_language": selected_language,
                "selected_profile_type": selected_profile_type,
            },
        )
        return self.get_voice_lab_state()

    def create_voice_generation(
        self,
        *,
        mode: str,
        profile_id: int | None,
        source_type: str,
        input_text: str,
        emotion: str,
        speed: float,
        status: str,
        audio_path: str,
        audio_size_bytes: int,
        latency_ms: float,
        duration_ms: float,
        attached_to_avatar: bool,
        avatar_session_id: str = "",
        language: str = "id",
        style_preset: str = "natural",
        stability: float = 0.75,
        similarity: float = 0.8,
        audio_filename: str = "",
        download_name: str = "",
    ) -> dict[str, Any]:
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO voice_generations (
                    mode, profile_id, source_type, input_text, language, emotion, style_preset,
                    stability, similarity, speed, status, audio_path, audio_filename, download_name,
                    audio_size_bytes, latency_ms, duration_ms,
                    attached_to_avatar, avatar_session_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mode,
                    profile_id,
                    source_type,
                    input_text,
                    language,
                    emotion,
                    style_preset,
                    float(stability),
                    float(similarity),
                    float(speed),
                    status,
                    audio_path,
                    audio_filename,
                    download_name,
                    int(audio_size_bytes),
                    float(latency_ms),
                    float(duration_ms),
                    int(attached_to_avatar),
                    avatar_session_id,
                ),
            )
            generation_id = int(cursor.lastrowid)
        self._record_command(
            "voice.generation.create",
            "completed",
            {
                "generation_id": generation_id,
                "mode": mode,
                "profile_id": profile_id,
                "status": status,
                "language": language,
                "attached_to_avatar": attached_to_avatar,
            },
        )
        return self.get_voice_generation(generation_id) or {}

    def create_voice_training_job(
        self,
        *,
        profile_id: int,
        job_type: str,
        status: str,
        current_stage: str,
        progress_pct: float,
        dataset_path: str = "",
        log_path: str = "",
        meta: dict[str, Any] | None = None,
        error_text: str = "",
    ) -> dict[str, Any]:
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO voice_training_jobs (
                    profile_id, job_type, status, current_stage, progress_pct,
                    dataset_path, log_path, meta_json, error_text, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    profile_id,
                    job_type,
                    status,
                    current_stage,
                    float(progress_pct),
                    dataset_path,
                    log_path,
                    _json_dumps(meta or {}),
                    error_text,
                ),
            )
            job_id = int(cursor.lastrowid)
        self._record_command(
            "voice.training_job.create",
            "completed",
            {"job_id": job_id, "profile_id": profile_id, "job_type": job_type, "status": status},
        )
        return self.get_voice_training_job(job_id) or {}

    def list_voice_training_jobs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    vtj.*,
                    vp.name AS profile_name
                FROM voice_training_jobs vtj
                LEFT JOIN voice_profiles vp ON vp.id = vtj.profile_id
                ORDER BY vtj.id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [self._voice_training_job_from_row(row) or {} for row in rows]

    def get_voice_training_job(self, job_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT
                    vtj.*,
                    vp.name AS profile_name
                FROM voice_training_jobs vtj
                LEFT JOIN voice_profiles vp ON vp.id = vtj.profile_id
                WHERE vtj.id = ?
                """,
                (job_id,),
            ).fetchone()
        return self._voice_training_job_from_row(row)

    def list_voice_generations(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    vg.*,
                    vp.name AS profile_name
                FROM voice_generations vg
                LEFT JOIN voice_profiles vp ON vp.id = vg.profile_id
                ORDER BY vg.id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [self._voice_generation_from_row(row) or {} for row in rows]

    def get_voice_generation(self, generation_id: int) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT
                    vg.*,
                    vp.name AS profile_name
                FROM voice_generations vg
                LEFT JOIN voice_profiles vp ON vp.id = vg.profile_id
                WHERE vg.id = ?
                """,
                (generation_id,),
            ).fetchone()
        return self._voice_generation_from_row(row)
