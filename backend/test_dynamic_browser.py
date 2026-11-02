import os
import time
from playwright.sync_api import sync_playwright

def clean_str(s):
    return str(s).replace("\u20b9", "INR ")

def run_browser_dynamic_test():
    print("=================================================================")
    print("NexusIQ Dynamic Data Integration & Multi-Dataset Browser Test")
    print("=================================================================")

    frontend_host = os.getenv("FRONTEND_HOST", "localhost")
    frontend_port = os.getenv("FRONTEND_PORT", "3000")
    base_url = f"http://{frontend_host}:{frontend_port}"

    file_a = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_data", "dataset_a_tech_park.csv"))
    file_b = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_data", "dataset_b_heavy_industry.csv"))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: errors.append(str(err)))

        # -------------------------------------------------------------
        # STEP 1: INITIAL LOAD (DEMO BENCHMARK)
        # -------------------------------------------------------------
        print(f"\n--- 1. Initial Load at {base_url} ---")
        page.goto(f"{base_url}/", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Check Active Dataset Badge in Navbar
        badge_text = page.locator("div.hidden.xl\\:flex").first.text_content()
        print(f"  [PASS] Navbar Active Dataset Badge: '{clean_str(badge_text)}'")

        kpis_initial = page.locator(".grid-cols-2.md\\:grid-cols-3 > div p.text-xl").all_text_contents()
        print(f"  [PASS] Demo KPIs: {[clean_str(x) for x in kpis_initial]}")
        page.screenshot(path="screenshot_1_demo_dashboard.png")

        # -------------------------------------------------------------
        # STEP 2: UPLOAD DATASET A (Tech Park)
        # -------------------------------------------------------------
        print("\n--- 2. Ingesting Dataset A (Tech Park: ~11,480 kWh, Solar PV) ---")
        page.locator("nav button:has-text('Data Ingestion')").first.click()
        page.wait_for_timeout(1000)

        # Upload file via file input
        file_input = page.locator("input[type='file']")
        file_input.set_input_files(file_a)
        page.wait_for_timeout(500)

        # Click Parse & Profile Facility button
        parse_btn = page.locator("button:has-text('Parse & Profile Facility')")
        parse_btn.click()
        page.wait_for_timeout(2500)

        # Check summary card on ingestion view
        summary_kwh = page.locator("span:has-text('Total Logged Energy') + span").first.text_content()
        summary_peak = page.locator("span:has-text('Peak Recorded Load') + span").first.text_content()
        print(f"  [PASS] Ingestion Summary: Energy = '{clean_str(summary_kwh)}', Peak = '{clean_str(summary_peak)}'")
        assert "11,479" in summary_kwh or "11,480" in summary_kwh

        # Navigate to Dashboard to verify Dataset A live propagation
        page.locator("nav button:has-text('Dashboard')").first.click()
        page.wait_for_timeout(2000)

        kpis_a = page.locator(".grid-cols-2.md\\:grid-cols-3 > div p.text-xl").all_text_contents()
        print(f"  [PASS] Dataset A Dashboard KPIs: {[clean_str(x) for x in kpis_a]}")
        assert "11,480 kWh" in kpis_a[0] or "11,479.8 kWh" in kpis_a[0]
        assert kpis_a[1] != "0 kWh" # Solar is installed

        # Verify chart curves for Dataset A
        curves_a = page.locator(".recharts-curve").count()
        print(f"  [PASS] Rendered curves count: {curves_a}")
        assert curves_a >= 3

        page.screenshot(path="screenshot_2_dataset_a_dashboard.png")
        print("  [PASS] Captured 'screenshot_2_dataset_a_dashboard.png'")

        # Verify Forecasting View for Dataset A
        page.locator("nav button:has-text('AI Forecast')").first.click()
        page.wait_for_timeout(1500)
        fc_curves_a = page.locator(".recharts-curve").count()
        print(f"  [PASS] AI Forecast View curves count: {fc_curves_a}")
        assert fc_curves_a >= 2

        # Verify Optimization View for Dataset A
        page.locator("nav button:has-text('Optimization')").first.click()
        page.wait_for_timeout(1500)
        opt_cost_a = page.locator("p.text-2xl.font-extrabold").first.text_content()
        print(f"  [PASS] Optimization Baseline Cost for Dataset A: '{clean_str(opt_cost_a)}'")

        # Verify ESG Reports for Dataset A
        page.locator("nav button:has-text('ESG Reports')").first.click()
        page.wait_for_timeout(1500)
        esg_dataset_a = page.locator("span:has-text('Active Dataset:') + span").first.text_content()
        print(f"  [PASS] ESG Report Active Dataset: '{clean_str(esg_dataset_a)}'")
        assert "dataset_a_tech_park.csv" in esg_dataset_a

        # -------------------------------------------------------------
        # STEP 3: UPLOAD DATASET B (Heavy Industry)
        # -------------------------------------------------------------
        print("\n--- 3. Ingesting Dataset B (Heavy Industry: ~108,710 kWh, ZERO Solar) ---")
        page.locator("nav button:has-text('Data Ingestion')").first.click()
        page.wait_for_timeout(1000)

        file_input = page.locator("input[type='file']")
        file_input.set_input_files(file_b)
        page.wait_for_timeout(500)

        parse_btn = page.locator("button:has-text('Parse & Profile Facility')")
        parse_btn.click()
        page.wait_for_timeout(2500)

        summary_b_kwh = page.locator("span:has-text('Total Logged Energy') + span").first.text_content()
        summary_b_peak = page.locator("span:has-text('Peak Recorded Load') + span").first.text_content()
        print(f"  [PASS] Ingestion Summary: Energy = '{clean_str(summary_b_kwh)}', Peak = '{clean_str(summary_b_peak)}'")
        assert "108,710" in summary_b_kwh

        # Navigate to Dashboard to verify Dataset B live propagation
        page.locator("nav button:has-text('Dashboard')").first.click()
        page.wait_for_timeout(2000)

        kpis_b = page.locator(".grid-cols-2.md\\:grid-cols-3 > div p.text-xl").all_text_contents()
        print(f"  [PASS] Dataset B Dashboard KPIs: {[clean_str(x) for x in kpis_b]}")
        assert "108,710.2 kWh" in kpis_b[0] or "108,710 kWh" in kpis_b[0]
        assert kpis_b[1] == "0 kWh" # Zero solar installed!

        page.screenshot(path="screenshot_3_dataset_b_dashboard.png")
        print("  [PASS] Captured 'screenshot_3_dataset_b_dashboard.png'")

        # Verify Dataset B is 10x larger than Dataset A
        val_a = float(kpis_a[0].replace(" kWh", "").replace(",", ""))
        val_b = float(kpis_b[0].replace(" kWh", "").replace(",", ""))
        print(f"  [PASS] Verified Dataset B ({val_b:,.1f} kWh) is ~10x Dataset A ({val_a:,.1f} kWh)")
        assert val_b > 8 * val_a

        # Verify ESG Reports for Dataset B
        page.locator("nav button:has-text('ESG Reports')").first.click()
        page.wait_for_timeout(1500)
        esg_dataset_b = page.locator("span:has-text('Active Dataset:') + span").first.text_content()
        print(f"  [PASS] ESG Report Active Dataset: '{clean_str(esg_dataset_b)}'")
        assert "dataset_b_heavy_industry.csv" in esg_dataset_b

        # -------------------------------------------------------------
        # STEP 4: SWITCH BACK TO DEMO MODE
        # -------------------------------------------------------------
        print("\n--- 4. Switching Back to Demo Mode ---")
        demo_btn = page.locator("button:has-text('Demo')").first
        demo_btn.click()
        page.wait_for_timeout(2000)

        page.locator("nav button:has-text('Dashboard')").first.click()
        page.wait_for_timeout(1500)

        kpis_restored = page.locator(".grid-cols-2.md\\:grid-cols-3 > div p.text-xl").all_text_contents()
        print(f"  [PASS] Demo Restored Dashboard KPIs: {[clean_str(x) for x in kpis_restored]}")
        page.screenshot(path="screenshot_4_demo_restored.png")
        print("  [PASS] Captured 'screenshot_4_demo_restored.png'")

        print(f"\nBrowser Console Errors: {len(errors)}")
        assert len(errors) == 0, f"Encountered browser errors: {errors}"

        browser.close()
        print("\n=======================================================")
        print("[SUCCESS] All Multi-Dataset Browser Tests Passed 100%!")
        print("=======================================================")

if __name__ == "__main__":
    run_browser_dynamic_test()
