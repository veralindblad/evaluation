import os
import json
import requests
from openai import OpenAI

# =========================
# CONFIG
# =========================

LOCAL_API_URL = "http://localhost:8000/api/v1/ask"
LOCAL_API_KEY = "DIN_LOKALA_API_NYCKEL"

JUDGE_MODEL = "gpt-5.4"

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# =========================
# DATA
# =========================

cases = [
    {
        "id": "case_1",
        "question": "En 67-årig man har bröstsmärta och kallsvettas. Vad bör han göra?",
        "reference": "Misstänk akut hjärtsjukdom. Patienten ska söka akut vård direkt eller ringa 112."
    },
    {
        "id": "case_2",
        "question": "Ett barn har feber i två dagar men leker och dricker. När ska man söka vård?",
        "reference": "Sök vård vid försämring, slöhet, andningsbesvär, uttorkning eller långvarig feber."
    }
]


# =========================
# 1. CALL AGENT
# =========================

def ask_agent(question):
    headers = {
        "Authorization": f"Bearer {LOCAL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "question": question
    }

    response = requests.post(LOCAL_API_URL, headers=headers, json=payload)

    data = response.json()

    # ändra här om ditt API använder annat namn
    return data.get("answer", "")


# =========================
# 2. JUDGE (ACCURACY ONLY)
# =========================

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "accuracy": {"type": "number"},
        "pass_fail": {
            "type": "string",
            "enum": ["pass", "fail"]
        },
        "reasoning": {"type": "string"}
    },
    "required": ["accuracy", "pass_fail", "reasoning"],
    "additionalProperties": False
}


def judge_accuracy(question, reference, answer):
    prompt = f"""
Du är en strikt medicinsk examinator.

Bedöm ENDAST hur korrekt svaret är jämfört med facit.

Regler:
- accuracy: mellan 0.0 och 1.0
- 1.0 = helt korrekt
- 0.0 = helt fel
- pass = om svaret är medicinskt korrekt
- fail = om det finns tydliga fel

FRÅGA:
{question}

FACIT:
{reference}

SVAR:
{answer}
"""

    response = client.responses.create(
        model=JUDGE_MODEL,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "accuracy_eval",
                "schema": JUDGE_SCHEMA,
                "strict": True
            }
        }
    )

    return json.loads(response.output_text)


# =========================
# 3. RUN
# =========================

results = []

for case in cases:
    print(f"Kör: {case['id']}")

    answer = ask_agent(case["question"])

    judgment = judge_accuracy(
        case["question"],
        case["reference"],
        answer
    )

    results.append({
        "id": case["id"],
        "question": case["question"],
        "reference": case["reference"],
        "answer": answer,
        "evaluation": judgment
    })


# =========================
# 4. SAVE
# =========================

with open("results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)


# =========================
# 5. SUMMARY
# =========================

scores = [r["evaluation"]["accuracy"] for r in results]

avg = sum(scores) / len(scores)
pass_rate = sum(1 for r in results if r["evaluation"]["pass_fail"] == "pass") / len(results)

print("\nRESULTAT:")
print(f"Average accuracy: {avg:.2f}")
print(f"Pass rate: {pass_rate:.2%}")