import requests
import os
from decimal import Decimal
from datetime import datetime
import platform
from dotenv import load_dotenv
# from services.my_logger import log



OS_RELEASE = platform.release()

if OS_RELEASE == "5.10.16.3-microsoft-standard-WSL2":
    # WSL Ubuntu
    load_dotenv(dotenv_path='/home/andy/PYTHON/ScrapePrice/.env')
elif OS_RELEASE == "6.12.25+rpt-rpi-v8":
    # Raspberry Pi
    load_dotenv(dotenv_path='/home/andys/ScrapePrice/.env')
else:
    # Windows
    load_dotenv()


API_KEY = os.getenv("API_KEY")
headers = {"X-API-Key": API_KEY}

LOCAL_DB = os.getenv("LOCAL_DB")
REMOTE_DB = os.getenv("REMOTE_DB")

# Initialize SERVER_DB with local as default
SERVER_DB = LOCAL_DB if LOCAL_DB else REMOTE_DB


def set_server(use_server="local"):
    global SERVER_DB
    if use_server == "local":
        SERVER_DB = LOCAL_DB
    else:
        SERVER_DB = REMOTE_DB
    # lo
    # g(f"Using SERVER_DB: {SERVER_DB}")


def _request(method, endpoint, **kwargs):
    """Helper to make safe API requests with error handling"""
    try:
        url = f"{SERVER_DB}{endpoint}"
        print(f"method: {method} endpoint: {endpoint} kwargs: {kwargs}")
        # using DELETE casues the IDE editor to get weird
        if method == "REMOVE":
            response = requests.delete(url=url, headers=headers, **kwargs)
        else:
            response = requests.request(method, url, headers=headers, **kwargs)
        return return_response(endpoint, response)
    except requests.exceptions.RequestException as e:
        print(f"API Connection Error accessing {endpoint}: {e}")
        return f"Connection Error: {str(e)}", 503


def add_activity(**kwargs):
    params = {key: to_json_serializable(value) for key, value in kwargs.items()}
    return _request("POST", "activity", json=params)


def add_activities(**kwargs):
    params = {key: to_json_serializable(value) for key, value in kwargs.items()}
    return _request("POST", "activities", json=params)


def add_contact(lister):
    return _request("POST", "contact", json={
        "contact_type": "Agent",
        "email_address": lister["email_address"],
        "first_name": lister["first_name"],
        "last_name": lister["last_name"],
        "license": lister["license"],
        "phone": lister["phone"],
        "company": lister["company"]
    })


def add_colister(mls_number, colister_id):
    return _request("POST", "colister", json={
        "mls_number": mls_number,
        "contact_id": colister_id
    })


def add_affordability_emails(**kwargs):
    params = {key: to_json_serializable(value) for key, value in kwargs.items()}
    return _request("POST", "affordability_emails", json=params)


def add_affordability_reports(**kwargs):
    params = {key: to_json_serializable(value) for key, value in kwargs.items()}
    return _request("POST", "affordability_reports", json=params)


def add_daily_price(**kwargs):
    params = {key: to_json_serializable(value) for key, value in kwargs.items()}
    return _request("POST", "daily_price", json=params)


def add_dscr_price(params_dict):
    params = {key: to_json_serializable(value) for key, value in params_dict.items()}
    return _request("POST", "dscr/daily_price", json=params)


def add_dscr_quotes(listing_status=None):
    return _request("POST", "dscr/quotes", json={"listing_status": listing_status})


def add_emails(**kwargs):
    params = {key: to_json_serializable(value) for key, value in kwargs.items()}
    return _request("POST", "emails", json=params)


def add_listing_dict(params_dict=None):
    params = {key: to_json_serializable(value) for key, value in params_dict.items()}
    return _request("POST", "listing", json=params)


def add_quote(**kwargs):
    params = {key: to_json_serializable(value) for key, value in kwargs.items()}
    return _request("POST", "quote", json=params)


def add_quotes(**kwargs):
    params = {key: to_json_serializable(value) for key, value in kwargs.items()}
    return _request("POST", "quotes", json=params)


def add_quote_dict(params_dict=None):
    params = {key: to_json_serializable(value) for key, value in params_dict.items()}
    return _request("POST", "quote", json=params)


def archive_table(table=None, days_old=None):
    params = {"days": days_old}
    return _request("POST", f"archive/{table}", json=params)


def delete_archive(table):
    return _request("REMOVE", f"archive/{table}")


def get_ami_first(city_state=None):
    return _request("GET", "ami_first", params={"city_state": city_state})


def get_activities(page=1, per_page=100):
    params = {"page": page, "per_page": per_page}
    return _request("GET", "activities", params=params)


def get_api_log(**kwargs):
    params = {key: to_json_serializable(value) for key, value in kwargs.items()}
    return _request("GET", "api_log", params=params)


def get_api_logs_summary():
    return _request("GET", "api_logs_summary", params=None)


def get_archive(table=None):
    return _request("GET", f"archive/{table}", params=None)


def get_conforming_limit(zipcode=None, normalized_type=None):
    params = {
        "zipcode": zipcode,
        "normalized_type": normalized_type}
    return _request("GET", "conforming_limit", params=params)


def get_contact(email_address=None):
    return _request("GET", "contact", params={"email_address": email_address})


def get_contacts(**kwargs):
    params = {key: to_json_serializable(value) for key, value in kwargs.items()}
    return _request("GET", "contacts", params=params)


def get_contacts_summary():
    return _request("GET", "contacts_summary", params=None)


def get_daily_price(zipcode=None, listing_type=None, loan_type=None):
    params = {
        "zipcode": zipcode,
        "listing_type": listing_type,
        "loan_type": loan_type}
    return _request("GET", "daily_price", params=params)


def get_daily_prices(zipcode=None, listing_type=None):
    params = {
        "zipcode": zipcode,
        "listing_type": listing_type}
    return _request("GET", "daily_prices", params=params)


def get_dscr_prices(zipcode=None, listing_type=None):
    params = {
        "zipcode": zipcode,
        "listing_type": listing_type}
    return _request("GET", "dscr/daily_prices", params=params)


def get_print_activities():
    return _request("GET", "print_activities")


def get_listing(mls_number=None):
    return _request("GET", f"listing/{mls_number}")


def get_listings(**kwargs):
    params = {key: to_json_serializable(value) for key, value in kwargs.items()}
    return _request("GET", "listings", params=params)


def get_listing_page_views(**kwargs):
    params = {key: to_json_serializable(value) for key, value in kwargs.items()}
    return _request("GET", "listing_page_views", params=params)


def get_listings_summary():
    return _request("GET", f"listings_summary")


def get_quotes(mls_number=""):
    return _request("GET", f"quotes/{mls_number}")


def get_dscr_quotes(mls_number=""):
    return _request("GET", f"dscr/quotes/{mls_number}")


def get_quote_urls(zipcode=None, listing_type=None):
    params = {
        "zipcode": zipcode,
        "listing_type": listing_type
    }
    return _request("GET", "quote_urls", params=params)


def get_web_log(**kwargs):
    params = {key: to_json_serializable(value) for key, value in kwargs.items()}
    return _request("GET", "web_log", params=params)


def purge_api_log(before):
    return _request("REMOVE", "api_log", params={"before": before})

   
def return_response(function, response):
    try:
        response.raise_for_status()  # raises error for 4xx or 5xx
        # try parsing JSON
        return response.json(), response.status_code

    except requests.exceptions.HTTPError as e:
        return response.text, response.status_code

    except requests.exceptions.JSONDecodeError as e:
        return response.text, response.status_code

    except requests.exceptions.RequestException as e:
        print(f"API Connection Error in {function}: {e}")
        return f"Connection Error: {str(e)}", 503


def to_json_serializable(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return obj
 

def unsubscribe_contact(email):
    print(f"unsubscribe: {email}")
    return _request("PUT", "contact", json={"email_address": email})

    
def update_listing(**kwargs):
    params = {}
    for key, value in kwargs.items():
        params[key] = value    
    return _request("PUT", "listing", json=params)


###################################################################################
# ### TEST FUNCTIONS  ###
###################################################################################

# set_server("local")
# set_server("remote")
# today = datetime.now().date()
# print(today)
# data = {}
# status_code = 0

# data, status_code = get_contacts_summary()
# data, status_code = get_api_logs_summary()
# data, status_code = get_listings_summary()

# data, status_code = add_affordability_reports(status="dscr_emailed")

# data, status_code = add_affordability_emails(debug=True, max_send_count=2)

# data, status_code = add_affordability_emails(debug=True)

# data, status_code = add_activity(activity_type="print_flyer")

# data, status_code = add_activity(activity_type="print_flyer")

# data, status_code = get_print_activities()

# data, status_code = unsubscribe_contact("andiego.code@gmail.com")
# if len(data) > 0:
#     print(f"data:{data} status_code:{status_code}")
# data, status_code = add_contact(lister)
# data, status_code = add_colister(mls_number, colister)
# data, status_code = add_daily_price(normalized_type="single", zipcode=92708, loan_type="va", dp_factor=0, rate=5.25, apr=6.75, points_credits=325, lender="billy bob lending", mi_factor=0.0003)

# data, status_code = add_emails(debug=False, dscr=False, max_send_count=25)

# params = { "mls_number": "OC00000445", "city_state": "costa-mesa-ca", "listing_type": "house", "details_url": "https://some_url", "property_address": "1234 main street", "price": 499999, "beds": 3, "baths": 2, "sq_ft": 1500, "zipcode": 92704, "quoted": False, "status": "new", "attachment_type": "attached", "units": 1, "lister_id": 1}        
# data, status_code = add_listing_dict(params)
# data, status_code = get_activities()
# data, status_code = get_ami_first(city_state="kapolei-hi")
# data, status_code = get_api_log()
# data, status_code =  get_daily_price(zipcode=96704, listing_type="condo", loan_type='conventional-5')
# data, status_code =  get_daily_prices(zipcode=96701)
# data, status_code =  get_dscr_prices(zipcode=96701)
# data, status_code = get_flyer_viewers()
# data, status_code =  get_listing(mls_number='202501952')
# data, status_code =  get_listings(status='new')
# data, status_code = get_quotes(mls_number='202501952')
# data, status_code = get_dscr_quotes(mls_number='202501952')
# data, status_code = purge_daily_prices()
 # data, status_code = purge_api_log(before=today)
# data, status_code = get_conforming_limit(zipcode=90001, normalized_type="single")

# print(data)




