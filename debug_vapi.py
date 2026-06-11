"""Run this directly: python debug_vapi.py"""
import asyncio, httpx, json, os
from dotenv import load_dotenv
load_dotenv()

VAPI_KEY = os.getenv("VAPI_API_KEY")
PHONE_ID = os.getenv("VAPI_PHONE_NUMBER_ID")
HEADERS  = {"Authorization": f"Bearer {VAPI_KEY}", "Content-Type": "application/json"}

async def main():
    async with httpx.AsyncClient(timeout=15) as c:

        print("=" * 60)
        print("1. PHONE NUMBER CONFIG")
        r = await c.get(f"https://api.vapi.ai/phone-number/{PHONE_ID}", headers=HEADERS)
        print(f"   Status: {r.status_code}")
        print(f"   Body:   {json.dumps(r.json(), indent=2)[:600]}")

        print()
        print("2. RECENT CALLS (last 5)")
        r2 = await c.get("https://api.vapi.ai/call?limit=5", headers=HEADERS)
        print(f"   Status: {r2.status_code}")
        calls = r2.json() if r2.status_code == 200 else []
        if isinstance(calls, list):
            for call in calls:
                print(f"   Call id={call.get('id')} status={call.get('status')} to={call.get('customer',{}).get('number','?')}")
                if call.get("endedReason"):
                    print(f"     endedReason: {call['endedReason']}")
                if call.get("errorMessage"):
                    print(f"     error: {call['errorMessage']}")
        else:
            print(f"   Body: {r2.text[:400]}")

        print()
        print("3. TEST OUTBOUND CALL (to your own number — CHANGE NUMBER BELOW)")
        YOUR_NUMBER = "+2348031234567"  # <-- change this to your real number
        payload = {
            "phoneNumberId": PHONE_ID,
            "customer": {"number": YOUR_NUMBER},
            "type": "outboundPhoneCall",
            "assistantId": None,
            "assistant": {
                "firstMessage": "Hello, this is a test call from SwiftClose Realty. If you hear this, the system is working. Goodbye.",
                "model": {"provider": "groq", "model": "llama-3.3-70b-versatile",
                          "messages": [{"role": "system", "content": "You are a test assistant. Say the first message and end the call."}]},
                "voice": {"provider": "playht", "voiceId": "jennifer"},
                "endCallFunctionEnabled": True,
            }
        }
        r3 = await c.post("https://api.vapi.ai/call", headers=HEADERS, json=payload)
        print(f"   Status: {r3.status_code}")
        print(f"   Body:   {r3.text[:600]}")

asyncio.run(main())
