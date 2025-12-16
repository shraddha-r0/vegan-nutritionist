# 🌱 Vegan Nutrition Assistant  
*A minimal, AI-powered vegan meal tracking prototype built for my GenAI Engineering capstone.*

---

## 📌 Overview

The Vegan Nutrition Assistant is a lightweight prototype that lets users log meals in natural language and instantly receive a structured breakdown of macro and micro nutrients. It’s designed to reduce the friction of food tracking while offering clarity on nutritional intake — especially for vegan diets, where micronutrients matter as much as macros.

The project focuses on **simplicity, accuracy, and grounded AI responses**, avoiding unnecessary complexity while still demonstrating strong GenAI engineering principles.

---

## 🎯 Product Vision

To create a **personalized vegan nutritionist** that understands plain-language meal descriptions, stores them cleanly, and provides meaningful nutritional insights — without requiring users to manually input every detail or rely on expensive nutrition consultations.

Phase 1 aims to:

- Make meal logging feel natural and conversational  
- Automatically extract relevant nutritional data  
- Summarize weekly intake to reveal trends and deficiencies  
- Ground AI outputs in trusted nutritional references  
- Keep the system simple, transparent, and easy to extend  

The long-term vision is a personal nutrition companion that understands your routine, adapts to your goals, and keeps you informed about your health — all while staying vegan-aware.

---

## 🧠 Core Features (Current Build)

| Capability | What it does |
| --- | --- |
| **LLM intent routing** | Every user message is classified (LOG / QUERY / GENERAL) so the assistant knows when to add a meal, analyze existing logs with SQL, or give advice. |
| **Guided meal logging** | When you say “I ate…”, the assistant asks clarifying questions (portion sizes, timing, meal type), uses an LLM to estimate macros/micros, previews the row, and only writes to SQLite after you confirm. |
| **SQL-backed meal insights** | Questions like “What did I eat for dinner on 1st April 2025?” or “How close was my protein last week?” trigger an LLM-to-SQL chain, run directly against `backend/data/nutrition.db`, and show both the query and tabular results. |
| **Date understanding** | Natural phrases (“yesterday”, “last week”, “April 2nd”) are normalized to ISO ranges before SQL planning, keeping analytics grounded. |
| **Nutrition profile grounding** | A rich YAML profile defines the user’s goals, preferences, and system prompt so general advice always stays on-brand for Shraddha. |
| **Streamlit chat UI** | Scrollable chat history, sticky input, inline loaders, and expandable panels for SQL analysis or meal-entry previews. |

---

## 🧭 Design Philosophy

This prototype is intentionally minimal:

- **No vector database**  
- **No over-engineered architecture**  
- **No voice or image input (yet)**  
- **No multi-agent systems**  
- **Direct text-to-SQL path (no REST API)** — the Streamlit client prompts the LLM for SQLite queries and executes them locally for grounded answers.

Just clean structured data, thoughtful prompt engineering, and clear reasoning about when to use (or *not* use) different GenAI components.

The project emphasizes **clarity over complexity** and showcases the ability to make strong technical decisions based on actual product needs, not trends.

---

## 🚀 Future Extensions

With the foundations in place, the next steps are clear:

- Voice-based logging and mobile capture  
- Ingredient-level parsing tied to official nutrition data sources  
- Editing & deleting existing meals directly from the chat  
- Personalized nutrient targets per training block or health goal  
- Progress dashboards and habit nudges  
- Integrations with wearable/health APIs  

---

## 💜 Author

**Shraddha Ramesh**  
GenAI Engineer • Data Scientist • Vegan • Lifelong Learner  
