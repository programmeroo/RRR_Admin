# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RateReadyRealtor is a mortgage marketing automation system for real estate agents. The **Client App** (this repository) is a Tkinter-based desktop automation tool that runs locally on Windows, scrapes real estate listings, generates mortgage quotes, and sends flyers to real estate agents.

**Critical Distinction**: This is the CLIENT APP, not the Server App. The Server App hosts the website, API, and database. Never mix responsibilities between these two codebases.

## Architecture

### Client/Server Separation

**Client App (this repository):**
- Tkinter GUI desktop application
- Reads/scrapes saved Homes.com HTML pages
- Calls Server App API for all database operations
- Triggers quotes and emails via API
- Runs automated workflow tasks
- Manages logs and file processing

**Server App (separate repository):**
- Hosts website at ratereadyrealtor.com
- Flask API server
- MySQL database
- Generates quotes from LoanFactory pricing
- Sends emails to agents
- Stores listings, contacts, quotes, daily prices, DSCR data

**Communication**: All database operations flow through `database_access.py` which makes REST API calls to either LOCAL_DB or REMOTE_DB.

### Core Components

**Entry Points:**
- `rate_ready_gui.py` - Tkinter GUI, main user interface
- `rate_ready_realtor.py` - Workflow orchestration and task definitions
- `run.py` - Simple launcher script

**Data Flow:**
1. **Scraping**: `scrape_homes.py` → Downloads folder → `pages/` folder
2. **Processing**: `process_listings.py` → Extract listing data → API → Database
3. **Pricing**: `scrape_pricing.py` (OO loans) or `dscr_pricing.py` (investment loans) → Selenium scraping → API → Database
4. **Quoting**: API generates quotes by matching listings with pricing
5. **Email**: API sends flyers to agents

**API Client**: `database_access.py`
- All functions return `(data, status_code)` tuples
- Use `set_server("local")` or `set_server("remote")` to switch environments
- Handles JSON serialization of Decimals and datetime objects

**Logging**: `my_logger.py`
- Centralized logging with timestamps
- Logs to `./logs/log_YYYYMMDD.txt` by default
- Use `log("message")` throughout the codebase
- Logger singleton instance created at module level
- GUI can override log filename via `log.set_logfile(filename)`

**File Locations:**
- **Pages (input)**: `C:/LOCAL_PROJECTS/RateReadyRealtor/pages/` (old path) or `C:/LOCAL_PROJECTS/RRR_LOGS/pages/` (current path)
- **Processed HTML**: `C:/LOCAL_PROJECTS/RRR_LOGS/processed/`
- **Failed HTML**: `C:/LOCAL_PROJECTS/RRR_LOGS/failed/`
- **Logs**: `C:/LOCAL_PROJECTS/RateReadyRealtor/logs/` or `C:/LOCAL_PROJECTS/RRR_LOGS/logs/`
- **Archives**: `C:/LOCAL_PROJECTS/RateReadyRealtor/archive/archive_YYYYMMDD_HHMM/`
- **Source Downloads**: `~/Downloads/pages/`
- **Download Backups**: `~/Downloads/backups/pages_YYYYMMDD_HHMMSS/`

### Workflow Engine

The workflow engine in `rate_ready_realtor.py` orchestrates sequential task execution. Each task is a decorated function with the `@monitor_task` decorator.

**Standard Workflow Order:**
1. `do_pricing()` - Scrape mortgage rates from LoanFactory
2. `do_scrape()` - Copy and rename HTML files from Downloads
3. `do_process_pages()` - Extract listings and agents from HTML
4. `do_quote()` - Generate conventional/FHA/VA quotes via API
5. `do_email()` - Send flyers to agents via API
6. `do_dscr_pricing()` - Add DSCR (investment loan) pricing
7. `do_dscr_quote()` - Generate DSCR quotes via API
8. `do_dscr_email()` - Send DSCR flyers via API
9. `do_archive()` - Export database tables to CSV
10. `do_clean_up()` - Purge old data from archive tables

**Workflow Execution:**
- Tasks execute via `do_start(workflow=workflow)` which iterates through the workflow list
- Use `set_quote_listing_status("new"|"active"|"all")` to control which listings get quoted
- Email tasks accept `debug=True` to test without sending actual emails

## Development Commands

### Virtual Environment Activation (PowerShell)
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Unrestricted -Force
C:\Users\andys\Documents\LOCAL_PROJECTS\RateReadyRealtor\.venv\Scripts\Activate.ps1
```

### Running the Application
```bash
python rate_ready_gui.py
# or
python run.py
```

### Running Individual Tasks (for testing)
```python
from database_access import set_server
from rate_ready_realtor import do_pricing

set_server("local")  # Use local server for testing
do_pricing()
```

### Testing Specific Zip Codes
```bash
python scrape_pricing.py --env local --zips 92708,90001,96701
```

## File Processing Workflow

**Scraping Workflow** (`scrape_homes.py`):
1. Backup existing pages: `~/Downloads/pages` → `~/Downloads/backups/pages_TIMESTAMP`
2. Copy HTML files: `~/Downloads/pages` → `C:/LOCAL_PROJECTS/RateReadyRealtor/pages`
3. Rename files using canonical URL from HTML
4. Remove non-property files
5. Return count of property files ready to process

**Processing Workflow** (`process_listings.py`):
- Reads HTML files from `C:/LOCAL_PROJECTS/RRR_LOGS/pages`
- Extracts listing details and agent information from JSON-LD structured data
- Creates contacts and listings via API
- Success: moves to `C:/LOCAL_PROJECTS/RRR_LOGS/processed`
- Failure: moves to `C:/LOCAL_PROJECTS/RRR_LOGS/failed`

## Pricing and Loan Programs

### OO Loan Programs (Conventional/FHA/VA)
`scrape_pricing.py` scrapes LoanFactory Direct for owner-occupied loans:
- **conventional-20**: 20% down
- **conventional-5**: 5% down
- **high balance-20**: High balance conforming, 20% down
- **high balance-5**: High balance conforming, 5% down
- **fha**: FHA minimum down (3.5%)
- **va**: VA 0% down
- **jumbo**: Jumbo 20% down

### DSCR Loan Programs (Investment Properties)
`dscr_pricing.py` uses hardcoded rates from Logan Finance:
- 3 scenarios per property type (house/condo)
- LTV options: 80%, 75%, 75% with 10-year interest-only
- Min FICO: 780

**Target Counties/Zip Codes:**
- Orange County: 90620
- San Diego: 91901
- Riverside: 91708
- Los Angeles: 90001
- Ventura: 91319
- San Bernardino: 91701
- Honolulu: 96701
- Kauai: 96703
- Maui: 96708
- Hawaii (Big Island): 96704

## API Endpoints Reference

All API endpoints are accessed through `database_access.py`. Each function returns a tuple: `(data, status_code)`.

**Authentication:**
- All requests include `X-API-Key` header from environment variable `API_KEY`
- Server selection via `set_server("local"|"remote")`

### Activity Endpoints

| Function | HTTP Method | Endpoint | Purpose | Parameters |
|----------|-------------|----------|---------|------------|
| `add_activity()` | POST | `/api/activity` | Log system activity | `**kwargs` - activity_type, etc. |
| `get_activities()` | GET | `/api/activities` | Retrieve all activities | None |

### Contact Endpoints

| Function | HTTP Method | Endpoint | Purpose | Parameters |
|----------|-------------|----------|---------|------------|
| `add_contact(lister)` | POST | `/api/contact` | Create new contact (agent) | contact_type, email_address, first_name, last_name, license, phone, company |
| `unsubscribe_contact(email)` | PUT | `/api/contact` | Unsubscribe contact from emails | email_address |

### Listing Endpoints

| Function | HTTP Method | Endpoint | Purpose | Parameters |
|----------|-------------|----------|---------|------------|
| `add_listing_dict(params_dict)` | POST | `/api/listing` | Create new listing | mls_number, city_state, listing_type, details_url, property_address, price, beds, baths, sq_ft, zipcode, lister_id |
| `get_listing(mls_number)` | GET | `/api/listing/{mls_number}` | Get single listing by MLS | mls_number |
| `get_listings(**kwargs)` | GET | `/api/listings` | Query listings | status (new/active/all), etc. |
| `update_listing(**kwargs)` | PUT | `/api/listing` | Update existing listing | mls_number + fields to update |
| `add_colister(mls_number, colister_id)` | POST | `/api/colister` | Link co-listing agent | mls_number, contact_id |

### Pricing Endpoints (OO Loans)

| Function | HTTP Method | Endpoint | Purpose | Parameters |
|----------|-------------|----------|---------|------------|
| `add_daily_price(**kwargs)` | POST | `/api/daily_price` | Add conventional/FHA/VA pricing | listing_type, zipcode, loan_type, loan_amount, dp_factor, rate, apr, points_credits, lender, mi_factor |
| `get_daily_price(zipcode, listing_type, loan_type)` | GET | `/api/daily_price` | Get single daily price | zipcode, listing_type, loan_type |
| `get_daily_prices(zipcode, listing_type)` | GET | `/api/daily_prices` | Get all daily prices for zip/type | zipcode, listing_type (optional) |
| `get_quote_urls(zipcode, listing_type)` | GET | `/api/quote_urls` | Get LoanFactory URLs for scraping | zipcode, listing_type |
| `get_conforming_limit(zipcode, normalized_type)` | GET | `/api/conforming_limit` | Get conforming loan limit | zipcode, normalized_type |

### DSCR Pricing Endpoints (Investment Loans)

| Function | HTTP Method | Endpoint | Purpose | Parameters |
|----------|-------------|----------|---------|------------|
| `add_dscr_price(params_dict)` | POST | `/api/dscr/daily_price` | Add DSCR pricing | listing_type, zipcode, lender, rate, ltv, interest_only, min_fico |
| `get_dscr_prices(zipcode, listing_type)` | GET | `/api/dscr/daily_prices` | Get DSCR prices for zip/type | zipcode, listing_type |

### Quote Endpoints

| Function | HTTP Method | Endpoint | Purpose | Parameters |
|----------|-------------|----------|---------|------------|
| `add_quote(**kwargs)` | POST | `/api/quote` | Add single quote | mls_number, loan_type, etc. |
| `add_quotes(**kwargs)` | POST | `/api/quotes` | Generate quotes for listings | listing_status (new/active/all) |
| `add_dscr_quotes(listing_status)` | POST | `/api/dscr/quotes` | Generate DSCR quotes | listing_status (new/active/all) |
| `get_quotes(mls_number)` | GET | `/api/quotes/{mls_number}` | Get OO quotes for listing | mls_number |
| `get_dscr_quotes(mls_number)` | GET | `/api/dscr/quotes/{mls_number}` | Get DSCR quotes for listing | mls_number |

### Email Endpoints

| Function | HTTP Method | Endpoint | Purpose | Parameters |
|----------|-------------|----------|---------|------------|
| `add_emails(**kwargs)` | POST | `/api/emails` | Send batch of flyers | debug (bool), dscr (bool), max_send_count |

### Archive & Maintenance Endpoints

| Function | HTTP Method | Endpoint | Purpose | Parameters |
|----------|-------------|----------|---------|------------|
| `archive_table(table, days_old)` | POST | `/api/archive/{table}` | Archive old records | table, days |
| `get_archive(table)` | GET | `/api/archive/{table}` | Retrieve archived data | table |
| `delete_archive(table)` | DELETE | `/api/archive/{table}` | Purge archive table | table |
| `get_api_log()` | GET | `/api/api_log` | Get API request log | None |
| `purge_api_log(before)` | DELETE | `/api/api_log` | Delete old API logs | before (date) |

### Utility Endpoints

| Function | HTTP Method | Endpoint | Purpose | Parameters |
|----------|-------------|----------|---------|------------|
| `get_ami_first(city_state)` | GET | `/api/ami_first` | Get AMI first-time buyer data | city_state |
| `get_flyer_viewers()` | GET | `/api/flyer_viewers` | Get flyer view analytics | None |

## API Response Patterns

All API functions return `(data, status_code)`:

**Success Patterns:**
- `200` - GET success (returns data)
- `201` - POST/PUT success (created/updated)
- `404` - Resource not found

**Error Handling:**
```python
response, status_code = get_listing(mls_number="12345")
if status_code == 200:
    # Listing found
    listing_data = response
elif status_code == 404:
    # Listing not found
    print(response)  # error message text
```

**JSON Serialization:**
- `to_json_serializable()` converts Decimal to float for API transmission
- Datetime objects are automatically handled by requests library

## Important Constraints

### Do NOT:
- Create new workflow tasks without explicit request
- Rename existing workflow task functions
- Modify API request signatures without confirming Server App compatibility
- Mix quoting logic into Client App (quoting is API-driven)
- Add business logic that belongs in Server App
- Create new files unless absolutely necessary

### DO:
- Maintain separation between Client App and Server App responsibilities
- Use `set_server("local")` for development/testing
- Use `set_server("remote")` for production
- Test with `debug=True` for email tasks
- Preserve existing logger and workflow patterns
- Use complete file outputs (not patches) for Tkinter UI updates
- Maintain two blank lines between functions
- Use cross-platform paths when possible (for future Linux migration)

## Configuration

**Environment Variables** (`.env`):
- `API_KEY` - Server API authentication
- `LOCAL_DB` - Local server URL (http://192.168.1.181:5000/api/)
- `REMOTE_DB` - Production server URL (http://www.ratereadyrealtor.com/api/)
- Twilio credentials for SMS notifications

**Platform Detection** (`database_access.py`, `scrape_pricing.py`):
- Windows: Default `.env` load
- WSL Ubuntu: `/home/andy/PYTHON/ScrapePrice/.env`
- Raspberry Pi: `/home/andys/ScrapePrice/.env`

## Dependencies

From `requirements.txt`:
- `pandas` - Data manipulation
- `bs4` (BeautifulSoup) - HTML parsing
- `numpy` - Numerical operations
- `requests` - HTTP API calls
- `python-dotenv` - Environment configuration
- `selenium` - Web scraping (LoanFactory pricing)

Additional runtime requirements:
- Chrome/ChromeDriver for Selenium (headless mode)
- Tkinter (included with Python on Windows)
