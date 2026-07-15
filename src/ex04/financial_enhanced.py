#!/usr/bin/env python3
"""
financial_enhanced.py — optimized version using httpx
"""

import sys
import os
import re

import httpx  # ← замена requests
from bs4 import BeautifulSoup


def load_cookies_from_file(filepath="cookies.txt"):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cookies file '{filepath}' not found.")
    cookies = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line:
                key, value = line.split("=", 1)
                cookies[key] = value
    return cookies


def get_financial_data(ticker, field):
    # Убрали time.sleep(5) — он не нужен в enhanced версии

    headers = {
        'authority': 'finance.yahoo.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'accept-language': 'ru,en;q=0.9',
        'cache-control': 'max-age=0',
        'referer': 'https://yandex.ru/',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 YaBrowser/25.8.0.0 Safari/537.36'
    }

    cookies = load_cookies_from_file("cookies.txt")
    url = f"https://finance.yahoo.com/quote/{ticker}/financials"

    try:
        # Используем httpx вместо requests
        with httpx.Client(headers=headers, cookies=cookies, timeout=15.0) as client:
            response = client.get(url, follow_redirects=True)

        if response.status_code != 200:
            if 'login.yahoo.com' in str(response.url) or 'signin' in response.text.lower():
                raise RuntimeError("Session expired — update cookies")
            raise RuntimeError(f"HTTP {response.status_code}")

        page_text = response.text.lower()
        if any(phrase in page_text for phrase in ['we couldn\'t find', 'no results found', 'symbols similar to', 'не найдено']):
            raise ValueError(f"Ticker '{ticker}' not found")

        return parse_financial_data(response.text, ticker, field)

    except httpx.RequestError as e:
        raise RuntimeError(f"Network error: {e}") from e


# Остальные функции — без изменений
def parse_financial_data(html, ticker, field):
    soup = BeautifulSoup(html, 'html.parser')
    financial_table = None

    tables = soup.find_all('table')
    for table in tables:
        table_text = table.get_text(strip=True)
        if 'Breakdown' in table_text and 'Total Revenue' in table_text:
            financial_table = table
            break

    if not financial_table:
        for table in tables:
            table_text = table.get_text(strip=True)
            if field in table_text and any(num in table_text for num in ['000', 'M', 'B']):
                financial_table = table
                break

    if not financial_table:
        div_containers = soup.find_all('div', class_=lambda x: x and any(word in str(x).lower() for word in ['table', 'grid', 'data', 'fin']))
        for div in div_containers:
            if field in div.get_text(strip=True):
                financial_table = div
                break

    result_data = extract_financial_values(financial_table, field)
    if not result_data:
        raise ValueError(f"Field '{field}' not found")

    return (field,) + tuple(result_data)


def extract_financial_values(table_element, field):
    values = []
    all_text = table_element.get_text(separator=' ', strip=True)

    pattern = rf'{re.escape(field)}\s+((?:\d{{1,3}}(?:,\d{{3}})*\s+){{5}})'
    match = re.search(pattern, all_text)

    if match:
        numbers_text = match.group(1).strip()
        numbers = re.findall(r'\d{1,3}(?:,\d{3})*', numbers_text)
        for num in numbers[:5]:
            try:
                clean_num = int(num.replace(',', ''))
                formatted = f"{clean_num:,}"
                values.append(formatted)
            except ValueError:
                values.append(num)
    else:
        elements = all_text.split()
        try:
            field_index = elements.index(field)
            for i in range(1, 6):
                if field_index + i < len(elements):
                    val = elements[field_index + i]
                    if re.match(r'\d{1,3}(?:,\d{3})*', val):
                        values.append(val)
        except ValueError:
            pass

    return values


def main():
    if len(sys.argv) != 3:
        print("Usage: ./financial_enhanced.py TICKER FIELD", file=sys.stderr)
        sys.exit(1)

    ticker = sys.argv[1].upper().strip()
    field = sys.argv[2].strip()

    try:
        result = get_financial_data(ticker, field)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()