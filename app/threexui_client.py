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
    provisioned_inbound_ids: list[int] = field(default_factory=list)
    failed_inbounds: list[tuple[int, str]] = field(default_factory=list)


class ThreeXUIClient:
    def __init__(self, config: ThreeXUIConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient(base_url=config.base_url, timeout=30.0)
        self._auth_cookies: dict[str, str] = {}

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

        Email в 3x-ui должен быть уникален на панели, поэтому на каждый inbound свой email
        (суффикс inbound id + фрагмент subId), иначе addClient даёт Duplicate email.
        """
        await self._ensure_login()

        inbound_ids = await self.list_inbound_ids(only_enabled=True)
        if not inbound_ids:
            inbound_ids = [self._config.inbound_id]

        expiry_ts_ms = int((time.time() + expire_days * 24 * 60 * 60) * 1000)
        client_uuid = str(uuid.uuid4())
        sub_id = self._generate_sub_id()
        sub_tag = sub_id[:16] if len(sub_id) >= 8 else sub_id
        logical_label = f"tg_{telegram_id}_trial"
        total_bytes = 0 if total_gb <= 0 else int(total_gb) * (1024**3)

        ok: list[int] = []
        failed: list[tuple[int, str]] = []
        for iid in inbound_ids:
            inbound_email = f"tg_{telegram_id}_i{iid}_{sub_tag}"
            client_obj: dict[str, Any] = {
                "id": client_uuid,
                "security": "auto",
                "password": "",
                "flow": "",
                "email": inbound_email,
                "limitIp": max(int(limit_ip), 0),
                "totalGB": total_bytes,
                "expiryTime": expiry_ts_ms,
                "enable": True,
                "tgId": int(telegram_id),
                "subId": sub_id,
                "comment": logical_label,
                "reset": 0,
            }
            settings_str = json.dumps({"clients": [client_obj]}, ensure_ascii=False, separators=(",", ":"))
            try:
                resp = await self._client.post(
                    "/panel/api/inbounds/addClient",
                    json={"id": iid, "settings": settings_str},
                    cookies=self._auth_cookies,
                )
                resp.raise_for_status()
                body = resp.json()
                if isinstance(body, dict) and body.get("success") is False:
                    msg = str(body.get("msg") or body.get("message") or "success=false").strip()
                    failed.append((iid, msg))
                    logger.warning("3x-ui addClient inbound=%s: %s", iid, msg)
                else:
                    ok.append(iid)
            except Exception as e:
                failed.append((iid, str(e)))
                logger.exception("3x-ui addClient inbound=%s failed", iid)

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
        email_on_link_inbound = f"tg_{telegram_id}_i{link_inbound}_{sub_tag}"
        config_text = await self._fetch_config_from_subscription(subscription_url)
        if not config_text:
            config_text = await self._build_client_link_from_inbound(
                inbound_id=link_inbound,
                client_uuid=client_uuid,
                client_email=email_on_link_inbound,
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
            subscription_url=subscription_url,
            subscription_json_url=subscription_json_url,
            provisioned_inbound_ids=ok,
            failed_inbounds=failed,
        )

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

    async def close(self) -> None:
        await self._client.aclose()
