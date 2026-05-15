import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def dashboard_test_db():
    from src.models.database import Database, Base, UserConfig, Subscription, PriceRecord, AlertLog
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_path = "data/test_flight_tracker.db"
    db_url = f"sqlite:///{db_path}"

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    with TestSession() as session:
        session.query(AlertLog).delete()
        session.query(PriceRecord).delete()
        session.query(Subscription).delete()
        session.query(UserConfig).delete()

        user = UserConfig(
            chat_id="999999999",
            origins="MDE,PEI",
            destinations="ADZ",
            adults=2,
            luggage="carry_on",
            max_budget=500000.0,
            non_stop_only=0,
            onboarded=1,
            active=1,
        )
        session.add(user)
        session.flush()

        sub = Subscription(
            chat_id="999999999", plan="trial", status="trial", api_requests_limit=10, api_requests_month=2
        )
        session.add(sub)

        for i in range(3):
            session.add(
                PriceRecord(
                    chat_id="999999999",
                    route="MDE:ADZ",
                    origin="MDE",
                    destination="ADZ",
                    price=250.0 + i * 10,
                    currency="COP",
                    airline="Avianca",
                    departure_date="2026-06-15",
                    return_date="2026-06-20",
                    checked_at=datetime.utcnow() - timedelta(hours=i),
                )
            )

        session.add(
            AlertLog(
                chat_id="999999999",
                route="MDE:ADZ",
                alert_type="price_drop",
                old_price=300.0,
                new_price=250.0,
                difference=50.0,
            )
        )
        session.commit()

    db = Database(db_url)
    db.engine = engine
    db.Session = TestSession

    yield db

    try:
        os.remove(db_path)
    except OSError:
        pass


@pytest.fixture
def client(dashboard_test_db):
    db = dashboard_test_db
    from src.dashboard import app
    from src.dashboard import routes as r

    original_get_db = r.get_db
    r.get_db = lambda: db
    yield TestClient(app)
    r.get_db = original_get_db


@pytest.fixture(autouse=True)
def mock_metrics_and_files():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(
            {
                "flight_tracker_flights_searched_total": 42,
                "flight_tracker_price_checks_total": 30,
                "flight_tracker_price_alerts_sent_total": 15,
                "flight_tracker_rate_limit_hits_total": 3,
            },
            f,
        )
        metrics_path = f.name

    data = {
        "MDE:ADZ": {"last_price": 250.0, "last_update": datetime.now().isoformat(), "airline": "Avianca"},
        "PEI:ADZ": {"last_price": 400.0, "last_update": datetime.now().isoformat(), "airline": "LATAM"},
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        history_path = f.name

    with patch("src.dashboard.routes._METRICS_FILE", Path(metrics_path)):
        with patch("src.dashboard.routes.PRICE_HISTORY_FILE", Path(history_path)):
            with patch("src.dashboard.routes.DESTINATIONS", ["ADZ"]):
                with patch("src.dashboard.routes.ORIGINS", ["MDE", "PEI"]):
                    with patch("src.dashboard.routes.ADMIN_CHAT_IDS", ["999999999"]):
                        yield

    try:
        os.unlink(metrics_path)
        os.unlink(history_path)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def mock_metrics_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(
            {
                "flight_tracker_flights_searched_total": 42,
                "flight_tracker_price_checks_total": 30,
                "flight_tracker_price_alerts_sent_total": 15,
                "flight_tracker_rate_limit_hits_total": 3,
            },
            f,
        )
        metrics_path = f.name

    with patch("src.dashboard.routes._METRICS_FILE", Path(metrics_path)):
        yield

    try:
        os.unlink(metrics_path)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def mock_price_history_file():
    data = {
        "MDE:ADZ": {"last_price": 250.0, "last_update": datetime.now().isoformat(), "airline": "Avianca"},
        "PEI:ADZ": {"last_price": 400.0, "last_update": datetime.now().isoformat(), "airline": "LATAM"},
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        history_path = f.name

    with patch("src.dashboard.routes.PRICE_HISTORY_FILE", Path(history_path)):
        with patch("src.dashboard.routes.DESTINATIONS", ["ADZ"]):
            with patch("src.dashboard.routes.ORIGINS", ["MDE", "PEI"]):
                yield

    try:
        os.unlink(history_path)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def mock_admin_chat_ids():
    with patch("src.dashboard.routes.ADMIN_CHAT_IDS", ["999999999"]):
        yield


class TestHealth:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "3.0.0"

    def test_api_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"


class TestMetrics:
    def test_get_metrics(self, client):
        resp = client.get("/api/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["flights_searched_total"] == 42
        assert data["price_checks_total"] == 30
        assert data["price_alerts_sent_total"] == 15
        assert data["rate_limit_hits_total"] == 3

    def test_metrics_empty_file(self, client, monkeypatch):
        with patch("src.dashboard.routes._METRICS_FILE", Path("/nonexistent/metrics.json")):
            resp = client.get("/api/metrics")
            assert resp.status_code == 200
            data = resp.json()
            assert data["flights_searched_total"] == 0


class TestLogin:
    def test_login_success(self, client):
        resp = client.post("/api/login?chat_id=999999999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["chat_id"] == "999999999"
        assert "token" in data
        assert data["plan"] == "trial"
        assert data["is_admin"] is True

    def test_login_missing_chat_id(self, client):
        resp = client.post("/api/login?chat_id=")
        assert resp.status_code == 400

    def test_login_user_not_found(self, client):
        resp = client.post("/api/login?chat_id=000000000")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data


class TestUserData:
    def test_get_user_found(self, client):
        resp = client.get("/api/user/999999999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["config"]["origins"] == "MDE,PEI"
        assert data["config"]["adults"] == 2
        assert data["subscription"]["plan"] == "trial"
        assert len(data["recent_alerts"]) > 0
        assert len(data["prices"]) > 0

    def test_get_user_not_found(self, client):
        resp = client.get("/api/user/000000000")
        assert resp.status_code == 404

    def test_get_user_prices(self, client):
        resp = client.get("/api/user/999999999/prices")
        assert resp.status_code == 200
        data = resp.json()
        assert "routes" in data
        assert len(data["routes"]) > 0

    def test_get_user_prices_empty(self, client):
        resp = client.get("/api/user/111111111/prices")
        assert resp.status_code == 200
        data = resp.json()
        assert data["routes"] == []


class TestPrices:
    def test_get_global_prices(self, client):
        resp = client.get("/api/prices")
        assert resp.status_code == 200
        data = resp.json()
        assert "routes" in data
        prices = data["routes"]
        assert "MDE:ADZ" in prices
        assert prices["MDE:ADZ"]["price"] == 250.0
        assert prices["MDE:ADZ"]["airline"] == "Avianca"

    def test_price_comparison(self, client):
        resp = client.get("/api/price-comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["routes"]) == 2


class TestAdmin:
    def test_get_admin_users(self, client):
        resp = client.get("/api/admin/users")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["chat_id"] == "999999999"

    def test_get_admin_stats(self, client):
        resp = client.get("/api/admin/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_users"] >= 1
        assert data["active_subscriptions"] >= 1

    def test_get_admin_alerts(self, client):
        resp = client.get("/api/admin/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_disable_user(self, client):
        resp = client.post("/api/admin/disable-user/999999999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "disabled"

    def test_enable_user(self, client):
        resp = client.post("/api/admin/enable-user/999999999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "enabled"


class TestPriceChart:
    def test_price_chart_with_chat_id(self, client):
        resp = client.get("/api/price-chart?route=MDE:ADZ&chat_id=999999999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["route"] == "MDE:ADZ"
        assert len(data["points"]) > 0
        assert data["points"][0]["price"] >= 250.0

    def test_price_chart_without_chat_id(self, client):
        resp = client.get("/api/price-chart?route=MDE:ADZ")
        assert resp.status_code == 200
        data = resp.json()
        assert "points" in data


class TestStatistics:
    def test_statistics_basic(self, client):
        resp = client.get("/api/statistics")
        assert resp.status_code == 200
        data = resp.json()
        assert "metrics_captured" in data
        assert data["metrics_captured"]["flights_searched"] == 42
        assert data["metrics_captured"]["price_checks"] == 30

    def test_statistics_database(self, client):
        resp = client.get("/api/statistics")
        data = resp.json()
        db_stats = data.get("database", {})
        assert db_stats.get("total_users", 0) >= 1
        assert db_stats.get("active_subscriptions", 0) >= 1
        assert db_stats.get("total_searches", 0) >= 1
        assert db_stats.get("total_alerts", 0) >= 1


class TestLogout:
    def test_logout(self, client):
        resp = client.post("/api/logout")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "logged_out"


class TestRoot:
    def test_root_page_served(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Flight Tracker" in resp.text
