from skill import MarketDataSkill

def test_skill():
    skill = MarketDataSkill()

    print("\n--- Testing Quote ---")
    quote = skill.get_stock_quote("600036")
    print("Quote (600036):", quote.get('symbol'), quote.get('price'))
    
    # Optional: Test fallback or other markets if desired, but keep it simple for verification
    # quote_hk = skill.get_stock_quote("00700")
    # print("Quote (00700):", quote_hk.get('symbol'), quote_hk.get('price'))

    print("\n--- Testing K-Line ---")
    kline = skill.get_kline("600036", period="daily", start_date="20231201", end_date="20231210")
    print(f"K-Line (600036) Len: {len(kline)}")
    if kline:
        print("First Candle:", kline[0])

    print("\n--- Testing Fund Flow (North) ---")
    north = skill.get_fund_flow("north")
    print(f"North Flow Len: {len(north)}")
    if north:
        print("Latest North:", north[0])

    print("\n--- Testing Fund Flow (Stock) ---")
    stock_flow = skill.get_fund_flow("stock", target="600036")
    print(f"Stock Flow Len: {len(stock_flow)}")
    if stock_flow:
        print("Latest Stock Flow:", stock_flow[0])

    print("\n--- Testing Sector Ranking ---")
    ranks = skill.get_sector_ranking()
    print(f"Sector Ranks Len: {len(ranks)}")
    if ranks:
        print("Top 1 Sector:", ranks[0])

if __name__ == "__main__":
    test_skill()
