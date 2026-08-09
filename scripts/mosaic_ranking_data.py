"""Mosaic Kitchen founder memories used to evaluate hybrid ranking.

Entries with ``source_type=repo_fact`` are derived from the public Mosaic
Kitchen repository. Entries with ``source_type=simulated_eval`` are plausible
founder/customer events created only for ranking evaluation; they are not real
product metrics.
"""


EVAL_MEMORIES = [
    {
        "key": "founder_product_vision",
        "memory_type": "user",
        "content": (
            "The founder is building Mosaic Kitchen, an AI-powered multicultural "
            "meal-planning and grocery assistant for diverse households in the UK."
        ),
        "importance": 1.0,
        "age_days": 90,
        "metadata": {"source_type": "repo_fact", "topic": "vision"},
    },
    {
        "key": "founder_research_led",
        "memory_type": "user",
        "content": (
            "The founder wants product decisions to remain grounded in doctoral "
            "research on healthy eating, food waste, food culture, and household routines."
        ),
        "importance": 0.9,
        "age_days": 75,
        "metadata": {"source_type": "repo_fact", "topic": "founder_preference"},
    },
    {
        "key": "founder_bilingual",
        "memory_type": "user",
        "content": (
            "The founder considers English and Simplified Chinese support a core product "
            "requirement rather than a later localisation feature."
        ),
        "importance": 0.9,
        "age_days": 45,
        "metadata": {"source_type": "repo_fact", "topic": "language"},
    },
    {
        "key": "founder_web_before_ios",
        "memory_type": "user",
        "content": (
            "The founder wants to validate the core value with a React web MVP before "
            "investing in the native SwiftUI iOS application."
        ),
        "importance": 0.8,
        "age_days": 30,
        "metadata": {"source_type": "repo_fact", "topic": "roadmap"},
    },
    {
        "key": "target_users",
        "memory_type": "semantic",
        "content": (
            "Mosaic Kitchen's primary MVP users are Chinese households in the UK, "
            "international students, Asian families, and busy professionals."
        ),
        "importance": 1.0,
        "age_days": 60,
        "metadata": {"source_type": "repo_fact", "topic": "icp"},
    },
    {
        "key": "research_problem_insight",
        "memory_type": "semantic",
        "content": (
            "Healthy and sustainable eating often breaks down because of limited time, "
            "disrupted routines, cultural preferences, and practical household constraints, "
            "not simply because people lack nutritional knowledge."
        ),
        "importance": 1.0,
        "age_days": 80,
        "metadata": {"source_type": "repo_fact", "topic": "customer_problem"},
    },
    {
        "key": "mvp_feature_scope",
        "memory_type": "semantic",
        "content": (
            "The web MVP combines AI meal planning, grocery-list generation, cultural "
            "cuisine preferences, budget-aware planning, manual fridge inventory, and "
            "food-waste reduction suggestions."
        ),
        "importance": 0.9,
        "age_days": 40,
        "metadata": {"source_type": "repo_fact", "topic": "mvp"},
    },
    {
        "key": "product_value_proposition",
        "memory_type": "semantic",
        "content": (
            "Mosaic Kitchen aims to help multicultural households eat more healthily, "
            "spend less on groceries, reduce avoidable food waste, and preserve culturally "
            "relevant meals."
        ),
        "importance": 0.9,
        "age_days": 50,
        "metadata": {"source_type": "repo_fact", "topic": "positioning"},
    },
    {
        "key": "demo_household_profile",
        "memory_type": "semantic",
        "content": (
            "The current demo household has two people in London, combines Chinese, "
            "British, and Indian food cultures, requires halal meals with no pork, and "
            "uses an eighty-pound weekly grocery budget."
        ),
        "importance": 0.7,
        "age_days": 20,
        "metadata": {"source_type": "repo_fact", "topic": "demo_profile"},
    },
    {
        "key": "pricing_hypothesis",
        "memory_type": "semantic",
        "content": (
            "The current pricing mock-up proposes a free starter plan, a 3.99 pound monthly "
            "Premium plan, and a 7.99 pound Premium Plus plan with AI fridge scanning and "
            "household intelligence."
        ),
        "importance": 0.6,
        "age_days": 10,
        "metadata": {"source_type": "repo_fact", "topic": "pricing"},
    },
    {
        "key": "current_backend_work",
        "memory_type": "task",
        "content": (
            "Current backend priorities are structured JSON output, Supabase integration, "
            "the user profile model, and the inventory-management API."
        ),
        "importance": 0.8,
        "age_days": 3,
        "metadata": {"source_type": "repo_fact", "topic": "engineering"},
    },
    {
        "key": "next_product_milestones",
        "memory_type": "task",
        "content": (
            "The next product milestones are the React frontend, bilingual interface, "
            "fridge inventory, grocery-list page, and a later SwiftUI TestFlight release."
        ),
        "importance": 0.8,
        "age_days": 7,
        "metadata": {"source_type": "repo_fact", "topic": "roadmap"},
    },
    {
        "key": "interview_cultural_relevance",
        "memory_type": "episodic",
        "content": (
            "In a simulated round of ten customer interviews, eight participants said "
            "mainstream meal-planning apps did not reflect the dishes they actually cook "
            "at home."
        ),
        "importance": 0.9,
        "age_days": 30,
        "metadata": {"source_type": "simulated_eval", "topic": "customer_interview"},
    },
    {
        "key": "interview_budget_pressure",
        "memory_type": "episodic",
        "content": (
            "In a simulated interview exercise, international students consistently asked "
            "for weekly budget limits and lower-cost ingredient substitutions."
        ),
        "importance": 0.8,
        "age_days": 14,
        "metadata": {"source_type": "simulated_eval", "topic": "customer_interview"},
    },
    {
        "key": "prototype_bilingual_result",
        "memory_type": "episodic",
        "content": (
            "A simulated prototype test found that bilingual ingredient names helped users "
            "confirm unfamiliar UK grocery labels and complete meal-plan setup more easily."
        ),
        "importance": 0.8,
        "age_days": 7,
        "metadata": {"source_type": "simulated_eval", "topic": "prototype_test"},
    },
    {
        "key": "prototype_pantry_friction",
        "memory_type": "episodic",
        "content": (
            "A simulated usability session found that manually entering a full pantry was "
            "the largest source of onboarding friction, especially for busy professionals."
        ),
        "importance": 0.9,
        "age_days": 5,
        "metadata": {"source_type": "simulated_eval", "topic": "usability"},
    },
    {
        "key": "pricing_test_result",
        "memory_type": "episodic",
        "content": (
            "In a simulated pricing test, participants understood the 3.99 pound Premium "
            "offer better when it emphasised unlimited planning, budget optimisation, and "
            "expiry-alert recipes."
        ),
        "importance": 0.7,
        "age_days": 2,
        "metadata": {"source_type": "simulated_eval", "topic": "pricing_test"},
    },
    {
        "key": "reflection_cultural_trust",
        "memory_type": "reflection",
        "content": (
            "Culturally specific dishes and bilingual ingredient language build more trust "
            "than generic claims about AI personalisation."
        ),
        "importance": 1.0,
        "age_days": 12,
        "metadata": {"source_type": "simulated_eval", "topic": "positioning"},
    },
    {
        "key": "reflection_focus_current_value",
        "memory_type": "reflection",
        "content": (
            "Near-term messaging should lead with culturally relevant meal planning, grocery "
            "budget control, and food-waste reduction; AI fridge scanning is compelling but "
            "belongs to a later product stage."
        ),
        "importance": 0.9,
        "age_days": 4,
        "metadata": {"source_type": "simulated_eval", "topic": "gtm_strategy"},
    },
    {
        "key": "reflection_reduce_setup_friction",
        "memory_type": "reflection",
        "content": (
            "The onboarding flow should let users start with a small set of expiring items "
            "instead of requiring a complete pantry, reducing setup work before the first "
            "useful recommendation."
        ),
        "importance": 0.9,
        "age_days": 1,
        "metadata": {"source_type": "simulated_eval", "topic": "product_strategy"},
    },
]


EVAL_QUERIES = [
    {
        "query": "Who should Mosaic Kitchen target for the first MVP?",
        "relevant": ["target_users"],
    },
    {
        "query": "Why do users struggle to maintain healthy and sustainable eating?",
        "relevant": ["research_problem_insight"],
    },
    {
        "query": "Which features belong in the first web release?",
        "relevant": ["mvp_feature_scope", "founder_web_before_ios"],
    },
    {
        "query": "Which languages must the product support first?",
        "relevant": ["founder_bilingual"],
    },
    {
        "query": "What did customer discovery suggest about cultural relevance?",
        "relevant": ["interview_cultural_relevance", "reflection_cultural_trust"],
    },
    {
        "query": "What do international students need from meal planning?",
        "relevant": ["interview_budget_pressure", "target_users"],
    },
    {
        "query": "What is causing friction during pantry onboarding?",
        "relevant": ["prototype_pantry_friction", "reflection_reduce_setup_friction"],
    },
    {
        "query": "How should Premium be positioned in the pricing page?",
        "relevant": ["pricing_test_result", "pricing_hypothesis"],
    },
    {
        "query": "Should we promote AI fridge scanning in the current launch?",
        "relevant": ["reflection_focus_current_value", "next_product_milestones"],
    },
    {
        "query": "What engineering work is currently unfinished?",
        "relevant": ["current_backend_work", "next_product_milestones"],
    },
]
