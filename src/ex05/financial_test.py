# financial_test.py
"""
Unit tests for financial.py using PyTest.

Requirements from ex05:
- For each function in financial.py, write at least 3 tests.
- Check: correct output for Total Revenue, return type is tuple, exception on invalid ticker.
"""

import pytest
from unittest.mock import patch, Mock
from bs4 import BeautifulSoup
from financial import (
    get_financial_data,
    parse_financial_data,
    extract_financial_values,
    load_cookies_from_file
)


# === Auto-mock cookie loading to avoid filesystem dependency ===
@pytest.fixture(autouse=True)
def mock_load_cookies(monkeypatch):
    monkeypatch.setattr("financial.load_cookies_from_file", lambda _: {"A3": "dummy"})


# === Sample HTML that matches real Yahoo Finance structure ===
@pytest.fixture
def sample_html():
    return """
    <html>
    <body>
        <table>
            <tr><th>Breakdown</th><th>2023</th><th>2022</th><th>2021</th><th>2020</th><th>2019</th></tr>
            <tr><td>Total Revenue</td><td>211,915,000</td><td>198,270,000</td><td>168,088,000</td><td>143,015,000</td><td>125,843,000</td></tr>
            <tr><td>Cost of Revenue</td><td>67,272,000</td><td>62,672,000</td><td>52,232,000</td><td>46,076,000</td><td>40,340,000</td></tr>
            <tr><td>Gross Profit</td><td>144,643,000</td><td>135,598,000</td><td>115,856,000</td><td>96,939,000</td><td>85,503,000</td></tr>
        </table>
    </body>
    </html>
    """


# ==============================================================================
# TESTS FOR extract_financial_values
# ==============================================================================

def test_extract_valid_numbers():
    html = '<div>Total Revenue 211,915,000 198,270,000 168,088,000 143,015,000 125,843,000</div>'
    soup = BeautifulSoup(html, 'html.parser')
    values = extract_financial_values(soup.div, "Total Revenue")
    assert values == ["211,915,000", "198,270,000", "168,088,000", "143,015,000", "125,843,000"]


def test_extract_fewer_than_five():
    html = '<span>Net Income 50,000 60,000</span>'
    soup = BeautifulSoup(html, 'html.parser')
    values = extract_financial_values(soup.span, "Net Income")
    assert values == ["50,000", "60,000"]


def test_extract_no_numbers():
    html = '<p>Total Revenue abc def ghi</p>'
    soup = BeautifulSoup(html, 'html.parser')
    values = extract_financial_values(soup.p, "Total Revenue")
    assert values == []


def test_extract_multi_word_field():
    html = '<div>Cost of Revenue 100,000 200,000</div>'
    soup = BeautifulSoup(html, 'html.parser')
    values = extract_financial_values(soup.div, "Cost of Revenue")
    assert values == ["100,000", "200,000"]


# ==============================================================================
# TESTS FOR parse_financial_data
# ==============================================================================

def test_parse_financial_data_valid_field(sample_html):
    result = parse_financial_data(sample_html, "MSFT", "Total Revenue")
    assert isinstance(result, tuple)
    assert result[0] == "Total Revenue"
    assert len(result) == 6
    assert result[1] == "211,915,000"


def test_parse_financial_data_invalid_field(sample_html):
    with pytest.raises(ValueError, match="Field 'NonExistent' not found"):
        parse_financial_data(sample_html, "MSFT", "NonExistent")


def test_parse_financial_data_case_sensitive(sample_html):
    with pytest.raises(ValueError):
        parse_financial_data(sample_html, "MSFT", "total revenue")


@pytest.mark.parametrize("field,expected_first", [
    ("Total Revenue", "211,915,000"),
    ("Cost of Revenue", "67,272,000"),
    ("Gross Profit", "144,643,000"),
])
def test_parse_multiple_fields(sample_html, field, expected_first):
    result = parse_financial_data(sample_html, "MSFT", field)
    assert result[0] == field
    assert result[1] == expected_first


# ==============================================================================
# TESTS FOR get_financial_data — directly address ex05 requirements
# ==============================================================================

def test_get_financial_data_invalid_ticker_raises_value_error():
    """Requirement: invalid ticker → exception."""
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.text = "we couldn't find this symbol"
    mock_resp.url = "https://finance.yahoo.com/quote/BADTICK/financials/"
    
    with patch("financial.requests.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="Ticker 'BADTICK' not found"):
            get_financial_data("BADTICK", "Total Revenue")


def test_get_financial_data_session_expired_by_url():
    """Redirect to login.yahoo.com → RuntimeError."""
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.text = ""
    mock_resp.url = "https://login.yahoo.com/"  # чистый URL без пробелов

    with patch("financial.requests.get", return_value=mock_resp):
        with pytest.raises(RuntimeError, match="Session expired"):
            get_financial_data("AAPL", "Total Revenue")



def test_get_financial_data_http_404():
    """Non-200 status → RuntimeError."""
    mock_resp = Mock()
    mock_resp.status_code = 404
    mock_resp.url = "https://finance.yahoo.com/quote/BAD/financials/"
    mock_resp.text = ""
    
    with patch("financial.requests.get", return_value=mock_resp):
        with pytest.raises(RuntimeError, match="HTTP 404"):
            get_financial_data("BAD", "Total Revenue")


def test_get_financial_data_success_returns_tuple(sample_html):
    """Valid request → returns tuple with correct data."""
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.text = sample_html
    mock_resp.url = "https://finance.yahoo.com/quote/MSFT/financials/"
    
    with patch("financial.requests.get", return_value=mock_resp):
        result = get_financial_data("MSFT", "Total Revenue")
        assert isinstance(result, tuple)
        assert result[0] == "Total Revenue"
        assert result[1] == "211,915,000"


# ==============================================================================
# CLI (main) TESTS
# ==============================================================================

def test_main_success(monkeypatch, capsys):
    def mock_get(*args, **kwargs):
        return ("Total Revenue", "211,915,000", "198,270,000", "168,088,000", "143,015,000", "125,843,000")
    
    monkeypatch.setattr("financial.get_financial_data", mock_get)
    monkeypatch.setattr("sys.argv", ["financial.py", "MSFT", "Total Revenue"])
    
    from financial import main
    main()
    
    captured = capsys.readouterr()
    assert "('Total Revenue', '211,915,000'" in captured.out


def test_main_invalid_args(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["financial.py", "MSFT"])
    from financial import main
    
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert "Usage:" in capsys.readouterr().err


def test_main_handles_exceptions(monkeypatch, capsys):
    def mock_fail(*args, **kwargs):
        raise ValueError("Invalid ticker")
    
    monkeypatch.setattr("financial.get_financial_data", mock_fail)
    monkeypatch.setattr("sys.argv", ["financial.py", "BAD", "Total Revenue"])
    
    from financial import main
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert "Error: Invalid ticker" in capsys.readouterr().err