"""
Batch test script - runs many symptom descriptions at once and prints
results, so you can review accuracy without typing each one manually.

Run with: python test_symptoms.py
"""

from app_core import load_knowledge_base, get_response

TEST_CASES = [
    "my cow's belly is swollen and it won't eat",
    "the cow's tummy looks big and it's kicking at its stomach",   # tests fuzzy match
    "the cow's udder is hot and swollen and milk looks clumpy",
    "my cow is limping and there's a bad smell from its foot",
    "my chickens have twisted necks and are gasping for air",
    "my goat's belly is swollen and it keeps lying down",
    "my goat has watery diarrhea for two days",
    "the animal has lost a lot of weight and its gums look pale",
    "my cow is coughing with fast breathing and a runny nose",
    "one of my goats has a cloudy, red eye",
    "my goat has been straining to give birth for hours with no progress",
    "my chickens stopped laying eggs this week",
    "I see ticks on my goat and it keeps scratching",
    "my goat's ear looks torn",                                    # not in KB - should be honest
    "my cow suddenly can't stand up at all",                       # not in KB - should be honest
    "the chicken's feathers look dull",                            # ambiguous/not in KB
    "my goat is drooling a lot and won't stop",                    # not in KB
    "my cow has a swollen jaw",                                    # not in KB
]


def run_tests():
    kb = load_knowledge_base()
    print(f"Running {len(TEST_CASES)} test cases...\n")
    print("=" * 70)

    for i, symptom in enumerate(TEST_CASES, 1):
        print(f"\n[{i}] Input: {symptom}")
        answer = get_response(symptom, kb)
        print(f"Response: {answer}")
        print("-" * 70)

    print("\nDone. Review above for:")
    print("- Emergencies (bloat, Newcastle, pneumonia, dystocia) clearly flagged")
    print("- Non-KB cases (ear injury, can't stand, dull feathers, drooling,")
    print("  swollen jaw) honestly admitting no info, not guessing")
    print("- No leftover trailing/garbage text after answers")


if __name__ == "__main__":
    run_tests()
