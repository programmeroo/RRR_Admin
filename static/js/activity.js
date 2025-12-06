/**
 * Global UI Activity Logger
 * -------------------------
 * This script automatically logs user interactions across the entire site.
 *
 * Any element with:
 *   data-log
 *   data-feature="listing"
 *   data-action="view_more"
 *   data-notes="mls=12345"
 *
 * will automatically generate:
 *   POST /api/activity
 *   {
 *     activity_type: "ui_click",
 *     feature: "listing",
 *     action: "view_more",
 *     notes: "mls=12345",
 *     endpoint: "/listings"
 *   }
 *
 * Backend will attach:
 *   - contact_id (if logged in)
 *   - email (if logged in)
 *   - ip_address (from api_logs)
 *   - user_agent (from api_logs)
 */

function logActivity(feature, action, notes = null) {
    try {
        fetch("/api/activity", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                activity_type: "ui_click",
                feature: feature || null,
                action: action || "click",
                notes: notes || null,
                endpoint: window.location.pathname
            })
        });
    } catch (err) {
        // Never allow logging failures to affect UI
        console.error("Activity logging error:", err);
    }
}


/**
 * Global Click Listener
 * ---------------------
 * Any element with data-log will be tracked automatically.
 */
document.addEventListener("click", function (e) {
    const el = e.target.closest("[data-log]");
    if (!el) return;

    const feature = el.dataset.feature || null;
    const action = el.dataset.action || "click";
    const notes = el.dataset.notes || null;

    logActivity(feature, action, notes);
});


/**
 * Optional: Track page load events
 * --------------------------------
 * Uncomment if you want to log page views:
 *
 * logActivity("page", "open_page", document.title);
 *
 * But this is disabled by default to avoid noise.
 */

// logActivity("page", "open_page", document.title);
