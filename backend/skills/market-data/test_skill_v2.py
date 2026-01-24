from scripts.market_data import MarketDataSkill
import json

skill = MarketDataSkill()

print("\n--- Testing Quote (Index) ---")
print(json.dumps(skill.get_quote("上证指数"), ensure_ascii=False))

print("\n--- Testing Indices (CN) ---")
# Use limit if get_indices_quote supported it, but it returns fixed list mostly.
print(json.dumps(skill.get_indices_quote("CN")[:2], ensure_ascii=False))

print("\n--- Testing Sector Constituents ---")
print(json.dumps(skill.get_sector_constituents("酿酒行业", limit=2), ensure_ascii=False))

print("\n--- Testing Turnover ---")
print(json.dumps(skill.get_market_turnover(), ensure_ascii=False))
