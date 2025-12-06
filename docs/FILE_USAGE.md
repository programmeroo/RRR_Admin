# RRR_Admin File Usage Analysis

## ✅ ACTIVELY USED FILES

### Core Application Files

| File | Status | Purpose |
|------|--------|---------|
| `app.py` | ✅ USED | Main Flask application entry point |
| `config.py` | ✅ USED | Configuration classes (Development/Production) |
| `.env` | ✅ USED | Environment variables (API keys, URLs) |
| `requirements.txt` | ✅ USED | Python dependencies |
| `README.md` | ✅ USED | Documentation |

### Routes (Blueprint Registration)

| File | Status | Purpose |
|------|--------|---------|
| `routes/__init__.py` | ✅ USED | Exports blueprints list for app registration |
| `routes/admin_routes.py` | ✅ USED | Dashboard, listings, quotes, contacts, prices |
| `routes/workflow_routes.py` | ✅ USED | Workflow execution and status |

### Services (Business Logic & Workflows)

| File | Status | Purpose |
|------|--------|---------|
| `services/workflow_runner.py` | ✅ USED | Background workflow engine with threading |
| `services/database_access.py` | ✅ USED | API client - all database operations via REST |
| `services/process_listings.py` | ✅ USED | Parse HTML files, extract listings |
| `services/scrape_homes.py` | ✅ USED | Copy HTML files from Downloads |
| `services/scrape_pricing.py` | ✅ USED | Scrape LoanFactory for OO loan rates |
| `services/dscr_pricing.py` | ✅ USED | DSCR (investment) loan pricing |
| `services/my_logger.py` | ✅ USED | Logging utility |

### Templates (Currently Used)

| File | Status | Purpose |
|------|--------|---------|
| `templates/admin/base.html` | ✅ USED | Base template with sidebar navigation |
| `templates/admin/dashboard.html` | ✅ USED | Main dashboard with stats and API switcher |
| `templates/admin/workflows.html` | ✅ USED | Workflow management UI |
| `templates/admin/user_activity.html` | ✅ USED | Flyer viewer tracking (needs implementation) |
| `templates/admin/listings.html` | ✅ USED | Listings view (needs implementation) |
| `templates/admin/quotes.html` | ✅ USED | Quotes view (needs implementation) |
| `templates/admin/contacts.html` | ✅ USED | Contacts view (needs implementation) |
| `templates/admin/daily_prices.html` | ✅ USED | Daily prices view (needs implementation) |

---

## ❌ NOT USED / SHOULD BE REMOVED OR MOVED

### Root Files (Copied from RRR_Server but not needed)

| File | Status | Reason |
|------|--------|--------|
| `extensions.py` | ❌ NOT USED | Was for SQLAlchemy/Flask-Login - we don't use DB |
| `auth_decorators.py` | ❌ NOT USED | Was for Flask-Login - we don't have user auth |
| `limit_utils.py` | ❌ NOT USED | Conforming limit lookups - done via API |
| `serializers.py` | ❌ NOT USED | JSON serialization - handled by database_access |
| `utils.py` | ❌ NOT USED | Generic utilities from RRR_Server |

### Services (Not Used in Admin App)

| File | Status | Reason |
|------|--------|--------|
| `services/rate_ready_gui.py` | ❌ NOT USED | TKinter GUI - this is the web replacement |
| `services/rate_ready_realtor.py` | ❌ NOT USED | Old workflow - replaced by workflow_runner.py |

### Templates (Old/Unused - from RRR_Server copy)

| File | Status | Reason |
|------|--------|--------|
| `templates/base.html` | ❌ NOT USED | Old base - using `templates/admin/base.html` |
| `templates/affordability.html` | ❌ NOT USED | Public website feature (belongs in RRR_Server) |
| `templates/change_password.html` | ❌ NOT USED | User management (belongs in RRR_Server) |
| `templates/custom_listing.html` | ❌ NOT USED | Public website feature |
| `templates/dscr_calculator.html` | ❌ NOT USED | Public website feature |
| `templates/listings.html` | ❌ NOT USED | Public website feature |
| `templates/login.html` | ❌ NOT USED | User auth (belongs in RRR_Server) |
| `templates/programs_owner.html` | ❌ NOT USED | Public website feature |
| `templates/quote.html` | ❌ NOT USED | Public website feature |
| `templates/quote_print.html` | ❌ NOT USED | Public website feature |
| `templates/quote_table.html` | ❌ NOT USED | Public website feature |
| `templates/rates.html` | ❌ NOT USED | Public website feature |
| `templates/rates_table.html` | ❌ NOT USED | Public website feature |
| `templates/request_password_reset.html` | ❌ NOT USED | User management |
| `templates/reset_password.html` | ❌ NOT USED | User management |
| `templates/unsubscribe.html` | ❌ NOT USED | Public website feature |
| `templates/dscr_quote_table.html` | ❌ NOT USED | Public website feature |
| `templates/admin/subscriptions.html` | ❌ NOT USED | Not referenced in routes |
| `templates/partials/*` | ❌ NOT USED | Public website partials |
| `templates/quote_email_versions/*` | ❌ NOT USED | Email templates (belong in RRR_Server) |
| `templates/dscr_quote_email_versions/*` | ❌ NOT USED | Email templates (belong in RRR_Server) |

---

## 📂 RECOMMENDED CLEANUP

### Move to `not_used/` folder:

```bash
# Root files
mv extensions.py not_used/
mv auth_decorators.py not_used/
mv limit_utils.py not_used/
mv serializers.py not_used/
mv utils.py not_used/

# Services
mv services/rate_ready_gui.py not_used/
mv services/rate_ready_realtor.py not_used/

# Templates - old base
mv templates/base.html not_used/

# Templates - public website features (belong in RRR_Server)
mv templates/affordability.html not_used/
mv templates/change_password.html not_used/
mv templates/custom_listing.html not_used/
mv templates/dscr_calculator.html not_used/
mv templates/listings.html not_used/
mv templates/login.html not_used/
mv templates/programs_owner.html not_used/
mv templates/quote.html not_used/
mv templates/quote_print.html not_used/
mv templates/quote_table.html not_used/
mv templates/rates.html not_used/
mv templates/rates_table.html not_used/
mv templates/request_password_reset.html not_used/
mv templates/reset_password.html not_used/
mv templates/unsubscribe.html not_used/
mv templates/dscr_quote_table.html not_used/

# Template directories
mv templates/partials not_used/
mv templates/quote_email_versions not_used/
mv templates/dscr_quote_email_versions not_used/

# Old admin template
mv templates/admin/subscriptions.html not_used/
```

---

## 📋 CURRENT ACTIVE STRUCTURE

After cleanup, here's what should remain:

```
RRR_Admin/
├── app.py                          ✅ Main Flask app
├── config.py                       ✅ Configuration
├── requirements.txt                ✅ Dependencies
├── .env                           ✅ Environment variables
├── README.md                      ✅ Documentation
├── FILE_USAGE.md                  ✅ This file
│
├── routes/
│   ├── __init__.py                ✅ Blueprint registration
│   ├── admin_routes.py            ✅ Admin routes
│   └── workflow_routes.py         ✅ Workflow routes
│
├── services/
│   ├── workflow_runner.py         ✅ Background workflows
│   ├── database_access.py         ✅ API client
│   ├── process_listings.py        ✅ HTML parser
│   ├── scrape_homes.py            ✅ File scraper
│   ├── scrape_pricing.py          ✅ Pricing scraper
│   ├── dscr_pricing.py            ✅ DSCR pricing
│   └── my_logger.py               ✅ Logger
│
├── templates/
│   └── admin/
│       ├── base.html              ✅ Base template
│       ├── dashboard.html         ✅ Dashboard
│       ├── workflows.html         ✅ Workflows
│       ├── user_activity.html     ✅ User activity
│       ├── listings.html          ✅ Listings (stub)
│       ├── quotes.html            ✅ Quotes (stub)
│       ├── contacts.html          ✅ Contacts (stub)
│       └── daily_prices.html      ✅ Prices (stub)
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
└── not_used/
    ├── flask_app.py               (old template)
    ├── rrr_server/                (reference files from RRR_Server)
    └── [all unused files above]
```

---

## 🎯 SUMMARY

**Total Files:**
- ✅ **Used**: 24 files
- ❌ **Not Used**: ~35+ files

**Action Items:**
1. Move unused files to `not_used/` folder
2. Keep the active structure clean and minimal
3. Build out the stub templates (listings, quotes, contacts, daily_prices, user_activity) as needed

**Core Philosophy:**
- This is an API-only admin client
- No models, no SQLAlchemy, no direct database
- All data via `services/database_access.py` → RRR_Server API
- Reuses workflow modules from RRR_local
- Clean, minimal structure focused on admin tasks
