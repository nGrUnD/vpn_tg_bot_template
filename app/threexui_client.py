from __future__ import annotations

import base64
import binascii
import json
import logging
import secrets
import string
import time
import urllib.parse
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from app.config import ThreeXUIConfig

logger = logging.getLogger(__name__)

DEFAULT_IP_LIMIT = 3


@dataclass
class ThreeXUIClientInfo:
    client_id: str
    config_text: str
    remark: Optional[str] = None
    server_label: Optional[str] = None
    sub_id: Optional[str] = None
    subscription_url: Optional[str] = None
    subscription_json_url: Optional[str] = None
    client_email: Optional[str] = None
    provisioned_inbound_ids: list[int] = field(default_factory=list)
    failed_inbounds: list[tuple[int, str]] = field(default_factory=list)


class ThreeXUIClient:
    def __init__(self, config: ThreeXUIConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient(base_url=config.base_url, timeout=30.0)
        self._auth_cookies: dict[str, str] = {}
        self._use_new_clients_api: bool | None = None

    async def _ensure_login(self) -> None:
        if self._auth_cookies:
            return
        response = await self._client.post(
            "/login",
            data={
                "username": self._config.username,
                "password": self._config.password,
            },
        )
        response.raise_for_status()
        self._auth_cookies = dict(response.cookies)

    def _generate_sub_id(self, length: int = 16) -> str:
        alphabet = string.ascii_lowercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(max(length, 8)))

    def _join_url_with_id(self, base: str, item_id: str) -> str:
        return base if not item_id else (base if base.endswith("/") else base + "/") + item_id

    async def _fetch_panel_settings(self) -> dict[str, Any]:
        await self._ensure_login()
        response = await self._client.post("/panel/setting/all", cookies=self._auth_cookies)
        response.raise_for_status()
        payload = self._extract_payload(response.json())
        return payload if isinstance(payload, dict) else {}

    def _build_subscription_urls(self, settings: dict[str, Any], sub_id: str) -> tuple[str | None, str | None]:
        if not sub_id:
            return None, None
        sub_uri = str(settings.get("subURI") or "").strip()
        sub_json_uri = str(settings.get("subJsonURI") or "").strip()
        if not sub_uri or not sub_json_uri:
            parsed = urllib.parse.urlparse(self._config.base_url or "")
            base = ""
            if parsed.scheme and parsed.netloc:
                base = f"{parsed.scheme}://{parsed.netloc}"
            sub_path = str(settings.get("subPath") or "/sub/").strip() or "/sub/"
            sub_json_path = str(settings.get("subJsonPath") or "/json/").strip() or "/json/"
            if not sub_path.startswith("/"):
                sub_path = "/" + sub_path
            if not sub_json_path.startswith("/"):
                sub_json_path = "/" + sub_json_path
            if base:
                if not sub_uri:
                    sub_uri = base + sub_path
                if not sub_json_uri:
                    sub_json_uri = base + sub_json_path
        subscription_url = self._join_url_with_id(sub_uri, sub_id) if sub_uri else None
        subscription_json_url = self._join_url_with_id(sub_json_uri, sub_id) if sub_json_uri else None
        return subscription_url, subscription_json_url

    def _decode_subscription_body(self, payload: str) -> list[str]:
        text = (payload or "").strip()
        if not text:
            return []
        raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
        if any(line.startswith(("vless://", "vmess://", "trojan://", "ss://")) for line in raw_lines):
            return raw_lines
        try:
            padding = "=" * (-len(text) % 4)
            decoded = base64.b64decode(text + padding).decode("utf-8", errors="ignore")
        except (binascii.Error, ValueError):
            return raw_lines
        return [line.strip() for line in decoded.splitlines() if line.strip()]

    def _apply_display_name_to_config(self, config_text: str | None, display_name: str) -> str | None:
        text = (config_text or "").strip()
        if not text or not display_name:
            return config_text
        if not text.startswith(("vless://", "trojan://", "ss://")):
            return config_text
        try:
            split = urllib.parse.urlsplit(text)
            return urllib.parse.urlunsplit(
                (
                    split.scheme,
                    split.netloc,
                    split.path,
                    split.query,
                    urllib.parse.quote(display_name, safe=""),
                )
            )
        except Exception:
            base = text.split("#", 1)[0]
            return base + "#" + urllib.parse.quote(display_name, safe="")

    async def _fetch_config_from_subscription(self, subscription_url: str | None) -> str | None:
        if not subscription_url:
            return None
        try:
            response = await self._client.get(
                subscription_url,
                headers={"Accept": "text/plain, */*"},
                follow_redirects=True,
            )
            response.raise_for_status()
        except Exception:
            return None
        lines = self._decode_subscription_body(response.text)
        return lines[0] if lines else None

    async def list_inbound_ids(self, *, only_enabled: bool = True) -> list[int]:
        await self._ensure_login()
        response = await self._client.get("/panel/api/inbounds/list", cookies=self._auth_cookies)
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            return []
        obj = data.get("obj") or data.get("data") or []
        if not isinstance(obj, list):
            return []
        ids: list[int] = []
        for item in obj:
            if not isinstance(item, dict):
                continue
            if only_enabled and item.get("enable") is False:
                continue
            try:
                iid = int(item["id"])
                if iid > 0:
                    ids.append(iid)
            except (KeyError, TypeError, ValueError):
                continue
        return ids


    def _mark_legacy_client_api(self) -> None:
        self._use_new_clients_api = False

    async def _probe_new_client_api(self) -> bool:
        if self._use_new_clients_api is not None:
            return self._use_new_clients_api
        await self._ensure_login()
        try:
            resp = await self._client.get(
                "/panel/api/clients/list",
                cookies=self._auth_cookies,
            )
            resp.raise_for_status()
            body = resp.json()
            is_new = isinstance(body, dict) and body.get("success") is not False
        except Exception:
            is_new = False
        self._use_new_clients_api = is_new
        if is_new:
            logger.info("3x-ui: API clients/* (единый клиент на несколько inbound)")
        return is_new

    async def _resolve_target_inbound_ids(self) -> list[int]:
        configured = getattr(self._config, "inbound_ids", None)
        if configured:
            return [int(i) for i in configured if int(i) > 0]
        ids = await self.list_inbound_ids(only_enabled=True)
        if ids:
            return ids
        return [self._config.inbound_id]

    @staticmethod
    def client_email_for_telegram(telegram_id: int, *, label: str = "trial") -> str:
        return f"tg_{telegram_id}_{label}"

    def _build_client_payload(
        self,
        *,
        telegram_id: int,
        client_uuid: str,
        client_email: str,
        sub_id: str,
        expiry_ts_ms: int,
        total_bytes: int,
        limit_ip: int,
    ) -> dict[str, Any]:
        return {
            "id": client_uuid,
            "security": "auto",
            "password": "",
            "flow": "",
            "email": client_email,
            "limitIp": max(int(limit_ip), 0),
            "totalGB": max(int(total_bytes), 0),
            "expiryTime": int(expiry_ts_ms),
            "enable": True,
            "tgId": int(telegram_id),
            "subId": sub_id,
            "comment": client_email,
            "reset": 0,
        }

    @staticmethod
    def _api_success(body: Any) -> bool:
        return not (isinstance(body, dict) and body.get("success") is False)

    @staticmethod
    def _api_error_message(body: Any, fallback: str = "success=false") -> str:
        if isinstance(body, dict):
            return str(body.get("msg") or body.get("message") or fallback).strip()
        return fallback

    async def _create_client_via_clients_add(
        self,
        client_obj: dict[str, Any],
        inbound_ids: list[int],
    ) -> tuple[list[int], list[tuple[int, str]]]:
        resp = await self._client.post(
            "/panel/api/clients/add",
            json={"client": client_obj, "inboundIds": inbound_ids},
            cookies=self._auth_cookies,
        )
        if resp.status_code == 404:
            self._mark_legacy_client_api()
            raise RuntimeError("clients/add not found")
        resp.raise_for_status()
        body = resp.json()
        if not self._api_success(body):
            raise RuntimeError(self._api_error_message(body, "clients/add failed"))
        return inbound_ids, []

    async def _create_client_via_add_client_inbounds(
        self,
        client_obj: dict[str, Any],
        inbound_ids: list[int],
    ) -> tuple[list[int], list[tuple[int, str]]] | None:
        settings_str = json.dumps({"clients": [client_obj]}, ensure_ascii=False, separators=(",", ":"))
        try:
            resp = await self._client.post(
                "/panel/api/inbounds/addClientInbounds",
                json={"settings": settings_str, "inboundIds": inbound_ids},
                cookies=self._auth_cookies,
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            body = resp.json()
            if not self._api_success(body):
                raise RuntimeError(self._api_error_message(body, "addClientInbounds failed"))
            return inbound_ids, []
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise

    async def _create_client_via_legacy_per_inbound(
        self,
        *,
        telegram_id: int,
        client_uuid: str,
        sub_id: str,
        expiry_ts_ms: int,
        total_bytes: int,
        limit_ip: int,
        inbound_ids: list[int],
        logical_label: str,
    ) -> tuple[list[int], list[tuple[int, str]]]:
        """Старые панели: отдельный email на каждый inbound."""
        sub_tag = sub_id[:16] if len(sub_id) >= 8 else sub_id
        tb = max(int(total_bytes), 0)
        ok: list[int] = []
        failed: list[tuple[int, str]] = []
        for iid in inbound_ids:
            inbound_email = f"tg_{telegram_id}_i{iid}_{sub_tag}"
            client_obj = self._build_client_payload(
                telegram_id=telegram_id,
                client_uuid=client_uuid,
                client_email=inbound_email,
                sub_id=sub_id,
                expiry_ts_ms=expiry_ts_ms,
                total_bytes=tb,
                limit_ip=limit_ip,
            )
            client_obj["comment"] = logical_label
            settings_str = json.dumps({"clients": [client_obj]}, ensure_ascii=False, separators=(",", ":"))
            try:
                resp = await self._client.post(
                    "/panel/api/inbounds/addClient",
                    json={"id": iid, "settings": settings_str},
                    cookies=self._auth_cookies,
                )
                resp.raise_for_status()
                body = resp.json()
                if not self._api_success(body):
                    msg = self._api_error_message(body)
                    failed.append((iid, msg))
                    logger.warning("3x-ui addClient inbound=%s: %s", iid, msg)
                else:
                    ok.append(iid)
            except Exception as exc:
                failed.append((iid, str(exc)))
                logger.exception("3x-ui addClient inbound=%s failed", iid)
        return ok, failed

    async def _get_client_traffics_by_email(self, email: str) -> dict[str, Any] | None:
        safe_email = urllib.parse.quote(email, safe="")
        for path in (
            f"/panel/api/clients/traffic/{safe_email}",
            f"/panel/api/inbounds/getClientTraffics/{safe_email}",
        ):
            try:
                resp = await self._client.get(path, cookies=self._auth_cookies)
                if resp.status_code == 404:
                    continue
                resp.raise_for_status()
                body = resp.json()
                if isinstance(body, dict) and body.get("obj") is not None:
                    obj = body["obj"]
                    return obj if isinstance(obj, dict) else None
                if isinstance(body, dict) and body.get("email"):
                    return body
            except Exception:
                logger.debug("get client traffic %s via %s failed", email, path, exc_info=True)
        return None

    async def _delete_client_by_email(self, client_email: str) -> bool:
        safe_email = urllib.parse.quote(client_email, safe="")
        try:
            resp = await self._client.post(
                f"/panel/api/clients/del/{safe_email}",
                cookies=self._auth_cookies,
            )
            if resp.status_code == 404:
                self._mark_legacy_client_api()
                return False
            resp.raise_for_status()
            body = resp.json()
            if isinstance(body, dict) and body.get("success") is False:
                msg = self._api_error_message(body).lower()
                if "not found" in msg or "не найден" in msg:
                    return True
                logger.info("3x-ui clients/del %s: %s", client_email, msg)
            return True
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                self._mark_legacy_client_api()
                return False
            raise


    async def create_client_all_inbounds(
        self,
        telegram_id: int,
        *,
        expiry_ts_ms: int,
        total_bytes: int,
        limit_ip: int = DEFAULT_IP_LIMIT,
        client_label: str = "trial",
    ) -> ThreeXUIClientInfo:
        """
        Один клиент (UUID, email, subId) на несколько inbound одной панели.
        На панелях 3x-ui v3.1.0+ — POST /panel/api/clients/add с inboundIds.
        """
        await self._ensure_login()

        inbound_ids = await self._resolve_target_inbound_ids()
        client_uuid = str(uuid.uuid4())
        sub_id = self._generate_sub_id()
        client_email = self.client_email_for_telegram(telegram_id, label=client_label)
        logical_label = client_email
        client_obj = self._build_client_payload(
            telegram_id=telegram_id,
            client_uuid=client_uuid,
            client_email=client_email,
            sub_id=sub_id,
            expiry_ts_ms=expiry_ts_ms,
            total_bytes=total_bytes,
            limit_ip=limit_ip,
        )

        ok: list[int] = []
        failed: list[tuple[int, str]] = []
        if await self._probe_new_client_api():
            try:
                ok, failed = await self._create_client_via_clients_add(client_obj, inbound_ids)
            except RuntimeError as exc:
                if "not found" in str(exc).lower():
                    ok, failed = [], [(0, str(exc))]
                else:
                    raise
        if not ok:
            created = await self._create_client_via_add_client_inbounds(client_obj, inbound_ids)
            if created is not None:
                ok, failed = created
        if not ok:
            ok, failed = await self._create_client_via_legacy_per_inbound(
                telegram_id=telegram_id,
                client_uuid=client_uuid,
                sub_id=sub_id,
                expiry_ts_ms=expiry_ts_ms,
                total_bytes=total_bytes,
                limit_ip=limit_ip,
                inbound_ids=inbound_ids,
                logical_label=logical_label,
            )

        if not ok:
            err = failed[0][1] if failed else "no inbounds"
            raise RuntimeError(f"Не удалось добавить клиента ни в один inbound: {err}")

        subscription_url = None
        subscription_json_url = None
        try:
            panel_settings = await self._fetch_panel_settings()
            subscription_url, subscription_json_url = self._build_subscription_urls(panel_settings, sub_id)
        except Exception:
            subscription_url = None
            subscription_json_url = None

        link_inbound = ok[0]
        config_text = await self._fetch_config_from_subscription(subscription_url)
        if not config_text:
            config_text = await self._build_client_link_from_inbound(
                inbound_id=link_inbound,
                client_uuid=client_uuid,
                client_email=client_email,
            )
        if not config_text:
            server = self._config.vless_server
            port = self._config.vless_port
            if server and port is not None:
                config_text = f"vless://{client_uuid}@{server}:{port}#{logical_label}"
            else:
                config_text = f"Подписка: {logical_label} (панель 3x-ui)"
        config_text = self._apply_display_name_to_config(config_text, logical_label) or config_text

        return ThreeXUIClientInfo(
            client_id=client_uuid,
            config_text=config_text,
            remark=logical_label,
            sub_id=sub_id,
            client_email=client_email,
            subscription_url=subscription_url,
            subscription_json_url=subscription_json_url,
            provisioned_inbound_ids=ok,
            failed_inbounds=failed,
        )
    async def create_trial_client_all_inbounds(
        self,
        telegram_id: int,
        expire_days: int,
        *,
        total_gb: int = 0,
        limit_ip: int = DEFAULT_IP_LIMIT,
    ) -> ThreeXUIClientInfo:
        """
        Один логический trial: один и тот же Xray client id (UUID) и один subId на всех inbounds,
        чтобы одна ссылка подписки тянула все узлы.

        Один email и один subId на все inbound (DE, NL и др.) через API clients/add.
        """
        expiry_ts_ms = int((time.time() + expire_days * 24 * 60 * 60) * 1000)
        total_bytes = 0 if total_gb <= 0 else int(total_gb) * (1024**3)
        return await self.create_client_all_inbounds(
            telegram_id,
            expiry_ts_ms=expiry_ts_ms,
            total_bytes=total_bytes,
            limit_ip=limit_ip,
        )

    async def delete_client_uuid_from_all_inbounds(
        self,
        client_uuid: str,
        *,
        client_email: str | None = None,
    ) -> None:
        """Удалить клиента с панели (v3.1.0+ — по email, иначе по UUID в каждом inbound)."""
        cu = str(client_uuid).strip()
        email = str(client_email or "").strip()
        if not cu and not email:
            return
        await self._ensure_login()
        if email and await self._probe_new_client_api():
            if await self._delete_client_by_email(email):
                return
        if not cu:
            return
        ids = await self._resolve_target_inbound_ids()
        safe_id = urllib.parse.quote(cu, safe="-_")
        for iid in ids:
            try:
                resp = await self._client.post(
                    f"/panel/api/inbounds/{int(iid)}/delClient/{safe_id}",
                    cookies=self._auth_cookies,
                )
                resp.raise_for_status()
                body = resp.json()
                if isinstance(body, dict) and body.get("success") is False:
                    logger.info(
                        "3x-ui delClient inbound=%s: %s",
                        iid,
                        str(body.get("msg") or body.get("message") or "").strip(),
                    )
            except Exception:
                logger.debug("3x-ui delClient inbound=%s пропущен", iid, exc_info=True)
    async def collect_client_quota_snapshot(
        self,
        client_uuid: str,
        *,
        client_email: str | None = None,
    ) -> Optional[tuple[int, int, int]]:
        """
        (expiry_ts_ms, limit_total_bytes, used_bytes) или None.
        На новых панелях — трафик по email; иначе поиск UUID по inbound.
        """
        cu = str(client_uuid).strip().lower()
        email = str(client_email or "").strip()
        await self._ensure_login()
        if email and await self._probe_new_client_api():
            traffic = await self._get_client_traffics_by_email(email)
            if traffic:
                up = int(traffic.get("up") or 0)
                down = int(traffic.get("down") or 0)
                total = int(traffic.get("total") or 0)
                used = total if total > 0 else up + down
                exp_ms = int(traffic.get("expiryTime") or 0)
                limit_b = int(traffic.get("totalGB") or traffic.get("totalGb") or 0)
                return (exp_ms, limit_b, used)
        if not cu:
            return None
        ids = await self._resolve_target_inbound_ids()
        exp_ms = 0
        limit_b = 0
        used_max = 0
        found = False
        for iid in ids:
            try:
                obj = await self._get_inbound(iid)
                if not obj:
                    continue
                for c in self._extract_clients(obj):
                    if str(c.get("id") or "").strip().lower() != cu:
                        continue
                    found = True
                    tb = int(c.get("totalGB") or 0)
                    if tb > 0:
                        limit_b = max(limit_b, tb)
                    up = int(c.get("up") or 0)
                    down = int(c.get("down") or 0)
                    tot = int(c.get("total") or 0)
                    used = int(tot) if tot > 0 else up + down
                    used_max = max(used_max, used)
                    exp_ms = max(exp_ms, int(c.get("expiryTime") or 0))
            except Exception:
                logger.debug("collect quota inbound=%s", iid, exc_info=True)
                continue
        if not found:
            return None
        return (exp_ms, limit_b, used_max)
    async def _get_inbound(self, inbound_id: int) -> Optional[dict[str, Any]]:
        await self._ensure_login()
        for path in (f"/panel/api/inbounds/get/{inbound_id}", f"/panel/api/inbound/get/{inbound_id}"):
            try:
                resp = await self._client.get(path, cookies=self._auth_cookies)
                resp.raise_for_status()
                data = resp.json()
                if not data.get("success"):
                    continue
                obj = data.get("obj") or data.get("data")
                if obj:
                    return obj
            except Exception:
                continue
        return None

    def _extract_clients(self, inbound_obj: dict[str, Any]) -> list[dict[str, Any]]:
        settings_raw = inbound_obj.get("settings") or "{}"
        settings = json.loads(settings_raw) if isinstance(settings_raw, str) else (settings_raw or {})
        clients = settings.get("clients") or []
        return clients if isinstance(clients, list) else []

    def _extract_payload(self, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("obj") is not None:
                return data.get("obj")
            if data.get("data") is not None:
                return data.get("data")
        return data

    def _get_nested(self, d: dict, *keys: str) -> Any:
        for k in keys:
            if k in d and d[k] is not None:
                return d[k]
        return None

    def _build_vless_from_inbound(
        self,
        obj: dict[str, Any],
        client_uuid: str,
        client_email: str,
        client_flow: str = "",
    ) -> Optional[str]:
        try:
            listen = (obj.get("listen") or obj.get("Listen") or "").strip()
            port = self._get_nested(obj, "port", "Port")
            if port is None:
                return None
            port = int(port) if isinstance(port, (int, float)) else None
            if port is None:
                return None
            client_port = self._config.vless_port
            if client_port is not None:
                port = int(client_port)
            client_host = self._config.vless_server
            if client_host:
                host = client_host
            else:
                host = listen if listen and listen not in ("0.0.0.0", "::") else None
                if not host:
                    parsed = urllib.parse.urlparse(self._config.base_url or "")
                    host = parsed.hostname or "localhost"
            stream_raw = self._get_nested(obj, "streamSettings", "stream_settings") or "{}"
            if isinstance(stream_raw, str):
                stream = json.loads(stream_raw) if stream_raw.strip() else {}
            else:
                stream = stream_raw or {}
            network = self._get_nested(stream, "network", "Network") or "tcp"
            security = self._get_nested(stream, "security", "Security") or "none"
            params = ["type=" + str(network), "encryption=none"]
            tcp = self._get_nested(stream, "tcpSettings", "tcp_settings") or {}
            if isinstance(tcp, str):
                tcp = json.loads(tcp) if tcp.strip() else {}
            ws = self._get_nested(stream, "wsSettings", "ws_settings") or {}
            if isinstance(ws, str):
                ws = json.loads(ws) if ws.strip() else {}
            grpc = self._get_nested(stream, "grpcSettings", "grpc_settings") or {}
            if isinstance(grpc, str):
                grpc = json.loads(grpc) if grpc.strip() else {}
            httpupgrade = self._get_nested(stream, "httpupgradeSettings", "httpupgrade_settings") or {}
            if isinstance(httpupgrade, str):
                httpupgrade = json.loads(httpupgrade) if httpupgrade.strip() else {}
            xhttp = self._get_nested(stream, "xhttpSettings", "xhttp_settings") or {}
            if isinstance(xhttp, str):
                xhttp = json.loads(xhttp) if xhttp.strip() else {}

            if network == "tcp":
                header = self._get_nested(tcp, "header", "Header") or {}
                request = self._get_nested(header, "request", "Request") or {}
                header_type = self._get_nested(header, "type", "Type")
                if header_type == "http":
                    path_list = request.get("path") or []
                    if isinstance(path_list, list) and path_list:
                        params.append("path=" + urllib.parse.quote(",".join(str(x) for x in path_list), safe=""))
                    headers = request.get("headers") or {}
                    h = headers.get("Host") or headers.get("host") or ""
                    if isinstance(h, list):
                        h = ",".join(str(x) for x in h if x)
                    if h:
                        params.append("host=" + urllib.parse.quote(str(h), safe=""))
                    params.append("headerType=http")
            elif network == "ws":
                path = ws.get("path") or ""
                host_header = ws.get("host") or ws.get("Host") or ""
                if path:
                    params.append("path=" + urllib.parse.quote(str(path), safe="/,"))
                if host_header:
                    params.append("host=" + urllib.parse.quote(str(host_header), safe=",:"))
            elif network == "grpc":
                service_name = grpc.get("serviceName") or grpc.get("service_name") or ""
                authority = grpc.get("authority") or ""
                if service_name:
                    params.append("serviceName=" + urllib.parse.quote(str(service_name), safe=""))
                if authority:
                    params.append("authority=" + urllib.parse.quote(str(authority), safe=""))
                if grpc.get("multiMode") or grpc.get("multi_mode"):
                    params.append("mode=multi")
            elif network == "httpupgrade":
                path = httpupgrade.get("path") or ""
                host_header = httpupgrade.get("host") or httpupgrade.get("Host") or ""
                if path:
                    params.append("path=" + urllib.parse.quote(str(path), safe="/,"))
                if host_header:
                    params.append("host=" + urllib.parse.quote(str(host_header), safe=",:"))
            elif network == "xhttp":
                path = xhttp.get("path") or ""
                host_header = xhttp.get("host") or xhttp.get("Host") or ""
                mode = xhttp.get("mode") or ""
                if path:
                    params.append("path=" + urllib.parse.quote(str(path), safe="/,"))
                if host_header:
                    params.append("host=" + urllib.parse.quote(str(host_header), safe=",:"))
                if mode:
                    params.append("mode=" + urllib.parse.quote(str(mode), safe=""))

            params.append("security=" + str(security))
            if security == "reality":
                reality = self._get_nested(stream, "realitySettings", "reality_settings") or {}
                if isinstance(reality, str):
                    reality = json.loads(reality) if reality.strip() else {}
                if not reality and stream:
                    reality = stream
                settings = reality.get("settings") or reality.get("Settings") or {}
                pbk = (
                    self._get_nested(reality, "publicKey", "public_key")
                    or settings.get("publicKey")
                    or settings.get("public_key")
                    or ""
                )
                if isinstance(pbk, str):
                    pbk = pbk.strip()
                sni = ""
                for key in ("serverNames", "server_names", "serverName", "server_name", "dest", "Dest"):
                    v = reality.get(key)
                    if isinstance(v, list) and v:
                        sni = str(v[0]).split(":")[0] if ":" in str(v[0]) else str(v[0])
                        break
                    if isinstance(v, str) and v.strip():
                        sni = v.split(":")[0].strip()
                        break
                short_ids = (
                    self._get_nested(reality, "shortIds", "short_ids")
                    or settings.get("shortIds")
                    or settings.get("short_ids")
                    or []
                )
                if isinstance(short_ids, str):
                    short_ids = [s.strip() for s in short_ids.split(",") if s.strip()]
                sid = short_ids[0] if short_ids else ""
                fp = (
                    self._get_nested(reality, "fingerprint", "fingerprint")
                    or settings.get("fingerprint")
                    or "random"
                )
                params.append("fp=" + str(fp))
                if pbk:
                    params.append("pbk=" + urllib.parse.quote(str(pbk), safe=""))
                if sni:
                    params.append("sni=" + urllib.parse.quote(sni, safe=""))
                if sid:
                    params.append("sid=" + urllib.parse.quote(str(sid), safe=""))
                spider_x = (
                    self._get_nested(reality, "spiderX", "spider_x")
                    or settings.get("spiderX")
                    or settings.get("spider_x")
                    or "/"
                )
                if spider_x:
                    params.append("spx=" + urllib.parse.quote(str(spider_x), safe=""))
                if network == "tcp" and client_flow:
                    params.append("flow=" + urllib.parse.quote(str(client_flow), safe=""))
            query = "&".join(params)
            frag = urllib.parse.quote(client_email, safe="")
            return f"vless://{client_uuid}@{host}:{port}/?{query}#{frag}"
        except Exception:
            return None

    async def _build_client_link_from_inbound(
        self,
        inbound_id: int,
        client_uuid: str,
        client_email: str,
    ) -> Optional[str]:
        obj = await self._get_inbound(inbound_id)
        if not obj:
            return None
        clients = self._extract_clients(obj)
        target = next((c for c in clients if c.get("id") == client_uuid), None)
        client_flow = str((target or {}).get("flow") or "").strip()
        return self._build_vless_from_inbound(obj, client_uuid, client_email, client_flow=client_flow)

    async def trial_client_uuid_seen_on_panel(
        self,
        client_uuid: str,
        *,
        client_email: str | None = None,
    ) -> bool:
        """
        True — клиент есть на панели или проверить не удалось (не сбрасывать БД).
        False — клиента точно нет.
        """
        cu = str(client_uuid).strip().lower()
        email = str(client_email or "").strip()
        if not cu and not email:
            return True
        await self._ensure_login()
        if await self._probe_new_client_api():
            try:
                resp = await self._client.get("/panel/api/clients/list", cookies=self._auth_cookies)
                resp.raise_for_status()
                body = resp.json()
                rows = body.get("obj") if isinstance(body, dict) else None
                if isinstance(rows, list):
                    for row in rows:
                        if not isinstance(row, dict):
                            continue
                        if email and str(row.get("email") or "").strip() == email:
                            return True
                        if cu and str(row.get("id") or "").strip().lower() == cu:
                            return True
                    return False
            except Exception:
                logger.debug("trial sync: clients/list недоступен", exc_info=True)
                return True
        if not cu:
            return True
        ids = await self._resolve_target_inbound_ids()
        saw_inbound_response = False
        for iid in ids:
            try:
                obj = await self._get_inbound(iid)
                if obj is None:
                    continue
                saw_inbound_response = True
                for c in self._extract_clients(obj):
                    cid = str(c.get("id") or "").strip().lower()
                    if cid == cu:
                        return True
            except Exception:
                logger.debug("trial sync: inbound %s недоступен", iid, exc_info=True)
                continue
        if not saw_inbound_response:
            return True
        return False
    async def close(self) -> None:
        await self._client.aclose()
