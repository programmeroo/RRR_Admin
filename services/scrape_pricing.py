import time
from bs4 import BeautifulSoup
from services.database_access import add_daily_price, get_quote_urls, set_server
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from decimal import Decimal
from datetime import datetime, date
from services.my_logger import log
import os
import platform
from dotenv import load_dotenv
from twilio.rest import Client
import argparse


OS_RELEASE = platform.release()
PRICING_ENGINE_URL = "https://www.loanfactorydirect.com/quote/qm?"
debugging = False
driver = None


def do_all_pricing(z_list=None):
    county_names = { 90620: "Orange", 91901: "San Diego", 91708: "Riverside", 90001: "Los Angeles", 91319: 
                    "Ventura", 91701: "San Bernardino", 96701: "Honolulu", 96703: "Kauai", 96708: "Maui", 96704: "Hawaii"}
    if z_list == None:
        z_list = [90620, 91901, 91708, 90001, 91319, 91701, 96701, 96703, 96708, 96704]

    start = datetime.now()
    log(f"{start}  Start pricing")
    count = 0

    for index, zipcode in enumerate(z_list):
        try:
            daily_prices_house = set_daily_prices(zipcode=zipcode, listing_type="house")
            daily_prices_condo = set_daily_prices(zipcode=zipcode, listing_type="condo")
            log(f"Daily Price for {county_names[zipcode]} county - House: {len(daily_prices_house)} Condo: {len(daily_prices_condo)}")
            count += len(daily_prices_house)
            count += len(daily_prices_condo)
        except Exception as e:  # <-- Catch all errors
            log(f"Exception do_all_pricing ({county_names[zipcode]} - {zipcode}): {e}")


    if driver is not None:
        try:
            driver.quit()
        except Exception as qe:
            log(f"Error quitting driver: {qe}")

    finish = datetime.now()
    log(f"{finish}  Finish pricing")
    time_diff = finish - start
    minutes = int(time_diff.total_seconds() / 60)
    msg = f"Total records: {count} in {minutes} minutes"
    log(msg)
    return count, minutes


def extract_monthly_mi(row) -> int:
    monthly_mi = 0

    # Look for MI in visible tags (including 'null')
    visible_tags = row.find_all("div", class_=lambda x: x and "table-cell" in x and "table-num" in x)

    for tag in visible_tags:
        small = tag.find("small")
        if small and "Monthly MI" in small.get_text():
            text = tag.get_text(strip=True)
            match = re.search(r"\$([\d,]+)", text)
            if match:
                monthly_mi = int(match.group(1).replace(",", ""))
                break

    return monthly_mi


def get_pricing_engine_data(soup) -> list:
    rows = soup.find_all("div", class_="table-row rounded best_lender best_lender_product rate_close lender_close")
    pricing_data = []

    for row in rows:
        try:
            # --- Extract Rate ---
            rate_tag = row.find("strong")
            rate_text = rate_tag.text.strip() if rate_tag else "N/A"
            rate_match = re.search(r"[\d.]+", rate_text)
            rate = Decimal(rate_match.group()) if rate_match else None

            # --- Extract APR ---
            apr_tag = row.find("i")
            apr_text = apr_tag.text.strip() if apr_tag else "N/A"
            apr_match = re.search(r"[\d.]+", apr_text)
            apr = Decimal(apr_match.group()) if apr_match else None

            # --- Extract Lender Name ---
            lender_tag = row.find("div", class_="lender_column")
            if lender_tag:
                texts = list(lender_tag.stripped_strings)
                lender = texts[0] if texts else "N/A"
                for junk in ["undefined", "Best lender", "FNMA - Pearl"]:
                    lender = lender.replace(junk, "")
                lender = lender.strip()
            else:
                lender = "N/A"

            # --- Extract Points/Credits (as integer dollars) ---
            points_tag = row.find("span", {"data-toggle": "tooltip"})
            points_credits = None
            if points_tag:
                text = points_tag.text.strip()
                match = re.search(r"-?\$([\d,]+)", text)
                if match:
                    value = int(match.group(1).replace(",", ""))
                    points_credits = -value if "-" in text else value

            # --- Extract Monthly MI (as integer) ---
            monthly_mi = extract_monthly_mi(row)

            if rate is not None and apr is not None and points_credits is not None:
                pricing_data.append({
                    "rate": rate,
                    "apr": apr,
                    "lender": lender,
                    "points_credits": points_credits,  # int
                    "monthly_mi": monthly_mi,          # int
                    "mi_factor": Decimal("0.0"),       # default placeholder
                })
                    
        except Exception as e:
            log(f"Error processing row: {e}")

    return pricing_data


def parse_args():
    parser = argparse.ArgumentParser(description="Run pricing scraper.")
    parser.add_argument('--env', choices=['local', 'remote'], default='remote', help='Which environment to use')
    parser.add_argument('--zips', type=str, help='Comma-separated list of ZIP codes, e.g. 92101,90001,90620')
    return parser.parse_args()


def scrape_price(driver, url: str, loan_amount: int, dp_factor: float, listing_type: str, zipcode: int, loan_type: str) -> tuple:  
    driver.get(url)

    # Wait for the first quote row to be present
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".table-row.rounded.best_lender.best_lender_product")))

    # Now parse with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    time.sleep(3)

    pricing_data = get_pricing_engine_data(soup)
    best_quote = select_best_quote(pricing_data)

    if not best_quote:
        log("select_best_quote - best_quote not returned.")
        if debugging:
            with open(f"{loan_type}_{zipcode}.html", "w") as file:
                file.write(str(soup))
        return (0,0)
    else:
         log(f"{listing_type}-{loan_type}-{loan_amount} best_quote: rate: {best_quote['rate']:.3f} points: {best_quote['points_credits']} lender: {best_quote['lender']}")
    
    mi_factor = 0.0
    if dp_factor < 0.2:
        if "monthly_mi" in best_quote:
            monthly_mi = best_quote.get("monthly_mi")
            mi_factor = float(monthly_mi) / int(loan_amount) if int(loan_amount) > 0 else 0.0

    best_quote["mi_factor"] = mi_factor

    # add the daily_price to db
    new_daily_price, status_code = add_daily_price(listing_type=listing_type, 
                                                   zipcode=zipcode, 
                                                   loan_type=loan_type, 
                                                   loan_amount=loan_amount, 
                                                   dp_factor=dp_factor,
                                                   rate=best_quote.get("rate"), 
                                                   apr=best_quote.get("apr"), 
                                                   points_credits=best_quote.get("points_credits"), 
                                                   lender=best_quote.get("lender"), 
                                                   mi_factor=mi_factor)
    
    return new_daily_price, status_code


def select_best_quote(pricing_data) -> dict:
    if not pricing_data:
        return None

    if debugging:
        log(f"Evaluating {len(pricing_data)}")

    best_quote = None
    best_choices = []
    closest_distance = 999999
    for quote in pricing_data:
        pc = quote.get("points_credits", 0)
        if abs(pc) <= 5000 and abs(pc) < closest_distance:
            closest_distance = abs(pc)
            best_choices.append(quote)
    
    best_rate_w_pts = 10.0
    for quote in best_choices:
        pc =  quote.get("points_credits", 0)
        rate =  quote.get("rate", 0)
        if pc > 0 and rate < best_rate_w_pts:
            best_rate_w_pts = rate
            best_quote = quote
        if best_quote == None:
            best_quote = quote
      
    return best_quote
        

def select_best_quote_ai(pricing_data) -> dict:
    if not pricing_data:
        return None

    if debugging:
        log(f"Evaluating {len(pricing_data)}")

    best_choices = [
        q for q in pricing_data
        if abs(q.get("points_credits", 0)) <= 5000
    ]

    # Sort by (1) absolute points_credits (favor closer to 0), then (2) rate
    best_choices.sort(key=lambda q: (
        abs(q.get("points_credits", 0)),
        q.get("rate", 10.0)
    ))

    return best_choices[0] if best_choices else None


def set_daily_prices(zipcode=0, listing_type="") -> list:
    global driver
    daily_prices=[]
    programs = {
        "conventional-20": {"dp_factor": 0.2 },
        "conventional-5": {"dp_factor": 0.05 },
        "high balance-20": {"dp_factor": 0.2 },
        "high balance-5": {"dp_factor": 0.05 },
        "fha": {"dp_factor": 0.035 },
        "va": {"dp_factor": 0.0 },
        "jumbo": {"dp_factor": 0.2 }
    }

    if driver == None:
        driver = start_selenium()

    quote_urls, status_code = get_quote_urls(zipcode=zipcode, listing_type=listing_type)

    if status_code == 200:
        for quote_url in quote_urls:
            qu = quote_url["attributes"]
            loan_type = qu.get("loan_type")
            url = qu.get("url")
            loan_amount = qu.get("loan_amount")
            dp_factor = float(qu.get("dp_factor"))

            price_data, status = scrape_price(driver, url=url, loan_amount=loan_amount, dp_factor=dp_factor, 
                                            listing_type=listing_type, zipcode=zipcode, loan_type=loan_type)

            if status == 201:
                daily_prices.append(price_data)
        
    return daily_prices


def start_selenium():
    # from selenium.webdriver.firefox.options import Options


    from selenium.webdriver.chrome.options import Options
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--headless")
    # driver = webdriver.Firefox(options=options)
    driver = webdriver.Chrome(options=options)
    time.sleep(4)
    return driver


def text_status(msg=None):
    virtual_number = os.getenv("TWILIO_VIRTUAL_NUMBER")
    verified_nmuber = os.getenv("TWILIO_VERIFIED_NUMBER")
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    client = Client(twilio_sid, twilio_token)
    client.messages.create(
        body=msg,
        from_=virtual_number,
        to=verified_nmuber
    )


def main():
    if OS_RELEASE == "5.10.16.3-microsoft-standard-WSL2":
        # WSL Ubuntu
        load_dotenv(dotenv_path='/home/andy/PYTHON/ScrapePrice/.env')
        LOCAL_DB = os.getenv("LOCAL_DB")
    elif OS_RELEASE == "6.12.25+rpt-rpi-v8":
        # Raspberry Pi
        load_dotenv(dotenv_path='/home/andys/ScrapePrice/.env')
    else:
        # Windows
        load_dotenv()    

    args = parse_args()
    print(f"args.env: {args.env}")
    if args.env == 'local':
        set_server('local')
    else:
        set_server('remote')
    
    set_server('local')
    z_list = None
    if args.zips:
        z_list = [int(z.strip()) for z in args.zips.split(",")]

    print(z_list)
    do_all_pricing(z_list)


if __name__ == "__main__":
    main()





