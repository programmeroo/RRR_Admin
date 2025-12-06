# RRR_Server API Reference

This file documents all available API endpoints, models, and server resources for use by RRR_Admin.

## Database Models (from models.py)

### Activity
- **Table**: `activities`
- **Fields**: id, contact_id, email, mls_number, activity_type, feature, action, endpoint, notes, ip_address, user_agent, created

### APILog
- **Table**: `api_logs`
- **Fields**: id, timestamp, endpoint, api_key, request_params, response_data, status_code, ip_address, user_agent

### User
- **Table**: `users`
- **Fields**: id, first_name, last_name, email, api_key, password_hash, role, created_at, quote_alerts, rate_alerts, marketing, contact_id

### Contact
- **Table**: `contacts`
- **Fields**: id, contact_type, email_address, first_name, last_name, license, phone, company, website, first_contact_date, unsubscribed_date, notes

### Listing
- **Table**: `listings`
- **Fields**: mls_number (PK), created_at, city_state, listing_type, details_url, property_address, price, beds, baths, sq_ft, zipcode, status, archive, lister_id

### Quote
- **Table**: `quotes`
- **Fields**: id, created_at, archive, property_value, loan_amount, zipcode, listing_type, loan_type, rate, apr, points_credits, origination, payment, monthly_mi, lender, priced_on, mls_number

### Email
- **Table**: `emails`
- **Fields**: id, sender, recipient_email, subject, sent_at, mls_number, template

### DailyPrice
- **Table**: `daily_prices`
- **Fields**: id, priced_on, listing_type, zipcode, loan_type, loan_amount, dp_factor, rate, apr, points_credits, lender, mi_factor, archive

### DscrDailyPrice
- **Table**: `dscr_daily_prices`
- **Fields**: id, priced_on, listing_type, zipcode, lender, rate, archive, min_fico, ltv, interest_only

### DscrQuote
- **Table**: `dscr_quotes`
- **Fields**: id, created_at, archive, mls_number, loan_amount, listing_type, lender, rate, ltv, interest_only, origination, apr, payment, priced_on

### AMILookup
- **Table**: `ami_lookup`
- **Fields**: zipcode (PK), city, state_code, county_name, single, duplex, triplex, fourplex, ami

### FHALimit
- **Table**: `fha_limits`
- **Fields**: id, state_code, county_name, single, duplex, triplex, fourplex

### ConformingLimit
- **Table**: `conforming_limits`
- **Fields**: id, normalized_type, zipcode, state_code, county_name, baseline, conforming_limit, fha_limit, va_limit

### VALimit
- **Table**: `va_limits`
- **Fields**: id, state_code, county_name, single, duplex, triplex, fourplex

## API Endpoints (from routes/api/)

### Activity Routes (`/api/activity`, `/api/activities`)
- **GET /api/activities** - List recent activities (limit parameter)
- **GET /api/activity/<id>** - Get single activity
- **POST /api/activity** - Create single activity (public, rate-limited)
- **POST /api/activities** - Create activities (bulk, or trigger extraction based on activity_type)
- **PUT /api/activity/<id>** - Update activity
- **DELETE /api/activity/<id>** - Delete activity
- **GET /api/activity/flyer_prints/preview** - Preview flyer print events from api_logs

### API Log Routes (`/api/api_log`)
- **GET /api/api_log** - Get API logs

### Archive Routes (`/api/archive/<table>`)
- **POST /api/archive/<table>** - Archive records from a table

### Contact Routes (`/api/contact`)
- **GET /api/contact** - Get all contacts
- **GET /api/contact/<id>** - Get single contact
- **POST /api/contact** - Create contact
- **PUT /api/contact/<id>** - Update contact
- **DELETE /api/contact/<id>** - Delete contact

### Listing Routes (`/api/listing`, `/api/listings`)
- **GET /api/listings** - Get listings (status parameter: new, quoted, emailed, etc.)
- **GET /api/listing/<mls_number>** - Get single listing
- **POST /api/listing** - Create listing
- **PUT /api/listing/<mls_number>** - Update listing
- **DELETE /api/listing/<mls_number>** - Delete listing

### Quote Routes (`/api/quotes`)
- **GET /api/quotes/<mls_number>** - Get quotes for listing
- **POST /api/quotes** - Generate quotes (requires listing_status parameter)

### Daily Price Routes (`/api/daily_price`, `/api/daily_prices`)
- **GET /api/daily_prices** - Get daily prices (zipcode parameter)
- **GET /api/daily_price** - Get specific daily price (zipcode, listing_type, loan_type parameters)
- **POST /api/daily_price** - Create daily price

### DSCR Routes (`/api/dscr/`)
- **GET /api/dscr/daily_prices** - Get DSCR daily prices (zipcode parameter)
- **POST /api/dscr/daily_price** - Create DSCR daily price
- **POST /api/dscr/quotes** - Generate DSCR quotes
- **POST /api/dscr/emails** - Send DSCR emails

### Email Routes (`/api/emails`)
- **POST /api/emails** - Send emails (dscr parameter for DSCR emails)

### Lookup Routes
- **GET /api/ami_first** - Get AMI data (city_state parameter)
- **GET /api/conforming_limit** - Get conforming limits (zipcode parameter)
- **GET /api/fha_limits** - Get FHA limits (county, state parameters)
- **GET /api/va_limits** - Get VA limits (county, state parameters)

### Quote URL Routes (`/api/quote_urls`)
- **GET /api/quote_urls** - Get quote URLs for pricing scraper

### User Routes (`/api/user`)
- **GET /api/user/<id>** - Get user
- **POST /api/user** - Create user
- **PUT /api/user/<id>** - Update user

### CoLister Routes (`/api/colister`)
- **POST /api/colister** - Add co-lister to listing

## Services (from services/)

### activities.py
- `add_activity(**kwargs)` - Insert single activity
- `get_activity(activity_id)` - Get single activity
- `get_activities(limit=100)` - Get recent activities with contact info (LEFT JOIN)
- `update_activity(activity_id, **kwargs)` - Update activity
- `delete_activity(activity_id)` - Delete activity
- `add_print_activities(**kwargs)` - Extract print_flyer events from api_logs (WHERE endpoint LIKE '%/print')
- `add_activities(**kwargs)` - Dispatcher (calls add_print_activities if activity_type="print_flyer")
- `preview_flyer_print_activities()` - Preview print events without inserting

### report_service.py
- `get_flyer_viewers_report()` - Get report of contacts who printed flyers

### contacts.py
- `get_contact_by_email(email)` - Lookup contact by email

### emails.py
- Email sending functions

### quotes.py
- Quote generation functions

### listings.py
- Listing management functions

### daily_prices.py
- Daily price management functions

### dscr_*.py
- DSCR-specific functions

## Database Access Functions (database_access.py)

Available functions in RRR_Admin:
- `set_server(use_server)` - Switch between local/remote
- `get_activities()` - GET /api/activities
- `add_activities(**kwargs)` - POST /api/activities
- `get_api_log()` - GET /api/api_log
- `get_listings(status)` - GET /api/listings
- `get_listing(mls_number)` - GET /api/listing/<mls>
- `get_quotes(mls_number)` - GET /api/quotes/<mls>
- `get_daily_prices(zipcode)` - GET /api/daily_prices
- And many more...

## Important Notes

### Print Flyer Workflow
1. User prints flyer on website → logged as `ui_click` activity with action `print_flyer_owner` or `print_flyer_dscr`
2. These are stored directly in `activities` table, NOT in `api_logs`
3. To find flyer printers: filter activities where `action` starts with `'print_flyer'`
4. The `add_activities(activity_type="print_flyer")` extracts from api_logs (legacy), but current prints go directly to activities

### Activity Types
- **activity_type**: `ui_click`, `print_flyer` (legacy)
- **action**: `print_flyer_owner`, `print_flyer_dscr`, `submit_form`, `view_listings`, etc.
- **feature**: `my_listings`, `dashboard`, `standard`, `dscr`, etc.

### Authentication
- All API requests require `X-API-Key` header
- API key stored in .env: `0bf1e17b-1ebe-4119-b12c-6f8f62e6eea5`

### County Zipcodes for Pricing
- Orange: 90620
- San Diego: 91901
- Riverside: 91708
- Los Angeles: 90001
- Ventura: 91319
- San Bernardino: 91701
- Honolulu: 96701
- Kauai: 96703
- Maui: 96708
- Hawaii: 96704
