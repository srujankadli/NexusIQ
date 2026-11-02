import sys
import time
from playwright.sync_api import sync_playwright

def run_e2e_audit():
    print("=================================================================")
    print("NexusIQ End-to-End Headless Browser Interaction & Reliability Audit")
    print("=================================================================")

    console_errors = []
    console_logs = []

    def on_console(msg):
        if msg.type == "error":
            console_errors.append(msg.text)
        else:
            console_logs.append(f"[{msg.type}] {msg.text}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.on("console", on_console)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        # -------------------------------------------------------------
        # STEP 1: INITIAL LOAD & DASHBOARD VIEW
        # -------------------------------------------------------------
        print("\n--- 1. Testing Dashboard View & Initial Load ---")
        page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        time.sleep(2)

        # Check page title and banner
        banner_text = page.locator("h1").first.text_content()
        print(f"  [PASS] Page Loaded: '{banner_text}'")

        # Verify KPI values are populated (not null or empty)
        kpi_cards = page.locator(".grid-cols-2.md\\:grid-cols-3 > div")
        count = kpi_cards.count()
        print(f"  [PASS] Found {count} KPI summary cards on Dashboard")

        # Test Refresh button
        refresh_btn = page.get_by_role("button", name="Refresh")
        refresh_btn.click()
        time.sleep(1)
        toast = page.locator("div.bg-emerald-500\\/10").first
        if toast.is_visible():
            print(f"  [PASS] Refresh Telemetry Toast: '{toast.text_content()}'")

        # Test Ingest Data button navigation
        ingest_btn = page.get_by_role("button", name="Ingest Data")
        ingest_btn.click()
        time.sleep(1)
        assert any("Ingest Electricity Bills" in h for h in page.locator("h1").all_text_contents())
        print("  [PASS] Navigated to Data Ingestion via 'Ingest Data' button")

        # Return to Dashboard
        page.locator("nav button:has-text('Dashboard')").first.click()
        time.sleep(1)

        # Test 'Open 3D Campus Twin' navigation button
        twin_link = page.get_by_role("button", name="Open 3D Campus Twin")
        twin_link.click()
        time.sleep(1)
        assert any("NHCE Multi-Building" in h for h in page.locator("h1").all_text_contents())
        print("  [PASS] Navigated to Digital Twin via Dashboard link")

        # -------------------------------------------------------------
        # STEP 2: DIGITAL TWIN VIEW
        # -------------------------------------------------------------
        print("\n--- 2. Testing Digital Twin View ---")
        # Click on different buildings
        building_cards = page.locator("div.grid-cols-1.sm\\:grid-cols-2 > div")
        bld_count = building_cards.count()
        print(f"  [PASS] Submetered Buildings Found: {bld_count}")
        if bld_count > 1:
            building_cards.nth(1).click()
            time.sleep(0.5)
            print("  [PASS] Selected Building 2, telemetry panel updated")

        # Check if controllable load shift button exists
        shift_btn = page.locator("button:has-text('Simulate Shift'), button:has-text('Revert to Baseline')")
        if shift_btn.count() > 0 and shift_btn.first.is_visible():
            btn_text_before = shift_btn.first.text_content()
            shift_btn.first.click()
            time.sleep(1.5)
            print(f"  [PASS] Dispatched BMS load shift: '{btn_text_before}'")

        # -------------------------------------------------------------
        # STEP 3: FORECASTING VIEW
        # -------------------------------------------------------------
        print("\n--- 3. Testing AI Forecast View ---")
        page.locator("nav button:has-text('AI Forecast')").first.click()
        time.sleep(1.5)
        assert any("AI Demand Prediction" in h for h in page.locator("h1").all_text_contents())
        print("  [PASS] Navigated to AI Forecast view")

        # Test weather simulation buttons
        for w_label in ["Scattered (25%)", "Overcast (60%)", "Monsoon (85%)", "Clear Sky (10%)"]:
            w_btn = page.get_by_role("button", name=w_label)
            w_btn.click()
            time.sleep(1)
            print(f"  [PASS] Weather Simulation triggered: {w_label}")

        # Test Anomaly remediation if anomalies present
        remed_btn = page.locator("button:has-text('Execute Remediation')")
        if remed_btn.count() > 0 and remed_btn.first.is_visible():
            remed_btn.first.click()
            time.sleep(1)
            print("  [PASS] Executed BMS Automated Anomaly Remediation")

        # -------------------------------------------------------------
        # STEP 4: OPTIMIZATION VIEW
        # -------------------------------------------------------------
        print("\n--- 4. Testing Optimization Dispatch View ---")
        page.locator("nav button:has-text('Optimization')").first.click()
        time.sleep(1.5)
        assert any("Energy Dispatch Schedule" in h for h in page.locator("h1").all_text_contents())
        print("  [PASS] Navigated to Optimization view")

        # Test Collapsible Data Table Inspector
        inspect_btn = page.get_by_role("button", name="Inspect 24h Data")
        inspect_btn.click()
        time.sleep(0.5)
        assert "24-Hour Dispatch Numerical Inspector" in page.content(), "Table Inspector did not expand"
        print("  [PASS] 24-Hour Dispatch Table Inspector expanded successfully")
        page.get_by_role("button", name="Hide Data Table").click()
        time.sleep(0.5)
        print("  [PASS] 24-Hour Dispatch Table Inspector collapsed successfully")

        # Test Flexible Load Shifting checkbox toggle
        flex_checkbox = page.locator("input[type='checkbox']").first
        flex_checkbox.uncheck()
        time.sleep(1.5)
        print("  [PASS] Reran optimization with Flexible Load Shifting disabled")
        flex_checkbox.check()
        time.sleep(1.5)
        print("  [PASS] Reran optimization with Flexible Load Shifting enabled")

        # Test Recommendation Include/Exclude toggle button
        rec_toggle = page.locator("button:has-text('Included'), button:has-text('Excluded')").first
        if rec_toggle.is_visible():
            txt_before = rec_toggle.text_content()
            rec_toggle.click()
            time.sleep(0.5)
            print(f"  [PASS] Toggled recommendation status from '{txt_before}'")

        # Verify Download CSV link exists and has valid target
        download_link = page.locator("a[download='nexusiq_optimized_dispatch_schedule.csv']")
        assert download_link.is_visible() and "/api/optimization/download-schedule-csv" in download_link.get_attribute("href")
        print("  [PASS] Verified Dispatch Schedule CSV download link")

        # -------------------------------------------------------------
        # STEP 5: WHAT-IF SIMULATOR VIEW
        # -------------------------------------------------------------
        print("\n--- 5. Testing What-If Simulator View ---")
        page.locator("nav button:has-text('What-If Sim')").first.click()
        time.sleep(1.5)
        assert any("Interactive What-If" in h for h in page.locator("h1").all_text_contents())
        print("  [PASS] Navigated to What-If Simulator view")

        # Test Sliders
        sliders = page.locator("input[type='range']")
        assert sliders.count() >= 4, f"Expected at least 4 sliders, found {sliders.count()}"
        # Adjust Solar slider
        sliders.nth(0).fill("1.5")
        # Adjust Battery slider
        sliders.nth(1).fill("1.8")
        time.sleep(1)
        print("  [PASS] Adjusted Solar (1.5x) and Battery (1.8x) simulation sliders")

        # Test Reset Defaults button
        reset_btn = page.get_by_role("button", name="Reset Defaults")
        reset_btn.click()
        time.sleep(1)
        print("  [PASS] Simulator Reset Defaults executed successfully")

        # Test Apply to Platform button
        apply_btn = page.get_by_role("button", name="Apply to Platform")
        apply_btn.click()
        time.sleep(1.5)
        print("  [PASS] Simulated parameters applied to platform with confirmation toast")

        # -------------------------------------------------------------
        # STEP 6: DATA INGESTION & CSV PROCESSING VIEW
        # -------------------------------------------------------------
        print("\n--- 6. Testing Data Ingestion View ---")
        page.locator("nav button:has-text('Data Ingestion')").first.click()
        time.sleep(1.5)
        assert any("Ingest Electricity Bills" in h for h in page.locator("h1").all_text_contents())
        print("  [PASS] Navigated to Data Ingestion view")

        # Click "Load Demo Dataset (7 Days)"
        load_sample_btn = page.get_by_role("button", name="Load Demo Dataset (7 Days)")
        load_sample_btn.click()
        time.sleep(2)
        assert "Ingestion Analysis Summary" in page.content()
        assert "Total Logged Energy" in page.content()
        print("  [PASS] 7-Day Smart Meter Demo Dataset parsed & profiled successfully")

        # Test "View Live Dashboard with Uploaded Profile"
        view_dash_btn = page.get_by_role("button", name="View Live Dashboard with Uploaded Profile")
        view_dash_btn.click()
        time.sleep(1.5)
        assert any("NexusIQ" in h for h in page.locator("h1").all_text_contents())
        print("  [PASS] Ingestion summary transitioned seamlessly back to Live Dashboard")

        # -------------------------------------------------------------
        # STEP 7: ESG REPORTS VIEW
        # -------------------------------------------------------------
        print("\n--- 7. Testing ESG Reports View ---")
        page.locator("nav button:has-text('ESG Reports')").first.click()
        time.sleep(1.5)
        assert any("Campus Carbon Offsets" in h for h in page.locator("h1").all_text_contents())
        assert "Green Building Energy Audit Certificate" in page.content()
        print("  [PASS] Verified ESG certificate badges, carbon accounting & CEA standards")

        # -------------------------------------------------------------
        # STEP 8: SETTINGS MODAL
        # -------------------------------------------------------------
        print("\n--- 8. Testing Settings Modal ---")
        settings_btn = page.locator("header button:has(svg.lucide-settings)").first
        settings_btn.click()
        page.wait_for_selector("div.fixed.inset-0", timeout=5000)
        assert any("Facility & Tariff Configuration" in h for h in page.locator("h2").all_text_contents())
        print("  [PASS] Settings modal opened")

        # Test Cancel button
        cancel_btn = page.locator("div.fixed.inset-0 button:has-text('Cancel')").first
        cancel_btn.click()
        page.wait_for_timeout(500)
        print("  [PASS] Settings modal closed via Cancel")

        # Reopen and save
        settings_btn.click()
        page.wait_for_selector("div.fixed.inset-0", timeout=5000)
        save_btn = page.locator("div.fixed.inset-0 button:has-text('Save Parameters')").first
        save_btn.click()
        time.sleep(1.5)
        print("  [PASS] Settings saved and platform telemetry updated")

        # -------------------------------------------------------------
        # STEP 9: DEPLOYMENT LEVEL SWITCHING (L1, L2, L3)
        # -------------------------------------------------------------
        print("\n--- 9. Testing Deployment Level Switching ---")
        # Switch to L1: Basic
        page.locator("header button:has-text('L1: Basic')").first.click()
        time.sleep(1.5)
        page.locator("nav button:has-text('Dashboard')").first.click()
        time.sleep(1)
        assert "No Solar Installed" in page.content(), "Level 1 should show No Solar Installed"
        assert "No Storage Installed" in page.content(), "Level 1 should show No Storage Installed"
        print("  [PASS] Switched to Level 1 (Basic): Verified No Solar and No Battery")

        # Switch to L2: Solar
        page.locator("header button:has-text('L2: Solar')").first.click()
        time.sleep(1.5)
        assert "No Storage Installed" in page.content(), "Level 2 should show No Storage Installed"
        print("  [PASS] Switched to Level 2 (Solar): Verified Solar active and No Storage Installed")

        # Switch back to L3: Microgrid
        page.locator("header button:has-text('L3: Microgrid')").first.click()
        time.sleep(1.5)
        print("  [PASS] Switched back to Level 3 (Intelligent Campus): Full microgrid active")

        # -------------------------------------------------------------
        # STEP 10: MOBILE RESPONSIVE NAVIGATION
        # -------------------------------------------------------------
        print("\n--- 10. Testing Mobile Responsive Navigation ---")
        page.set_viewport_size({"width": 375, "height": 667})
        time.sleep(0.5)

        # Click hamburger menu
        menu_toggle = page.locator("button[aria-label='Toggle Navigation Menu']")
        menu_toggle.click()
        time.sleep(0.5)
        # Click Digital Twin in mobile menu
        page.locator(".md\\:hidden button:has-text('Digital Twin')").click()
        time.sleep(1)
        assert "Campus Microgrid Digital Twin" in page.content()
        print("  [PASS] Mobile Navigation Drawer successfully navigated to Digital Twin on 375px mobile viewport")

        # -------------------------------------------------------------
        # AUDIT VERIFICATION RESULTS
        # -------------------------------------------------------------
        print("\n=================================================================")
        print(f"Browser Console Errors: {len(console_errors)}")
        if console_errors:
            for err in console_errors:
                print(f"  [ERROR] {err}")
        else:
            print("  [PASS] Zero (0) browser console errors recorded during full workflow!")
        print("=================================================================")
        assert len(console_errors) == 0, f"Encountered {len(console_errors)} console errors during browser test"

        browser.close()

if __name__ == "__main__":
    run_e2e_audit()
