from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.tools import tool


class ShoppingDataStore:
    """Student scaffold for mock-data lookup."""

    def __init__(self, json_path: Path) -> None:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.metadata = data.get("metadata", {})
        self.customers = data.get("customers", [])
        self.orders = data.get("orders", [])
        self.vouchers = data.get("vouchers", [])

        # Build in-memory indexes for fast O(1) lookups
        self.customer_by_id = {c["customer_id"]: c for c in self.customers}
        self.order_by_id = {o["order_id"]: o for o in self.orders}
        
        self.orders_by_customer_id = {}
        for o in self.orders:
            cid = o["customer_id"]
            if cid not in self.orders_by_customer_id:
                self.orders_by_customer_id[cid] = []
            self.orders_by_customer_id[cid].append(o)
            
        self.vouchers_by_customer_id = {}
        for v in self.vouchers:
            cid = v["customer_id"]
            if cid not in self.vouchers_by_customer_id:
                self.vouchers_by_customer_id[cid] = []
            self.vouchers_by_customer_id[cid].append(v)

    def get_customer_by_id(self, customer_id: str) -> dict[str, Any]:
        customer = self.customer_by_id.get(customer_id)
        if customer:
            return {"status": "ok", "customer": customer}
        return {"status": "not_found", "message": f"Customer '{customer_id}' not found."}

    def get_orders_by_customer_id(self, customer_id: str, limit: int = 10) -> dict[str, Any]:
        orders = self.orders_by_customer_id.get(customer_id, [])
        if orders:
            orders = sorted(orders, key=lambda x: x.get("created_at", ""), reverse=True)
            return {"status": "ok", "orders": orders[:limit]}
        return {"status": "not_found", "message": f"No orders found for customer '{customer_id}'."}

    def get_order_detail_by_order_id(self, order_id: str) -> dict[str, Any]:
        order = self.order_by_id.get(order_id)
        if order:
            return {"status": "ok", "order": order}
        return {"status": "not_found", "message": f"Order '{order_id}' not found."}

    def get_vouchers_by_customer_id(
        self,
        customer_id: str,
        only_active: bool = False,
    ) -> dict[str, Any]:
        vouchers = self.vouchers_by_customer_id.get(customer_id, [])
        if only_active:
            vouchers = [v for v in vouchers if v.get("status") == "active" and v.get("remaining_uses", 0) > 0]
            
        if vouchers:
            return {"status": "ok", "vouchers": vouchers}
        return {"status": "not_found", "message": f"No vouchers found for customer '{customer_id}'."}


def build_data_tools(store: ShoppingDataStore) -> list:
    @tool
    def get_customer_by_id(customer_id: str) -> dict[str, Any]:
        """Look up a customer's basic information and statistics using their customer_id."""
        return store.get_customer_by_id(customer_id)

    @tool
    def get_orders_by_customer_id(customer_id: str, limit: int = 10) -> dict[str, Any]:
        """Retrieve a list of the most recent orders placed by a specific customer using their customer_id."""
        return store.get_orders_by_customer_id(customer_id, limit)

    @tool
    def get_order_detail_by_order_id(order_id: str) -> dict[str, Any]:
        """Look up detailed information for a specific order using its order_id, including status, delivery, and items."""
        return store.get_order_detail_by_order_id(order_id)

    @tool
    def get_vouchers_by_customer_id(customer_id: str, only_active: bool = False) -> dict[str, Any]:
        """Retrieve the list of vouchers owned by a customer using their customer_id. Set only_active=True to filter for usable vouchers."""
        return store.get_vouchers_by_customer_id(customer_id, only_active)

    return [
        get_customer_by_id,
        get_orders_by_customer_id,
        get_order_detail_by_order_id,
        get_vouchers_by_customer_id,
    ]
