import time
from services.database_access import add_dscr_price, add_dscr_quotes, set_server
from decimal import Decimal
from datetime import datetime, date
from services.my_logger import log
import os
import platform
from dotenv import load_dotenv
import argparse


# Scenarios - 3 scenarios for house or condo.
# Price-1: House, Min FICO 740, LTV 80%, 30 yr-fixed rate.
# Price-2: House, Min FICO 740, LTV 75%, 30 yr-fixed.
# Price-3: House, Min FICO 740, LTV 75%, 30 yr-fixed, 10 yr I/O.
# Price-4: Condo, Min FICO 740, LTV 80%, 30 yr-fixed rate.
# Price-5: Condo, Min FICO 740, LTV 75%, 30 yr-fixed.
# Price-6: Condo, Min FICO 740, LTV 75%, 30 yr-fixed, 10 yr I/O.

def dscr_pricing(z_list=None):
    # set_server('local')
    if z_list == None:
        z_list = [90620, 91901, 91708, 90001, 91319, 91701, 96701, 96703, 96708, 96704]

    start = datetime.now()
    log(f"{start}  Start pricing")
    count = 0

    house_rates = [6.750, 6.49, 6.50]
    condo_rates = [6.750, 6.124, 6.374]
    ltvs = [80, 75, 75]
    interest_onlys = [False, False, True]
    count = 0
    status = True

    for zipcode in z_list:
        for index, rate in enumerate(house_rates):
            house_params = {
                "listing_type" : "house",
                "zipcode" : zipcode,
                "lender" : "Logan Finance",
                "rate" : rate,
                "ltv" : ltvs[index],
                "interest_only" : interest_onlys[index],
                "min_fico" : 780
            }
            result, status_code = add_dscr_price(house_params)
            if status_code == 201:
                count += 1
            else:
                status = False
                log(f"do_dscr_pricing: {result}")

            condo_params = {
                "listing_type" : "condo",
                "zipcode" : zipcode,
                "lender" : "Logan Finance",
                "rate" : rate,
                "ltv" : ltvs[index],
                "interest_only" : interest_onlys[index],
                "min_fico" : 780
            }
            result, status_code = add_dscr_price(condo_params)
            if status_code == 201:
                count += 1
            else:
                status = False
                log(f"do_dscr_pricing: {result}")

    return count, status


