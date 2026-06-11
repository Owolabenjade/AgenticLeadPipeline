"""Run this directly: python debug_hubspot.py"""
import asyncio, httpx, json, os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")
OWNER = os.getenv("HUBSPOT_SALES_OWNER_ID")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

async def main():
    async with httpx.AsyncClient(timeout=15) as c:

        print("=" * 60)
        print("1. PIPELINES")
        r = await c.get("https://api.hubapi.com/crm/v3/pipelines/deals", headers=HEADERS)
        print(f"   Status: {r.status_code}")
        pipeline_id = "default"
        stage_id = "appointmentscheduled"
        if r.status_code == 200:
            for p in r.json().get("results", []):
                pipeline_id = p["id"]
                print(f"   Pipeline: id={p['id']}  label={p['label']}")
                for s in p.get("stages", []):
                    stage_id = s["id"]
                    print(f"     Stage: id={s['id']}  label={s['label']}")
        else:
            print(f"   ERROR: {r.text[:200]}")

        print()
        print("2. CONTACTS (first 3)")
        r2 = await c.get("https://api.hubapi.com/crm/v3/objects/contacts?limit=3", headers=HEADERS)
        print(f"   Status: {r2.status_code}")
        contact_id = None
        if r2.status_code == 200:
            for ct in r2.json().get("results", []):
                print(f"   Contact id={ct['id']}  {ct['properties'].get('firstname','')} {ct['properties'].get('lastname','')}")
                contact_id = ct["id"]
        else:
            print(f"   ERROR: {r2.text[:200]}")

        print()
        print("3. DEAL — minimal (no owner, no association)")
        r3 = await c.post(
            "https://api.hubapi.com/crm/v3/objects/deals",
            headers=HEADERS,
            json={"properties": {"dealname": "DEBUG Test Deal", "pipeline": pipeline_id, "dealstage": stage_id}}
        )
        print(f"   Status: {r3.status_code}")
        print(f"   Body:   {r3.text[:400]}")
        deal_id = r3.json().get("id") if r3.status_code in (200, 201) else None

        print()
        print(f"4. DEAL — with owner ({OWNER})")
        r4 = await c.post(
            "https://api.hubapi.com/crm/v3/objects/deals",
            headers=HEADERS,
            json={"properties": {"dealname": "DEBUG Test Deal + Owner", "pipeline": pipeline_id,
                                 "dealstage": stage_id, "hubspot_owner_id": OWNER}}
        )
        print(f"   Status: {r4.status_code}")
        print(f"   Body:   {r4.text[:400]}")

        print()
        print("5. OWNER LOOKUP")
        r5 = await c.get(f"https://api.hubapi.com/crm/v3/owners/{OWNER}", headers=HEADERS)
        print(f"   Status: {r5.status_code}")
        print(f"   Body:   {r5.text[:300]}")

        print()
        print("6. PRIVATE APP SCOPES")
        r6 = await c.get(f"https://api.hubapi.com/oauth/v1/access-tokens/{TOKEN}")
        print(f"   Status: {r6.status_code}")
        if r6.status_code == 200:
            scopes = r6.json().get("scopes", [])
            print(f"   Scopes: {scopes}")
        else:
            print(f"   Body: {r6.text[:300]}")

        print()
        print("=" * 60)
        print("SUMMARY")
        print(f"  Pipeline used: {pipeline_id}")
        print(f"  Stage used:    {stage_id}")
        print(f"  Contact ID:    {contact_id}")
        print(f"  Deal created:  {deal_id}")

asyncio.run(main())
