import csv
import logging

from src.models.price_history import PriceHistory
from src.utils.config import DESTINATIONS, ORIGINS

logger = logging.getLogger(__name__)


def export_price_history_csv(history: PriceHistory) -> str:
    output = "Route,Origin,Destination,Price,Currency,Airline,LastUpdate\n"
    for dest in DESTINATIONS:
        for origin in ORIGINS:
            route = f"{origin}:{dest}"
            data = history.data.get(route, {})
            if data.get("last_price"):
                output += (
                    f"{route},{origin},{dest},"
                    f"{data['last_price']},COP,"
                    f"{data.get('airline', 'N/A')},"
                    f"{data.get('last_update', 'N/A')}\n"
                )
    return output


def export_price_history_to_file(history: PriceHistory, filepath: str) -> str:
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Route", "Origin", "Destination", "Price", "Currency", "Airline", "Last Update"])
        for dest in DESTINATIONS:
            for origin in ORIGINS:
                route = f"{origin}:{dest}"
                data = history.data.get(route, {})
                if data.get("last_price"):
                    writer.writerow([
                        route, origin, dest,
                        data["last_price"], "COP",
                        data.get("airline", "N/A"),
                        data.get("last_update", "N/A"),
                    ])
    logger.info(f"CSV exported to {filepath}")
    return filepath


def get_stats_summary(history: PriceHistory) -> dict:
    prices = []
    airlines = set()
    for dest in DESTINATIONS:
        for origin in ORIGINS:
            route = f"{origin}:{dest}"
            data = history.data.get(route, {})
            price = data.get("last_price")
            if price:
                prices.append(price)
                if data.get("airline"):
                    airlines.add(data["airline"])
    return {
        "lowest_price": min(prices) if prices else None,
        "highest_price": max(prices) if prices else None,
        "average_price": sum(prices) / len(prices) if prices else None,
        "total_routes": len(DESTINATIONS) * len(ORIGINS),
        "airlines": sorted(airlines),
    }
