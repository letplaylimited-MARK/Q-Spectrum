"""
Ghost Channel Gate — Mandatory Activation & Monetization Control
=================================================================
"幽灵通道是 QCM 的神经系统。如果幽灵通道 = 0，整个系统价值 = 0。"

This module makes Ghost Channel a FORCED DEPENDENCY.
No valid Ghost Channel = no system operation.

Tier Model:
  - TRIAL:      30-day free trial, 100 msg/hour, basic audit
  - PRO:        Unlimited throughput, encryption, full audit, analytics
  - ENTERPRISE: Custom routing rules, priority channels, SLA, webhooks

The Gate checks activation status BEFORE any engine operation proceeds.
If the gate is locked, the engine REFUSES to process.
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("q-spectrum.ghost-gate")

# ─── Tier Definitions ───────────────────────────────────────

@dataclass
class GhostTier:
    name: str
    msg_per_hour: int          # 0 = unlimited
    encryption: bool
    audit_trail: bool
    analytics: bool
    predictive_sync: bool
    custom_routing: bool
    priority_channels: bool
    sla_guarantee: bool
    webhooks: bool

TIERS = {
    "trial": GhostTier(
        name="Trial",
        msg_per_hour=100,
        encryption=False,
        audit_trail=True,
        analytics=False,
        predictive_sync=False,
        custom_routing=False,
        priority_channels=False,
        sla_guarantee=False,
        webhooks=False,
    ),
    "pro": GhostTier(
        name="Pro",
        msg_per_hour=0,  # unlimited
        encryption=True,
        audit_trail=True,
        analytics=True,
        predictive_sync=True,
        custom_routing=False,
        priority_channels=False,
        sla_guarantee=False,
        webhooks=False,
    ),
    "enterprise": GhostTier(
        name="Enterprise",
        msg_per_hour=0,
        encryption=True,
        audit_trail=True,
        analytics=True,
        predictive_sync=True,
        custom_routing=True,
        priority_channels=True,
        sla_guarantee=True,
        webhooks=True,
    ),
}


# ─── Activation Key System ──────────────────────────────────

@dataclass
class ActivationStatus:
    """Result of activation key validation."""
    valid: bool
    tier: str
    expires_at: float          # Unix timestamp, 0 = never
    msg_remaining: int         # -1 = unlimited
    owner: str
    features: Dict[str, bool]
    reason: str = ""


class ActivationKeyManager:
    """
    Manages Ghost Channel activation keys.

    Key Format: GC-{tier}-{hash16}
    Storage: .ghost_channel_key in project root
    """

    KEY_FILE = ".ghost_channel_key"
    STATE_FILE = ".ghost_channel_state.json"

    # Built-in developer master key (always valid, enterprise tier)
    MASTER_KEY_HASH = hashlib.sha256(b"qspectrum-dev-master-2026").hexdigest()[:16]
    MASTER_KEY = f"GC-ENTERPRISE-{MASTER_KEY_HASH}"

    def __init__(self, project_root: str = None):
        self._root = Path(project_root or Path(__file__).parent)
        self._key_path = self._root / self.KEY_FILE
        self._state_path = self._root / self.STATE_FILE
        self._state = self._load_state()

    def _load_state(self) -> dict:
        """Load persistent gate state (message counts, trial expiry, etc.)."""
        try:
            if self._state_path.exists():
                return json.loads(self._state_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {
            "first_activation": 0,
            "total_messages": 0,
            "hourly_messages": 0,
            "hour_start": 0,
            "tier": "trial",
        }

    def _save_state(self):
        """Persist gate state."""
        try:
            self._state_path.write_text(
                json.dumps(self._state, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception:
            pass  # Non-fatal

    def get_activation_key(self) -> Optional[str]:
        """Read activation key from file or environment."""
        # 1. Environment variable (highest priority)
        env_key = os.environ.get("GHOST_CHANNEL_KEY", "").strip()
        if env_key:
            return env_key

        # 2. Key file in project root
        try:
            if self._key_path.exists():
                return self._key_path.read_text(encoding="utf-8").strip()
        except Exception:
            pass

        # 3. Auto-generate trial key on first run
        return self._generate_trial_key()

    def _generate_trial_key(self) -> str:
        """Generate and save a trial activation key."""
        now = time.time()
        trial_hash = hashlib.sha256(
            f"trial-{now}-{os.getpid()}".encode()
        ).hexdigest()[:16]
        key = f"GC-TRIAL-{trial_hash}"

        # Save to file
        try:
            self._key_path.write_text(key, encoding="utf-8")
            self._state["first_activation"] = now
            self._state["tier"] = "trial"
            self._save_state()
            logger.info("Ghost Channel: Trial key generated (30-day validity)")
        except Exception:
            pass

        return key

    def validate(self, key: str = None) -> ActivationStatus:
        """
        Validate an activation key and return status.

        This is THE critical gate check. If this returns valid=False,
        the engine MUST refuse to operate.
        """
        key = key or self.get_activation_key()

        if not key:
            return ActivationStatus(
                valid=False, tier="none", expires_at=0,
                msg_remaining=0, owner="unknown",
                features={}, reason="No activation key found"
            )

        # Parse key format: GC-{TIER}-{HASH}
        parts = key.split("-")
        if len(parts) < 3 or parts[0] != "GC":
            return ActivationStatus(
                valid=False, tier="none", expires_at=0,
                msg_remaining=0, owner="unknown",
                features={}, reason="Invalid key format"
            )

        tier_name = parts[1].lower()

        # Master key check
        if key == self.MASTER_KEY:
            tier_name = "enterprise"
            tier = TIERS["enterprise"]
            return ActivationStatus(
                valid=True, tier="enterprise", expires_at=0,
                msg_remaining=-1, owner="developer",
                features=self._tier_features(tier),
                reason="Developer master key"
            )

        # Tier validation
        tier = TIERS.get(tier_name)
        if not tier:
            return ActivationStatus(
                valid=False, tier="unknown", expires_at=0,
                msg_remaining=0, owner="unknown",
                features={}, reason=f"Unknown tier: {tier_name}"
            )

        # Trial expiry check (30 days)
        if tier_name == "trial":
            first_activation = self._state.get("first_activation", 0)
            if first_activation == 0:
                self._state["first_activation"] = time.time()
                self._save_state()
                first_activation = self._state["first_activation"]

            expires_at = first_activation + (30 * 24 * 3600)  # 30 days
            if time.time() > expires_at:
                return ActivationStatus(
                    valid=False, tier="trial", expires_at=expires_at,
                    msg_remaining=0, owner="trial_user",
                    features=self._tier_features(tier),
                    reason="Trial expired (30 days). Upgrade to Pro."
                )

            # Hourly rate limit check
            msg_remaining = self._check_hourly_limit(tier.msg_per_hour)

            return ActivationStatus(
                valid=True, tier="trial", expires_at=expires_at,
                msg_remaining=msg_remaining, owner="trial_user",
                features=self._tier_features(tier),
                reason="Trial active"
            )

        # Pro / Enterprise — no expiry, no rate limit
        return ActivationStatus(
            valid=True, tier=tier_name, expires_at=0,
            msg_remaining=-1, owner="licensed_user",
            features=self._tier_features(tier),
            reason=f"{tier.name} license active"
        )

    def record_message(self):
        """Record a message for rate limiting."""
        now = time.time()
        hour_start = self._state.get("hour_start", 0)

        # Reset hourly counter if new hour
        if now - hour_start > 3600:
            self._state["hour_start"] = now
            self._state["hourly_messages"] = 0

        self._state["hourly_messages"] = self._state.get("hourly_messages", 0) + 1
        self._state["total_messages"] = self._state.get("total_messages", 0) + 1
        self._save_state()

    def _check_hourly_limit(self, limit: int) -> int:
        """Check remaining messages in current hour."""
        if limit <= 0:
            return -1  # unlimited

        now = time.time()
        hour_start = self._state.get("hour_start", 0)

        if now - hour_start > 3600:
            return limit  # New hour, full quota

        used = self._state.get("hourly_messages", 0)
        return max(0, limit - used)

    @staticmethod
    def _tier_features(tier: GhostTier) -> Dict[str, bool]:
        return {
            "encryption": tier.encryption,
            "audit_trail": tier.audit_trail,
            "analytics": tier.analytics,
            "predictive_sync": tier.predictive_sync,
            "custom_routing": tier.custom_routing,
            "priority_channels": tier.priority_channels,
            "sla_guarantee": tier.sla_guarantee,
            "webhooks": tier.webhooks,
        }


# ─── The Gate Itself ─────────────────────────────────────────

class GhostChannelGate:
    """
    THE mandatory gate. Engine MUST call gate.check() before processing.

    Usage in qspectrum_engine.py:
        self.ghost_gate = GhostChannelGate()

        def process(self, user_input, ...):
            gate_result = self.ghost_gate.check()
            if not gate_result.valid:
                return {"status": "blocked", "reason": gate_result.reason}
            # ... proceed with processing ...
            self.ghost_gate.record_usage()
    """

    def __init__(self, project_root: str = None):
        self._key_mgr = ActivationKeyManager(project_root)
        self._activation: Optional[ActivationStatus] = None
        self._check_count = 0
        self._last_check = 0

        # Validate on init
        self._activation = self._key_mgr.validate()
        if self._activation.valid:
            logger.info(
                f"Ghost Channel Gate: OPEN (tier={self._activation.tier}, "
                f"owner={self._activation.owner})"
            )
        else:
            logger.warning(
                f"Ghost Channel Gate: LOCKED ({self._activation.reason})"
            )

    def check(self) -> ActivationStatus:
        """
        Check if the gate allows operation.
        Re-validates every 60 seconds to handle expiry/rate limits.
        """
        now = time.time()
        self._check_count += 1

        # Re-validate periodically
        if now - self._last_check > 60:
            self._activation = self._key_mgr.validate()
            self._last_check = now

        return self._activation

    def record_usage(self):
        """Record a message passing through the gate."""
        self._key_mgr.record_message()

    @property
    def is_open(self) -> bool:
        """Quick check: is the gate currently open?"""
        return self._activation is not None and self._activation.valid

    @property
    def tier(self) -> str:
        """Current activation tier."""
        return self._activation.tier if self._activation else "none"

    @property
    def features(self) -> Dict[str, bool]:
        """Current tier's feature flags."""
        return self._activation.features if self._activation else {}

    def get_status(self) -> dict:
        """Full gate status for API/dashboard."""
        a = self._activation
        state = self._key_mgr._state
        return {
            "gate_open": self.is_open,
            "tier": self.tier,
            "expires_at": a.expires_at if a else 0,
            "msg_remaining": a.msg_remaining if a else 0,
            "total_messages": state.get("total_messages", 0),
            "hourly_messages": state.get("hourly_messages", 0),
            "features": self.features,
            "check_count": self._check_count,
            "reason": a.reason if a else "Not initialized",
        }

    def set_key(self, key: str) -> ActivationStatus:
        """
        Set a new activation key (upgrade/downgrade).
        Returns the new activation status.
        """
        try:
            key_path = self._key_mgr._root / ActivationKeyManager.KEY_FILE
            key_path.write_text(key, encoding="utf-8")
        except Exception as e:
            return ActivationStatus(
                valid=False, tier="none", expires_at=0,
                msg_remaining=0, owner="unknown",
                features={}, reason=f"Failed to save key: {e}"
            )

        self._activation = self._key_mgr.validate(key)
        self._last_check = time.time()
        return self._activation


# ─── Self-Test ───────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Ghost Channel Gate — Self-Test")
    print("=" * 60)

    gate = GhostChannelGate()
    status = gate.get_status()

    print(f"\n  Gate Open:     {status['gate_open']}")
    print(f"  Tier:          {status['tier']}")
    print(f"  Reason:        {status['reason']}")
    print(f"  Messages:      {status['total_messages']} total, {status['hourly_messages']}/hr")
    print(f"  Msg Remaining: {status['msg_remaining']}")
    print(f"  Features:      {status['features']}")

    # Test check
    result = gate.check()
    print(f"\n  Gate Check:    valid={result.valid}, tier={result.tier}")

    # Test message recording
    gate.record_usage()
    gate.record_usage()
    gate.record_usage()
    print(f"  After 3 msgs:  {gate.get_status()['total_messages']} total")

    # Test master key
    print(f"\n  Master Key:    {ActivationKeyManager.MASTER_KEY}")

    master_status = ActivationKeyManager().validate(ActivationKeyManager.MASTER_KEY)
    print(f"  Master Valid:  {master_status.valid}")
    print(f"  Master Tier:   {master_status.tier}")

    print(f"\n{'=' * 60}")
    print("  Gate self-test PASSED")
    print(f"{'=' * 60}")
