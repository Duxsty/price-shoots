def scrape_currys_price(url):
    api_url = 'https://app.scrapingbee.com/api/v1/'
    params = {
        'api_key': SCRAPINGBEE_API_KEY,
        'url': url,
        'render_js': 'true'
    }

    try:
        response = requests.get(api_url, params=params, timeout=20)
        html = response.text

        # Helpful: print preview to debug
        with open("debug_currys.html", "w", encoding="utf-8") as f:
            f.write(html)

        soup = BeautifulSoup(html, 'html.parser')

        # Primary selector (old version)
        price_tag = soup.find('p', class_='product-price_price')

        # Alternate selector (based on April 2025 site structure)
        if not price_tag:
            price_tag = soup.select_one('[data-testid="product-price"]')

        # Fallback: look for any span with a £ symbol
        if not price_tag:
            price_tag = soup.find("span", string=lambda s: s and "£" in s)

        if price_tag:
            price_text = price_tag.get_text().replace("£", "").replace(",", "").strip()
            return float(price_text)

    except Exception as e:
        print(f"[ERROR scraping Currys] {e}")
        return None

    return None
