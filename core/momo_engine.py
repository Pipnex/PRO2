# core/momo_engine.py
# Pipnex AI — Mobile Money (MoMo) Subscription Engine for Uganda (UGX)
# Supports MTN Mobile Money & Airtel Money UGX with Test Mode & Live Gateways (Flutterwave / Direct MoMo)

import os
import json
import uuid
import time
from datetime import datetime, timedelta
import aiohttp

SUBSCRIPTIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server", "subscriptions.json")

PACKAGES = {
    "starter": {
        "id": "starter",
        "name": "Pipnex Starter",
        "price": 50000,
        "currency": "UGX",
        "duration_days": 30,
        "duration_label": "1 Month",
        "badge": "STARTER",
        "features": [
            "1 MT5 Connected Account",
            "Institutional SMC Multi-TF Signals",
            "TradingView Live Chart Overlay",
            "Basic Risk Management"
        ]
    },
    "pro": {
        "id": "pro",
        "name": "Pipnex Pro SMC",
        "price": 120000,
        "currency": "UGX",
        "duration_days": 30,
        "duration_label": "1 Month",
        "badge": "PRO SMC",
        "popular": True,
        "features": [
            "3 MT5 Connected Accounts",
            "Trish AI V6.0 Live Market Analyst",
            "Autonomous Cloud Scalper Bots",
            "NewsIQ™ High-Impact Macro Filters",
            "Pulse Multi-Asset SMC Signals"
        ]
    },
    "elite": {
        "id": "elite",
        "name": "Platinum Elite + PropPass",
        "price": 250000,
        "currency": "UGX",
        "duration_days": 90,
        "duration_label": "3 Months",
        "badge": "PLATINUM ELITE",
        "features": [
            "Unlimited MT5 Connected Accounts",
            "PropPass™ Prop Firm Challenge Protection",
            "AI Vision Chart Screenshot Analysis",
            "Zero Daily Drawdown Breach Guard",
            "Priority Oxford UK VIP Support"
        ]
    }
}


class MoMoSubscriptionEngine:
    def __init__(self):
        self.transactions = {}
        self.active_subscriptions = {}
        self.load_data()

    def load_data(self):
        if os.path.exists(SUBSCRIPTIONS_FILE):
            try:
                with open(SUBSCRIPTIONS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.transactions = data.get("transactions", {})
                    self.active_subscriptions = data.get("active_subscriptions", {})
            except Exception as e:
                print(f"[MoMoEngine] Warning loading {SUBSCRIPTIONS_FILE}: {e}")
                self.transactions = {}
                self.active_subscriptions = {}

    def save_data(self):
        try:
            os.makedirs(os.path.dirname(SUBSCRIPTIONS_FILE), exist_ok=True)
            with open(SUBSCRIPTIONS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "transactions": self.transactions,
                    "active_subscriptions": self.active_subscriptions,
                    "updated_at": datetime.utcnow().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"[MoMoEngine] Error saving {SUBSCRIPTIONS_FILE}: {e}")

    def normalize_phone(self, phone: str) -> dict:
        """
        Normalizes Uganda phone numbers into national (07XXXXXXXX) and international (2567XXXXXXXX) format
        and detects the telecom network (MTN vs Airtel).
        """
        cleaned = "".join(filter(str.isdigit, str(phone)))
        
        # Strip leading 0 or +256 / 256
        if cleaned.startswith("256") and len(cleaned) == 12:
            cleaned = "0" + cleaned[3:]
        elif cleaned.startswith("0") and len(cleaned) == 10:
            pass
        elif len(cleaned) == 9:
            cleaned = "0" + cleaned

        intl = "256" + cleaned[1:] if len(cleaned) == 10 else cleaned

        # Detect Network
        network = "Unknown"
        color = "#8b5cf6"
        prefix = cleaned[:3] if len(cleaned) >= 3 else ""

        if prefix in ["077", "078", "076", "039"]:
            network = "MTN Mobile Money"
            color = "#facc15" # Yellow
        elif prefix in ["070", "074", "075", "020"]:
            network = "Airtel Money"
            color = "#ef4444" # Red

        return {
            "raw": phone,
            "national": cleaned,
            "international": intl,
            "network": network,
            "badge_color": color,
            "valid": len(cleaned) == 10 and network != "Unknown"
        }

    async def initiate_mobile_money_payment(self, phone_number: str, package_id: str, email: str = None) -> dict:
        """
        Initiates a Mobile Money payment in UGX.
        Dispatches USSD prompt to phone (or sandbox simulation in test mode).
        """
        phone_info = self.normalize_phone(phone_number)
        selected_package = PACKAGES.get(package_id)

        if not selected_package:
            raise ValueError(f"Package '{package_id}' not found")

        tx_ref = f"PIPNEX-MOMO-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.utcnow().isoformat()

        # Check if live gateway key is configured
        flw_sec_key = os.environ.get("FLUTTERWAVE_SECRET_KEY")
        is_live = bool(flw_sec_key and not flw_sec_key.startswith("FLWSECK_TEST"))

        tx_record = {
            "tx_ref": tx_ref,
            "phone_number": phone_info["national"],
            "phone_intl": phone_info["international"],
            "network": phone_info["network"],
            "package_id": package_id,
            "package_name": selected_package["name"],
            "amount": selected_package["price"],
            "currency": selected_package["currency"],
            "duration_days": selected_package["duration_days"],
            "status": "PENDING",
            "mode": "LIVE" if is_live else "TEST",
            "created_at": now_iso,
            "email": email or f"{phone_info['national']}@pipnex-ai.com"
        }

        # If live Flutterwave secret key is present, invoke real MoMo API
        if flw_sec_key:
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "tx_ref": tx_ref,
                        "amount": str(selected_package["price"]),
                        "currency": "UGX",
                        "phone_number": phone_info["international"],
                        "email": tx_record["email"],
                        "type": "mobile_money_uganda",
                        "network": "MTN" if "MTN" in phone_info["network"] else "AIRTEL"
                    }
                    headers = {
                        "Authorization": f"Bearer {flw_sec_key}",
                        "Content-Type": "application/json"
                    }
                    async with session.post("https://api.flutterwave.com/v3/charges?type=mobile_money_uganda", json=payload, headers=headers) as resp:
                        res_json = await resp.json()
                        tx_record["gateway_response"] = res_json
            except Exception as e:
                tx_record["gateway_error"] = str(e)

        self.transactions[tx_ref] = tx_record
        self.save_data()

        return {
            "status": "PENDING",
            "message": f"Payment prompt of UGX {selected_package['price']:,} sent to your phone. Approve on {phone_info['network']}.",
            "tx_ref": tx_ref,
            "phoneNumber": phone_info["national"],
            "network": phone_info["network"],
            "badgeColor": phone_info["badge_color"],
            "package": selected_package,
            "mode": tx_record["mode"]
        }

    def get_transaction_status(self, tx_ref: str) -> dict:
        tx = self.transactions.get(tx_ref)
        if not tx:
            return {"status": "NOT_FOUND", "message": "Transaction reference not found"}
        return tx

    def simulate_approval(self, tx_ref: str) -> dict:
        """
        Simulates user entering PIN on phone and payment succeeding.
        Activates subscription immediately.
        """
        tx = self.transactions.get(tx_ref)
        if not tx:
            return {"status": "ERROR", "message": "Transaction reference not found"}

        tx["status"] = "SUCCESSFUL"
        tx["paid_at"] = datetime.utcnow().isoformat()
        
        # Calculate expiry
        duration = tx.get("duration_days", 30)
        expires_at = (datetime.utcnow() + timedelta(days=duration)).isoformat()

        sub_record = {
            "phone_number": tx["phone_number"],
            "package_id": tx["package_id"],
            "package_name": tx["package_name"],
            "status": "ACTIVE",
            "activated_at": tx["paid_at"],
            "expires_at": expires_at,
            "tx_ref": tx_ref,
            "amount": tx["amount"],
            "currency": tx["currency"]
        }

        self.active_subscriptions[tx["phone_number"]] = sub_record
        self.save_data()

        return {
            "status": "SUCCESSFUL",
            "message": f"Payment of UGX {tx['amount']:,} confirmed! {tx['package_name']} subscription activated.",
            "subscription": sub_record
        }

    def get_user_subscription(self, phone_number: str) -> dict:
        norm = self.normalize_phone(phone_number)["national"]
        sub = self.active_subscriptions.get(norm)
        if not sub:
            return {"status": "INACTIVE", "plan": "FREE", "features": ["Limited Demo"]}
        return sub


momo_engine = MoMoSubscriptionEngine()
