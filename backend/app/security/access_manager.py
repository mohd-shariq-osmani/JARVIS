import os
import time
import uuid
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from pydantic import BaseModel

logger = logging.getLogger("AccessManager")
PERMISSIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'permissions.json')

class AccessRequest(BaseModel):
    id: str
    action: str
    resource: str
    reason: str
    status: str = "pending"  # "pending", "granted", "denied"
    created_at: float

class AccessManager:
    def __init__(self, broadcast_callback: Optional[Callable] = None):
        os.makedirs(os.path.dirname(PERMISSIONS_FILE), exist_ok=True)
        self.broadcast_callback = broadcast_callback
        self.pending_requests: Dict[str, AccessRequest] = {}
        self.authorized_resources: set = {"c:\\", "downloads", "desktop", "documents"}
        self._future_responses: Dict[str, asyncio.Future] = {}
        self.load_permissions()

    def set_broadcast_callback(self, callback: Callable):
        self.broadcast_callback = callback

    def load_permissions(self):
        if os.path.exists(PERMISSIONS_FILE):
            try:
                with open(PERMISSIONS_FILE, 'r') as f:
                    data = json.load(f)
                    self.authorized_resources = set(data.get("authorized", []))
                    logger.info(f"Loaded {len(self.authorized_resources)} authorized resources from disk.")
            except Exception as e:
                logger.error(f"Failed to load permissions: {e}")
        else:
            self.save_permissions()

    def save_permissions(self):
        try:
            with open(PERMISSIONS_FILE, 'w') as f:
                json.dump({"authorized": list(self.authorized_resources)}, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save permissions: {e}")

    def is_authorized(self, resource: str) -> bool:
        res_clean = resource.strip().lower()
        if res_clean in self.authorized_resources:
            return True
        for auth in self.authorized_resources:
            if res_clean.startswith(auth) or auth in res_clean:
                return True
        return False

    def grant_authorization(self, resource: str):
        self.authorized_resources.add(resource.strip().lower())
        self.save_permissions()
        logger.info(f"Granted permanent access to: {resource}")

    def revoke_authorization(self, resource: str):
        res = resource.strip().lower()
        if res in self.authorized_resources:
            self.authorized_resources.remove(res)
            self.save_permissions()

    async def create_access_request(self, action: str, resource: str, reason: str) -> AccessRequest:
        req_id = str(uuid.uuid4())[:8]
        req = AccessRequest(
            id=req_id,
            action=action,
            resource=resource,
            reason=reason,
            created_at=time.time()
        )
        self.pending_requests[req_id] = req
        
        # Broadcast to UI
        if self.broadcast_callback:
            try:
                await self.broadcast_callback("ACCESS_REQUEST", req.dict())
            except Exception as e:
                logger.error(f"Failed to broadcast access request: {e}")
                
        return req

    async def request_permission(self, action: str, resource: str, reason: str, timeout_seconds: float = 30.0) -> bool:
        """Asks user for permission. Pauses and waits for UI modal click or voice confirmation."""
        if self.is_authorized(resource):
            return True
            
        req = await self.create_access_request(action, resource, reason)
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self._future_responses[req.id] = future
        
        logger.info(f"Waiting for user authorization on request [{req.id}]: {action} ({resource})")
        
        try:
            decision = await asyncio.wait_for(future, timeout=timeout_seconds)
            return decision
        except asyncio.TimeoutError:
            logger.warning(f"Access request [{req.id}] timed out.")
            req.status = "denied"
            return False
        finally:
            if req.id in self._future_responses:
                del self._future_responses[req.id]

    def respond_to_request(self, request_id: str, grant: bool) -> bool:
        req = self.pending_requests.get(request_id)
        if not req:
            # Fallback to latest pending request if ID is generic
            if self.pending_requests:
                req = list(self.pending_requests.values())[-1]
                
        if req:
            req.status = "granted" if grant else "denied"
            if grant:
                self.grant_authorization(req.resource)
                
            if req.id in self._future_responses:
                fut = self._future_responses[req.id]
                if not fut.done():
                    fut.set_result(grant)
            return True
        return False

    def handle_voice_permission(self, text: str) -> Optional[bool]:
        """Detects if user spoken response is answering a pending access request."""
        if not self.pending_requests:
            return None
            
        t = text.lower().strip()
        positive = ["grant access", "grant", "allow", "yes allow", "authorize", "yes", "proceed", "approve", "go ahead"]
        negative = ["deny", "deny access", "no", "cancel", "reject", "do not allow", "stop"]
        
        latest_req = list(self.pending_requests.values())[-1]
        if latest_req.status == "pending":
            if any(p in t for p in positive):
                self.respond_to_request(latest_req.id, True)
                return True
            if any(n in t for n in negative):
                self.respond_to_request(latest_req.id, False)
                return False
        return None

# Global Access Manager Singleton
access_manager = AccessManager()
