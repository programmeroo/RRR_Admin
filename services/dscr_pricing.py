import time
from bs4 import BeautifulSoup
import re
from decimal import Decimal
from datetime import datetime
from services.my_logger import log
from services.my_logger import log
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import platform
from dotenv import load_dotenv
from twilio.rest import Client
import argparse
# from dscr_db_access import add_dscr_price, set_server   # use this on RaspBerry-Pi
from services.database_access import add_dscr_price, set_server  # use this on admin app

OS_RELEASE = platform.release()
debugging = False
driver = None


def dscr_pricing(z_list=None):
    # set_server('local')
    county_names = { 90620: "Orange", 91901: "San Diego", 91708: "Riverside", 90001: "Los Angeles", 91319: 
                    "Ventura", 91701: "San Bernardino", 96701: "Honolulu", 96703: "Kauai", 96708: "Maui", 96704: "Hawaii"}
    if z_list == None:
        z_list = [90620, 91901, 91708, 90001, 91319, 91701, 96701, 96703, 96708, 96704]

    house_80 = "https://www.loanfactorydirect.com/quote/non_qm?purpose=PM&property_value=1000000&loan_amount=800000&credit_score=780&non_qm_document_type=property_cash_flow_or_dscr&occupancy=Investment&loan_type=Non_QM&state=HI&zip=96813&property_type=Single&actual_number_of_units=1&citizenship=us_citizen&mortgage_lates=No_mortgage_late&credit_event=None&prepayment_penalty=_60_months_pp&non_qm_cash_reserved=6&interest_only=No&lock_period=30&has_self_employed=No&non_qm_dscr=1&first_time_investor=No&loan_to_close_name=Individual&borrower_paid_compensation=1&compensation_type=borrower_paid&impounds=Yes&employment_history=2&loan_program_group=FIXED_30"
    house_75 = "https://www.loanfactorydirect.com/quote/non_qm?purpose=PM&property_value=1000000&loan_amount=750000&credit_score=780&non_qm_document_type=property_cash_flow_or_dscr&occupancy=Investment&loan_type=Non_QM&state=HI&zip=96813&property_type=Single&actual_number_of_units=1&citizenship=us_citizen&mortgage_lates=No_mortgage_late&credit_event=None&prepayment_penalty=_60_months_pp&non_qm_cash_reserved=6&interest_only=No&lock_period=30&has_self_employed=No&non_qm_dscr=1&first_time_investor=No&loan_to_close_name=Individual&borrower_paid_compensation=1&compensation_type=borrower_paid&impounds=Yes&employment_history=2&loan_program_group=FIXED_30"
    house_75_io = "https://www.loanfactorydirect.com/quote/non_qm?purpose=PM&property_value=1000000&loan_amount=750000&credit_score=780&non_qm_document_type=property_cash_flow_or_dscr&occupancy=Investment&loan_type=Non_QM&state=HI&zip=96813&property_type=Single&actual_number_of_units=1&citizenship=us_citizen&mortgage_lates=No_mortgage_late&credit_event=None&prepayment_penalty=_60_months_pp&non_qm_cash_reserved=6&interest_only=Yes&lock_period=30&has_self_employed=No&non_qm_dscr=1&first_time_investor=No&loan_to_close_name=Individual&borrower_paid_compensation=1&compensation_type=borrower_paid&impounds=Yes&employment_history=2&loan_program_group=FIXED_30"
    condo_80 = "https://www.loanfactorydirect.com/quote/non_qm?purpose=PM&property_value=1000000&loan_amount=800000&credit_score=780&non_qm_document_type=property_cash_flow_or_dscr&occupancy=Investment&loan_type=Non_QM&state=HI&zip=96813&property_type=Condo&actual_number_of_units=1&citizenship=us_citizen&mortgage_lates=No_mortgage_late&credit_event=None&prepayment_penalty=_60_months_pp&non_qm_cash_reserved=6&interest_only=No&lock_period=30&has_self_employed=No&non_qm_dscr=1&first_time_investor=No&loan_to_close_name=Individual&borrower_paid_compensation=1&compensation_type=borrower_paid&impounds=Yes&employment_history=2&loan_program_group=FIXED_30"
    condo_75 = "https://www.loanfactorydirect.com/quote/non_qm?purpose=PM&property_value=1000000&loan_amount=750000&credit_score=780&non_qm_document_type=property_cash_flow_or_dscr&occupancy=Investment&loan_type=Non_QM&state=HI&zip=96813&property_type=Condo&actual_number_of_units=1&citizenship=us_citizen&mortgage_lates=No_mortgage_late&credit_event=None&prepayment_penalty=_60_months_pp&non_qm_cash_reserved=6&interest_only=No&lock_period=30&has_self_employed=No&non_qm_dscr=1&first_time_investor=No&loan_to_close_name=Individual&borrower_paid_compensation=1&compensation_type=borrower_paid&impounds=Yes&employment_history=2&loan_program_group=FIXED_30"
    condo_75_io = "https://www.loanfactorydirect.com/quote/non_qm?purpose=PM&property_value=1000000&loan_amount=750000&credit_score=780&non_qm_document_type=property_cash_flow_or_dscr&occupancy=Investment&loan_type=Non_QM&state=HI&zip=96813&property_type=Condo&actual_number_of_units=1&citizenship=us_citizen&mortgage_lates=No_mortgage_late&credit_event=None&prepayment_penalty=_60_months_pp&non_qm_cash_reserved=6&interest_only=Yes&lock_period=30&has_self_employed=No&non_qm_dscr=1&first_time_investor=No&loan_to_close_name=Individual&borrower_paid_compensation=1&compensation_type=borrower_paid&impounds=Yes&employment_history=2&loan_program_group=FIXED_30"

    start = datetime.now()
    log("     ")
    log(f"{start}  Start DSCR pricing")
    count = 0

    orig_dscr_programs = [
        { "program": "house_80", "listing_type": "house", "ltv": 80, "interest_only": False, "url": house_80, "quote": None },
        { "program": "house_75", "listing_type": "house", "ltv": 75, "interest_only": False, "url": house_75, "quote": None},
        { "program": "house_75_io", "listing_type": "house", "ltv": 75, "interest_only": True, "url": house_75_io, "quote": None},
        { "program": "condo_80", "listing_type": "condo", "ltv": 80, "interest_only": False, "url": condo_80, "quote": None},
        { "program": "condo_75", "listing_type": "condo", "ltv": 75, "interest_only": False, "url": condo_75, "quote": None},
        { "program": "condo_75_io", "listing_type": "condo", "ltv": 75, "interest_only": True, "url": condo_75_io, "quote": None},        
    ]

    dscr_programs = [
        { "program": "condo_80", "listing_type": "condo", "ltv": 80, "interest_only": False, "url": condo_80, "quote": None},
        { "program": "condo_75", "listing_type": "condo", "ltv": 75, "interest_only": False, "url": condo_75, "quote": None},
        { "program": "condo_75_io", "listing_type": "condo", "ltv": 75, "interest_only": True, "url": condo_75_io, "quote": None},        
    ]

    count = 0
    status = True

    driver = start_selenium()

    for program in dscr_programs:
        listing_type = program.get("listing_type")
        LTV = program.get("ltv")
        interest_only = program.get("interest_only")
        log(f"Scrape - {listing_type} LTV: {LTV} IO: {interest_only}")
        
        program["quote"] = scrape_dscr_price(driver, url = program.get("url"))
        quote =  program.get("quote")

        for zipcode in z_list:
            log(f"{county_names.get(zipcode)} Rate: {quote.get('rate')} APR: {quote.get('apr')} Points: {quote.get('points_credits')} Lender: {quote.get('lender')} ")

            price_params = {
                "listing_type" : program.get("listing_type"),
                "zipcode" : zipcode,
                "lender" : quote.get("lender"),
                "rate" : quote.get("rate"),
                "apr" : quote.get("apr"),
                "ltv" : program.get("ltv"),
                "points_credits" : quote.get("points_credits"),
                "interest_only" : program.get("interest_only"),
                "min_fico" : 780
            }
            result, status_code = add_dscr_price(price_params)
            if status_code == 201:
                count += 1
            else:
                status = False
                log(f"do_dscr_pricing: {result}")

    if driver is not None:
        try:
            driver.quit()
        except Exception as qe:
            log(f"Error quitting driver: {qe}")

    finish = datetime.now()
    log(f"{finish}  Finish DSCR pricing")
    time_diff = finish - start
    minutes = int(time_diff.total_seconds() / 60)
    msg = f"Total DSCR records: {count} in {minutes} minutes"
    log(msg)
    text_status(msg=msg)

    return count, status


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

            if rate is not None and apr is not None and points_credits is not None:
                pricing_data.append({
                    "rate": rate,
                    "apr": apr,
                    "lender": lender,
                    "points_credits": points_credits,  # int
                })
                    
        except Exception as e:
            log(f"Error processing row: {e}")

    return pricing_data


def parse_args():
    parser = argparse.ArgumentParser(description="Run DSCR pricing scraper.")
    parser.add_argument('--env', choices=['local', 'remote'], default='remote', help='Which environment to use')
    parser.add_argument('--zips', type=str, help='Comma-separated list of ZIP codes, e.g. 92101,90001,90620')
    return parser.parse_args()


def scrape_dscr_price(driver, url: str) -> tuple:  
    # Go Get the data
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
   
    return best_quote


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


def start_selenium_windows():
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


def start_selenium():
    options = Options()
    options.add_argument("--headless")
    service = Service(executable_path="/usr/local/bin/geckodriver")
    driver = webdriver.Firefox(service=service, options=options)
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
        load_dotenv(dotenv_path='/home/andy/PYTHON/DscrPrice/.env')
        LOCAL_DB = os.getenv("LOCAL_DB")
    elif OS_RELEASE == "6.12.25+rpt-rpi-v8":
        # Raspberry Pi
        load_dotenv(dotenv_path='/home/andys/DscrPrice/.env')
    else:
        # Windows
        load_dotenv()    

    args = parse_args()
    print(f"args.env: {args.env}")
    if args.env == 'local':
        set_server('local')
    else:
        set_server('remote')
    
    z_list = None
    if args.zips:
        z_list = [int(z.strip()) for z in args.zips.split(",")]

    print(z_list)
    dscr_pricing(z_list)


if __name__ == "__main__":
    main()
