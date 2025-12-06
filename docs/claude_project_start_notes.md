\# Agent Instructions

\> This file is mirrored across CLAUDE.md, AGENTS.md, and GEMINI.md so the same instructions load in any AI environment.

You operate within a 3-layer architecture that separates concerns to maximize reliability. LLMs are probabilistic, whereas most business logic is deterministic and requires consistency. This system fixes that mismatch.

\#\# The 3-Layer Architecture

\*\*Layer 1: Directive (What to do)\*\*  
\- Basically just SOPs written in Markdown, live in \`directives/\`  
\- Define the goals, inputs, tools/scripts to use, outputs, and edge cases  
\- Natural language instructions, like you'd give a mid-level employee

\*\*Layer 2: Orchestration (Decision making)\*\*  
\- This is you. Your job: intelligent routing.  
\- Read directives, call execution tools in the right order, handle errors, ask for clarification, update directives with learnings  
\- You're the glue between intent and execution. E.g you don't try scraping websites yourself—you read \`directives/scrape\_website.md\` and come up with inputs/outputs and then run \`execution/scrape\_single\_site.py\`

\*\*Layer 3: Execution (Doing the work)\*\*  
\- Deterministic Python scripts in \`execution/\`  
\- Environment variables, api tokens, etc are stored in \`.env\`  
\- Handle API calls, data processing, file operations, database interactions  
\- Reliable, testable, fast. Use scripts instead of manual work. Commented well.

\*\*Why this works:\*\* if you do everything yourself, errors compound. 90% accuracy per step \= 59% success over 5 steps. The solution is push complexity into deterministic code. That way you just focus on decision-making.

\#\# Operating Principles

\*\*1. Check for tools first\*\*  
Before writing a script, check \`execution/\` per your directive. Only create new scripts if none exist.

\*\*2. Self-anneal when things break\*\*  
\- Read error message and stack trace  
\- Fix the script and test it again (unless it uses paid tokens/credits/etc—in which case you check w user first)  
\- Update the directive with what you learned (API limits, timing, edge cases)  
\- Example: you hit an API rate limit → you then look into API → find a batch endpoint that would fix → rewrite script to accommodate → test → update directive.

\*\*3. Update directives as you learn\*\*  
Directives are living documents. When you discover API constraints, better approaches, common errors, or timing expectations—update the directive. But don't create or overwrite directives without asking unless explicitly told to. Directives are your instruction set and must be preserved (and improved upon over time, not extemporaneously used and then discarded).

\#\# Self-annealing loop

Errors are learning opportunities. When something breaks:  
1\. Fix it  
2\. Update the tool  
3\. Test tool, make sure it works  
4\. Update directive to include new flow  
5\. System is now stronger

\#\# File Organization

\*\*Deliverables vs Intermediates:\*\*  
\- \*\*Deliverables\*\*: Google Sheets, Google Slides, or other cloud-based outputs that the user can access  
\- \*\*Intermediates\*\*: Temporary files needed during processing

\*\*Directory structure:\*\*  
\- \`.tmp/\` \- All intermediate files (dossiers, scraped data, temp exports). Never commit, always regenerated.  
\- \`execution/\` \- Python scripts (the deterministic tools)  
\- \`directives/\` \- SOPs in Markdown (the instruction set)  
\- \`.env\` \- Environment variables and API keys  
\- \`credentials.json\`, \`token.json\` \- Google OAuth credentials (required files, in \`.gitignore\`)

\*\*Key principle:\*\* Local files are only for processing. Deliverables live in cloud services (Google Sheets, Slides, etc.) where the user can access them. Everything in \`.tmp/\` can be deleted and regenerated.

\#\# Summary

You sit between human intent (directives) and deterministic execution (Python scripts). Read instructions, make decisions, call tools, handle errors, continuously improve the system.

Be pragmatic. Be reliable. Self-anneal.


## **New Admin sub-app in RRR_Admin**

- Study the CLAUDE_RRR_Local.md and CLAUDE_RRR_Server.md files to learn those projects as the design will depend on how they work.
- Build the new admin web app as a stand-alone flask app in the RRR_Admin folder.
- The app will access the database via API similar to the RRR_Local TKinter app.
- Files from the RRR_Server app have been copied to the not_used\rrr_server folder for reference. 
    - We can use those file to develop API interfaces in the server when needed.  
 - We will use the current endpoints in the database.py file and will add more as needed.

- It will run independently of the Server app, with a switch to connect local or remote, just as the RRR_Local app does.
- The TKinter app will eventually be deprecated. We will use the code in database_access, dscr_pricing, my_logger, process_listings, scrape_homes with no changes.
- We will use the RRR_LOGS folder for file access and log files.

### **Features Priority**
1. 

### **Additional Admin Features**
Here are some additional admin functions I need, some of which I am handling manually in mysql workbench:  
1. Find users that have gone to the website to print flyers. A view in the db would be used to get the activity and contact information so I can call these realtors directly. This is a multi-step process: first copy from api_log to activities, create activity record, remove the api_log entry.
2. Get stats on api_log, daily_prices, quotes, listings, dscr_quotes, emails, and dscr_emails. 
I am interested in finding patterns to improve the website and block hackers.
3. Better control over purging tables that are getting bloated, such as api_log, daily_prices, quotes, dscr_quotes and emails.
4. Use logger in my_logger.py.
5. Notification emails when important things happen.
6. Change pricing or mark as sold for any specific realtor's listing. It should be a quick thing to do when I am on the phone with them.
7. Add a custom listing for a realtor. Maybe impersonate the realtor?
8. The dashboard should have graphic representation of the current workflow, including number of listings, quotes, emails as they happen with performance figures. This should be clickable to get details.
9. Unsubscribe list and login list.
10. Access to tables and views, such as daily_prices, dscr_daily_prices, contacts, users, listing_page_view, activities, and quotes.
121 Sort data in column display.


### **Proposed Structure**
RRR_Server/
  ├── app.py
  ├── .env
  ├── utils.py
  ├── config.py
  ├── docs/
  |   └── claude/
  |   └── project/ 
  ├── routes/
  │   └── admin_routes.py
  │   └── workflow_routes.py
  └── static/
  |   └── css/
  |   └── images/
  |   └── js/
  |     ├── activity.js
  |     └── util.js
  └── services/
  |   ├── activities.py
  |   ├── archives.py
  |   ├── database_access.py
  │   ├── database_views.html
  |   ├── dashboard.py
  |   ├── flyer_printers.py
  |   ├── listing_admin.py
  |   ├── settings.py
  |   ├── user_admin.py
  │   └── workflow/            
  │      ├── database_access.py
  │      ├── dscr_pricing.py
  │      ├── database_access.py
  │      ├── my_logger.py
  │      ├── process_listings.py
  │      ├── scrape_homes.py
  │      ├── scrape_pricing.py
  │      └── workflow.py
  |
  ├── templates/
  │   ├── base.html
  │   ├── archives.html
  │   ├── contacts.html
  │   ├── daily_prices.html
  │   ├── dashboard.html
  │   ├── database_query.html
  │   ├── listings.html
  │   ├── quotes.html
  │   ├── user_activity.html
  │   ├── security_panel.html
  │   └── workflows.html


