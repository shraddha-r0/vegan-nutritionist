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

## 🧠 Core Features (MVP)

### ⭐ Natural Language Meal Logging  
Type a meal the way you would text a friend.  
The system extracts the meal details and nutritional values automatically.

### ⭐ Nutritional Recordkeeping  
Each meal is stored with structured macro and micro nutrient values, making summaries easy and accurate.

### ⭐ Weekly Nutrition Insights  
The assistant can answer natural questions like:  
“Show me my total iron this week.”  
“Did I eat enough protein the last three days?”  
These are translated into SQL queries in the background.

### ⭐ Grounded Micronutrient Context  
A small metadata layer provides educational context — what nutrients do, vegan food sources, and recommended daily ranges — helping you interpret your intake meaningfully.

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

This MVP sets the foundation for richer features:

- Voice-based logging  
- Ingredient-level parsing  
- Personalized nutrient targets  
- Diet insights based on goals  
- Vegan food substitutions  
- Trend visualizations  
- Health-aware recommendation engine  

These will be added iteratively after the capstone.

---

## 💜 Author

**Shraddha Ramesh**  
GenAI Engineer • Data Scientist • Vegan • Lifelong Learner  
