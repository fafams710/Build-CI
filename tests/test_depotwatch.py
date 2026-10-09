import pytest
import requests
from depotwatch import fetch_shipments, heavy_shipments, unweighed, describe, report, main


def test_heavy_shipment_filter_and_sort():

    SHIPMENTS = [
    {"id": 1, "destination": "north", "packing": "crated", "weight_kg": 120},
    {"id": 2, "destination": "south", "packing": "loose", "weight_kg": 40},
    {"id": 3, "destination": "east", "packing": "crated", "weight_kg": 310},
    {"id": 4, "destination": "west", "packing": "crated", "weight_kg": None},
]
    result = heavy_shipments(SHIPMENTS, 100)
    assert len(result) == 2
    assert result[0]["id"] == 3
    assert result[1]["id"] == 1

def test_heavy_shipment_at_exact_threshold():
    shipments = [
        {"id": 1, "destination": "north", "packing": "crated", "weight_kg": 120},
    ]
    result = heavy_shipments(shipments, 100)

    assert len(result) == 1
    assert result[0]["id"] == 1

def test_unweighed_shipments():
    shipments = [
        {"id": 1, "destination": "north", "packing": "crated", "weight_kg": 120},
        {"id": 2, "destination": "south", "packing": "loose", "weight_kg": None},
        {"id": 3, "destination": "east", "packing": "crated"},
    ]
    assert unweighed(shipments) == [2, 3]

def test_heavy_shipments_ignores_invalid_and_missing_weights():
    shipments = [
        {"id": 1, "destination": "north", "packing": "crated", "weight_kg": None},
        {"id": 2, "destination": "south", "packing": "loose", "weight_kg": "150"},
        {"id": 3, "destination": "east", "packing": "crated"},
    ]
    assert heavy_shipments(shipments, 100) == []

def test_describe_formatting():
    shipment = {"id": 1, "destination": "north", "packing": "crated", "weight_kg": 120}
    assert describe(shipment) == "#1 north  crated    120kg"

def test_fetch_shipments_success(monkeypatch):
    def fake_get(url, timeout=None):
        response = requests.Response()
        response.status_code = 200
        response.encoding = "utf-8"
        response._content = b'[{"id": 1, "weight_kg": 150}]'
        return response

    monkeypatch.setattr(requests, "get", fake_get)
    result = fetch_shipments("http://localhost:8420")
    assert result == [{"id": 1, "weight_kg": 150}]


def test_report_success(monkeypatch, capsys):
    def fake_get(url, timeout=None):
        response = requests.Response()
        response.status_code = 200
        response.encoding = "utf-8"
        response._content = b"""[
            {"id": 1, "destination": "north", "packing": "crated", "weight_kg": 120},
            {"id": 2, "destination": "south", "packing": "loose", "weight_kg": 40},
            {"id": 4, "destination": "west", "packing": "crated", "weight_kg": null}
        ]"""
        return response

    monkeypatch.setattr(requests, "get", fake_get)

    exit_code = report(100)
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "1 at or above 100kg" in captured
    assert "#1 north  crated    120kg" in captured
    assert "no weight recorded for: 4" in captured


def test_report_no_heavy_shipments(monkeypatch, capsys):
    def fake_get(url, timeout=None):
        response = requests.Response()
        response.status_code = 200
        response._content = b'[{"id": 2, "destination": "south", "packing": "loose", "weight_kg": 40}]'
        return response

    monkeypatch.setattr(requests, "get", fake_get)

    exit_code = report(100)
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "nothing at or above 100kg" in captured


def test_report_empty_shipment_list(monkeypatch, capsys):
    def fake_get(url, timeout=None):
        response = requests.Response()
        response.status_code = 200
        response._content = b"[]"
        return response

    monkeypatch.setattr(requests, "get", fake_get)

    exit_code = report(100)
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "nothing at or above 100kg" in captured


def test_report_http_error(monkeypatch, capsys):
    def fake_get(url, timeout=None):
        response = requests.Response()
        response.status_code = 500
        return response

    monkeypatch.setattr(requests, "get", fake_get)

    exit_code = report(100)
    captured = capsys.readouterr().out

    assert exit_code == 1
    assert "the depot answered with an error: 500" in captured


def test_report_connection_error(monkeypatch, capsys):
    def fake_get(url, timeout=None):
        raise requests.ConnectionError()

    monkeypatch.setattr(requests, "get", fake_get)

    exit_code = report(100)
    captured = capsys.readouterr().out

    assert exit_code == 1
    assert "could not reach the depot: ConnectionError" in captured

def test_main_default_threshold(monkeypatch):
    calls = []

    def fake_report(threshold):
        calls.append(threshold)
        return 0

    monkeypatch.setattr("depotwatch.report", fake_report)
    exit_code = main(["depotwatch.py"])

    assert exit_code == 0
    assert calls == [100]

def test_main_invalid_threshold_type(capsys):
    exit_code = main(["depotwatch.py", "not_a_number"])
    captured = capsys.readouterr().out

    assert exit_code == 2
    assert "threshold must be a whole number of kg" in captured