import os
import json

# Target directory
base_dir = os.path.dirname(os.path.abspath(__file__))
scenarios_dir = os.path.join(base_dir, "scenarios")
os.makedirs(scenarios_dir, exist_ok=True)

categories = [
    "architecture",
    "planning",
    "rag",
    "memory",
    "guardrails",
    "software_engineering",
    "security",
    "github",
    "pdf",
    "long_context",
    "parallel_execution",
    "provider_routing",
]


def generate_questions(cat):
    return [
        {
            "scenario_id": f"{cat}_{i:03d}",
            "difficulty": "hard",
            "expected_capability": cat,
            "expected_agent": f"{cat}_agent",
            "expected_provider": "gemini",
            "expected_tools": ["search"] if "rag" in cat else [],
            "expected_guardrails": ["pii_filter"] if cat == "security" else [],
            "query": f"Sample query for {cat} number {i}?",
            "ground_truth": f"Expected valid output for {cat}.",
        }
        for i in range(1, 11)  # 10 questions each
    ]


for cat in categories:
    data = generate_questions(cat)
    file_path = os.path.join(scenarios_dir, f"{cat}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

print(
    f"Generated {len(categories) * 10} questions across {len(categories)} capability files in {scenarios_dir}"
)
