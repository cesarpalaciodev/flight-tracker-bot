import os
import json
from pathlib import Path
from typing import Optional


class PriceHistory:
    """Gestiona historial de precios."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.data: dict = {}
        self._ensure_file()
        self.data = self._load()
    
    def _ensure_file(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._save()
    
    def _load(self) -> dict:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save(self) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError:
            pass
    
    def get_last_price(self, route: str) -> Optional[float]:
        return self.data.get(route, {}).get("last_price")
    
    def update_price(self, route: str, flight_data: dict) -> None:
        if route not in self.data:
            self.data[route] = {}
        
        self.data[route].update({
            "last_price": flight_data.get("price"),
            "last_update": flight_data.get("last_update"),
            "airline": flight_data.get("airline"),
            "booking_link": flight_data.get("booking_link")
        })
        self._save()
    
    def get_price_drop(self, route: str, new_price: float) -> Optional[float]:
        last = self.get_last_price(route)
        if last is not None:
            return last - new_price
        return None