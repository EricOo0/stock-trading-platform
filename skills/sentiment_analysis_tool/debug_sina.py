#!/usr/bin/env python3
"""
Debug script for Sina scraper - shows actual HTML received
"""
import requests
from bs4 import BeautifulSoup

# Test with 平安银行
symbol = "sz000001"
url = f"https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_AllNewsStock/symbol/{symbol}.phtml"

print(f"Fetching: {url}\n")

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=10)
response.encoding = 'gb2312'

print(f"Status Code: {response.status_code}")
print(f"Content Length: {len(response.text)} chars\n")

# Parse
soup = BeautifulSoup(response.content, 'html.parser')

# Try different selectors
selectors = [
    'div.datelist ul li',
    'div#allNews ul li',
    'div.datelist li',
    'div#allNews li',
    'ul li',
    'li a'
]

for selector in selectors:
    elements = soup.select(selector)
    print(f"Selector '{selector}': Found {len(elements)} elements")
    if elements and len(elements) > 0:
        print(f"  First element text: {elements[0].get_text()[:100]}...")

# Show first 2000 chars of HTML for inspection
print("\n" + "="*70)
print("First 2000 chars of HTML:")
print("="*70)
print(response.text[:2000])
