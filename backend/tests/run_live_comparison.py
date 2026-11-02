import requests
import json
import time
import os

BASE_URL = 'https://ai-financial-intelligence-platform-89re.onrender.com'
login_payload = {'email': 'supermarket.demo@alladin.ai', 'password': 'Password123!'}

print('Connecting to ALLADIN backend and authenticating supermarket demo account...')
resp = requests.post(f'{BASE_URL}/api/v1/auth/login', json=login_payload, timeout=60)
if resp.status_code != 200:
    print('Failed to authenticate:', resp.status_code, resp.text)
    exit(1)

token = resp.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Fetch company context
me_resp = requests.get(f'{BASE_URL}/api/v1/auth/me', headers=headers, timeout=30)
user_data = me_resp.json().get('data', {})
company = user_data.get('companies', [{}])[0]
company_id = company.get('id')
company_name = company.get('name')
headers['X-Company-ID'] = company_id

print(f"Authenticated User: {user_data.get('email')}")
print(f"Tenant Context: {company_name} (ID: {company_id})")

questions = [
    "What is the name of my company, and what business data can you access for it?",
    "Explain the accounting equation — Assets = Liabilities + Owner’s Equity — with a simple supermarket example. Explain how a business owner can use it to understand financial position.",
    "How can a small supermarket improve cash flow and working capital? Give practical steps and explain the financial principles behind them.",
    "How can a supermarket reduce excess inventory and stockouts without tying up too much working capital?",
    "What financial indicators should a small supermarket owner monitor every month, and how should they interpret them?",
    "What does the knowledge base say about the relationship between assets, liabilities, and owner’s equity? Name the exact source you used.",
    "What is the current benchmark repo rate in 2026 according to public internet news?"
]

results = {'ollama': [], 'gemini': []}

for provider in ['ollama', 'gemini']:
    print(f"\n=======================================================")
    print(f"=== Testing Live Chat Provider: {provider.upper()} ===")
    print(f"=======================================================")
    sess_resp = requests.post(
        f'{BASE_URL}/api/v1/chat/sessions',
        json={'title': f'Supermarket Audit - {provider.upper()}'},
        headers=headers,
        timeout=30
    )
    sess_id = sess_resp.json().get('data', {}).get('id')
    print(f"Created Session ID: {sess_id}")

    for i, q in enumerate(questions, 1):
        print(f"\n--- [{provider.upper()} Q{i}] {q[:65]}... ---")
        t0 = time.time()
        try:
            msg_payload = {'message': q, 'provider': provider}
            url = f'{BASE_URL}/api/v1/chat/sessions/{sess_id}/messages' if sess_id else f'{BASE_URL}/api/v1/chat'
            res = requests.post(url, json=msg_payload, headers=headers, timeout=180)
            elapsed = round(time.time() - t0, 2)
            data = res.json().get('data', {})
            tools = data.get('tools_used') or []
            tool_names = [t.get('tool') for t in tools]
            citations = []
            for t in tools:
                c_list = ((t.get('result') or {}).get('citations') or [])
                citations.extend(c_list)

            entry = {
                'q_num': i,
                'question': q,
                'provider_requested': provider,
                'elapsed_seconds': elapsed,
                'http_status': res.status_code,
                'model_used': data.get('model'),
                'provider_recorded': data.get('provider'),
                'status': data.get('status', 'success' if res.status_code == 200 else 'error'),
                'tools_used': tool_names,
                'citations': citations,
                'reply': data.get('message') or data.get('content') or '',
            }
            results[provider].append(entry)
            print(f"Status: {res.status_code} | Provider: {entry['provider_recorded']} | Model: {entry['model_used']} | Elapsed: {elapsed}s")
            print(f"Tools Used: {tool_names}")
            if citations:
                print(f"Citations: {citations[:2]}")
            snippet = entry['reply'].replace('\n', ' ')[:160]
            print(f"Reply: {snippet}...")
        except Exception as e:
            print(f"Error executing Q{i}: {e}")
            results[provider].append({'q_num': i, 'question': q, 'error': str(e)})

os.makedirs('scratch', exist_ok=True)
with open('scratch/live_chat_comparison_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)
print('\nSuccessfully saved test results to scratch/live_chat_comparison_results.json')
