# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the **RateReadyRealtor Server App**, a Flask web application that serves as both a public website (ratereadyrealtor.com) and REST API for mortgage quote generation and delivery to real estate agents. It's part of a larger ecosystem that includes a Tkinter Client App (desktop automation) and a Raspberry Pi Daily Pricing scraper.

## Running the Application

```bash
# Start the Flask development server
python flask_app.py
# Runs on http://192.168.1.181:5000 (development) or https://www.ratereadyrealtor.com (production)

# Environment selection via FLASK_ENV variable
# production → ProductionConfig (PythonAnywhere MySQL)
# default → DevelopmentConfig (local MySQL)
```

**Database Bootstrap:**
- On first run, `bootstrap_app()` executes automatically
- Creates tables, admin user, and imports lookup data from CSV files in `lookup/`
- Creates 5 SQL views for data aggregation
- No manual migration commands needed

**Environment Variables Required:**
See `.env` file - key variables include database URIs, MailGun credentials, IDrive S3 keys, reCAPTCHA keys, and API authentication keys.

## Architecture Overview

### Request Flow Patterns

**Blueprint Registration:**
All blueprints export a `blueprints` list from `routes/api/__init__.py` and `routes/web/__init__.py`. The main app imports and registers them in bulk:
```python
from routes.api import blueprints as api_blueprints
for bp in api_blueprints:
    app.register_blueprint(bp)
```

**Service Layer Pattern:**
Routes should NEVER contain business logic. Always delegate to service modules:
```
Route Handler → Service Function → Model → Database
```
Services are pure functions that receive parameters (not request objects) and return data or raise exceptions. They use `db.session` from extensions but don't manage HTTP concerns.

**Dual Response Types:**
- API routes (`routes/api/`) return JSON via `jsonify()` with HTTP status codes
- Web routes (`routes/web/`) return HTML via `render_template()` with flash messages

### Authentication

**Two parallel systems:**
1. **API Key** (for external clients): Decorator `@authenticate_request` checks `X-API-Key` header against hashed `User.api_key`
2. **Flask-Login** (for web users): Decorator `@login_required` checks session cookie

Admin-only routes use `@admin_required` which checks `current_user.role == 'admin'`.

### Database Model Relationships

**Core entities:**
- `Listing` (MLS number as primary key) → many `Quote` + many `DscrQuote` + many `Email`
- `Contact` (realtor/agent) → many `Listing` (as lister) + optional one `User`
- `CoLister` joins additional contacts to listings (many-to-many)
- `DailyPrice` and `DscrDailyPrice` store county-normalized pricing (not per-zipcode)

**Archival pattern:**
Quotes and prices use `archive=True` flag rather than deletion. When new quotes/prices are generated, previous records are flagged archived. This maintains history without cluttering active queries.

**Status lifecycle:**
```
Listing: new → quoted → emailed → [sold/archived]
              ↓
         no_quotes

         new → dscr_quoted → dscr_emailed → [sold/archived]
              ↓
         no_dscr_quotes
```

## Quote Generation Workflow

**Conventional Quotes** (`services/quotes.py`):
1. `listing_quotes(listing)` orchestrates generation of 4 potential quotes:
   - 20% down conventional
   - 5% down conventional
   - FHA (3.5% down)
   - VA (0% down)
2. For each: `build_quote()` checks conforming limits by zipcode, calculates loan amount, fetches daily pricing, calculates P&I payment and PMI
3. Loan program waterfall: conforming → high balance (not in Hawaii) → jumbo (20% only)
4. `create_quote()` inserts with `archive=False`, previous quotes flagged `archive=True`
5. Listing status updated to "quoted"

**DSCR Quotes** (`services/dscr_quotes.py`):
Simpler investor-focused workflow with 3 fixed scenarios:
- LTV 80%, P&I
- LTV 75%, P&I
- LTV 75%, Interest-Only

No income/employment verification. Uses `DscrDailyPrice` table. APR calculated with 1% origination + $1495 lender fee.

**Pricing Lookups:**
Both quote types use `daily_price_wrapper()` which normalizes zipcodes to the first zipcode in each county. This reduces database size (one price per county vs. thousands of zipcodes).

## Email Workflow

**Batch Processing** (`services/email_processor.py`):
1. Query `listing_page_view` for status="quoted" or "dscr_quoted"
2. Generate HTML from Jinja2 templates (`quote_email.html` or `dscr_quote_email.html`)
3. Send via MailGun API (`services/email_service.py`)
4. Send to both lister and colister (if exists)
5. Update status to "emailed"/"dscr_emailed"
6. Rate limit: max 25 emails per batch, 0.5s sleep between sends
7. Errors set status to "error"/"dscr_error" for retry

**Email Logging:**
Every sent email logged to `Email` table with template name, recipients, and timestamp.

## Activity Tracking

**New feature** (recently implemented):
- Captures user interactions via POST to `/api/activity` (no auth, rate limited 60/min)
- Tracks: page views, button clicks, print flyer downloads, login/logout
- Stores: ip_address, user_agent, contact_id, mls_number, activity_type, feature, action
- Bulk extraction: `add_print_activities()` retroactively parses `/print` calls from `api_logs`

**Implementation in templates:**
Frontend JavaScript posts activity events. Always include ip_address and user_agent (auto-captured by route handler).

## Key Conventions

**Service naming:**
- `get_{entity}()` - single record
- `get_{entities}()` - multiple records
- `create_{entity}()` - insert
- `update_{entity}()` - modify
- `build_{entity}()` - complex construction
- `add_or_update_{entity}()` - upsert

**Error handling:**
Services raise exceptions; routes catch and convert to flash messages (web) or JSON errors (API). Always rollback on database errors.

**Property type normalization:**
Use `services/normalize.py` to convert raw listing types (e.g., "Home", "Condo", "Duplex") to normalized types ("single", "duplex", etc.) for conforming limit lookups.

**County-based pricing:**
When querying `DailyPrice` or `DscrDailyPrice`, always use `daily_price_wrapper()` to normalize zipcode. Never query by raw zipcode unless you've verified it's the county representative zipcode.

## Deployment

**Production:** PythonAnywhere ($12/month tier)
- WSGI configuration points to `flask_app.py`
- MySQL database: `programmeroo$rate_ready`
- Driver: `mysqldb` (C-based, faster than pymysql)
- Virtual environment: `/home/programmeroo/.virtualenvs/listingsenv`

**Domain enforcement:**
`@app.before_request` redirects `ratereadyrealtor.com` → `www.ratereadyrealtor.com` (301 permanent).

**External dependencies:**
- MailGun for email delivery
- IDrive E2 (S3-compatible) for media files via boto3
- Google reCAPTCHA on contact form

## Important Files

**Initialization:**
- `flask_app.py` - Application entry point, blueprint registration, before/after request hooks
- `config.py` - Environment-specific configuration (DevelopmentConfig vs ProductionConfig)
- `extensions.py` - Flask extension initialization (db, login_manager, cors)
- `database.py` - Database connection setup with pooling

**Data seeding:**
- `lookup/ami_lookup.csv` - Area Median Income by zipcode
- `lookup/fha_limits_2025.csv` - FHA loan limits by county
- `lookup/va_county_loan_limits_2025.csv` - VA loan limits by county
- Conforming limits calculated from FHA/VA data (baseline + delta)

**Views:**
Database views created in `services/bootstrap.py`:
- `listing_page_view` - Complete listing data with contacts (used everywhere)
- `unemailed_quotes_view` - Pending conventional emails
- `unemailed_dscr_quotes_view` - Pending DSCR emails
- `listing_card_view` - UNION-based view separating QM and DSCR quotes for public listings page
- `colister_view` - CoLister joins with contact info

**No test suite:**
Testing is manual. Use DEMO123 listing for UI testing (defined in `public_routes.py`). External Tkinter Client App used for API testing.

## Working with This Codebase

**When adding new routes:**
1. Create route handler in appropriate blueprint file
2. Add business logic to corresponding service module
3. Use existing patterns (jsonify for API, render_template for web)
4. Add API logging automatically captured by `@app.after_request` hook

**When modifying quote generation:**
Conventional and DSCR workflows are completely separate. Changes to one shouldn't affect the other. Both rely on daily pricing tables being up-to-date (updated by Raspberry Pi scraper).

**When adding new lookup data:**
Update CSV files in `lookup/` directory, then run bootstrap (or add targeted import function). Don't manually insert into lookup tables.

**When debugging email issues:**
Check `Email` table for sent logs, `Listing.status` for workflow state, and MailGun dashboard for delivery status. Email service has debug mode that redirects all emails to developer address.

**Connection pooling:**
Database uses `pool_pre_ping=True` and `pool_recycle=28000` to handle connection timeouts. If you see "MySQL server has gone away", these settings should prevent it.

## System Context

This server app is one of four applications in the RateReadyRealtor ecosystem:
1. **This app** - Public website + API + database
2. **Client App** (Tkinter) - Internal automation tool for scraping Homes.com and triggering workflows
3. **Daily Pricing App** (Raspberry Pi) - Automated LoanFactory scraper that updates pricing tables
4. **Mortgage Marketing Engine** - Social media automation (separate, uses Make.com)

The Client App and Daily Pricing App both authenticate via API keys and push data to this server. This server never initiates connections to external clients - it only responds to HTTP requests.
