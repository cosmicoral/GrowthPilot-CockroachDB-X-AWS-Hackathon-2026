# GrowthPilot-CockroachDB-X-AWS-Hackathon-2026
Persistent-memory AI growth agent built with CockroachDB, MCP and multi-agent workflows.

<div align="center">

# GrowthPilot

### Autonomous AI GTM Engineer with Persistent Memory

**Plan. Execute. Learn. Remember. Grow.**

Built for the CockroachDB AI Agent Hackathon 2026

</div>

---

# Overview

GrowthPilot is an autonomous AI Go-to-Market (GTM) Engineer that helps founders launch products from idea to growth.

Unlike traditional AI assistants that forget every conversation, GrowthPilot continuously builds long-term business memory.

It researches markets, identifies customer segments, generates launch strategies, writes marketing content, tracks outreach, analyses performance, reflects on previous launches, and improves future decisions through persistent memory.

Instead of simply answering questions, GrowthPilot behaves like an AI growth teammate that becomes smarter after every interaction.

---

# Why?

Every startup founder repeats the same work:

- researching competitors
- identifying customer personas
- writing launch posts
- tracking outreach
- analysing metrics
- remembering what worked

Today's AI tools generate content but forget everything after each session.

GrowthPilot changes that.

Every decision, experiment, customer interaction and campaign becomes part of a continuously evolving company memory.

---

# Demo Scenario

Imagine launching a new product.

You tell GrowthPilot:

> "I want to launch Mosaic Kitchen."

GrowthPilot automatically:

✅ researches competitors

✅ builds customer personas

✅ identifies positioning

✅ creates launch strategies

✅ generates launch content

✅ manages outreach

✅ stores every interaction

✅ reflects on campaign performance

Next week, instead of starting from scratch, GrowthPilot remembers:

- previous campaigns
- successful messaging
- customer feedback
- contacted users
- conversion rates
- product evolution

The AI grows alongside your company.

---

# Core Features

## Persistent Company Memory

Every interaction is remembered.

Examples include:

- customer conversations
- launch history
- campaign performance
- competitor research
- product decisions
- founder preferences

Memory survives across sessions.

---

## AI Market Research

Automatically researches:

- competitors
- Reddit discussions
- Product Hunt launches
- GitHub projects
- industry trends
- user pain points

Results become searchable company knowledge.

---

## Customer Persona Builder

Automatically generates:

- ICPs
- customer personas
- pain points
- buying motivations
- objections
- preferred channels

---

## Content Generation

Creates marketing assets including:

- LinkedIn posts
- X threads
- newsletters
- launch announcements
- landing page copy
- cold emails
- blog articles

---

## Outreach Assistant

Tracks:

- leads
- conversations
- follow-ups
- reply history
- relationship status

GrowthPilot never forgets previous interactions.

---

## Analytics Agent

Collects and analyses:

- website traffic
- campaign metrics
- GitHub stars
- signups
- conversion rates

Generates daily insights.

---

## Reflection Engine

At the end of every day GrowthPilot performs self-reflection.

It identifies:

- what worked
- what failed
- experiments worth repeating
- recommendations for future launches

These reflections become long-term memory.

---

# Multi-Agent Architecture

```
                    User
                      │
              Planner Agent
                      │
 ┌──────────┬─────────┼──────────┬─────────────┐
 │          │         │          │             │
Research   Strategy   ICP      Content    Outreach
 Agent      Agent    Agent      Agent       Agent
 │
 └──────────────┬────────────────────────────┐
                │
          Analytics Agent
                │
         Reflection Agent
                │
        Memory Retrieval Layer
                │
        CockroachDB + pgvector
                │
          Persistent Memory
```

---

# Memory Architecture

GrowthPilot stores multiple memory types.

## Episodic Memory

Daily events.

Example:

- launched on Reddit
- received 15 comments
- gained 120 users

---

## Semantic Memory

Long-term knowledge.

Examples:

- product positioning
- customer personas
- competitor database

---

## User Memory

Stores founder preferences.

Example:

- prefers LinkedIn launches
- focuses on AI startups
- building Mosaic Kitchen

---

## Task Memory

Tracks:

- completed tasks
- pending work
- blocked items

---

## Reflection Memory

Stores lessons learned after every campaign.

Examples:

- Reddit generated highest conversions
- Product Hunt launch underperformed
- Email subject line increased CTR

---

# Tech Stack

## Frontend

- React
- TypeScript
- Tailwind CSS
- shadcn/ui

## Backend

- FastAPI
- Python

## AI

- OpenAI / Claude
- LangChain
- MCP
- Tool Calling

## Memory

- CockroachDB Cloud
- pgvector

## Infrastructure

- AWS Lambda
- S3
- Bedrock (optional)
- CloudWatch

---

# MCP Workflow

```
User Request

↓

Planner Agent

↓

Tool Selection

↓

MCP Server

↓

CockroachDB

↓

Memory Retrieval

↓

LLM Reasoning

↓

Agent Response

↓

Memory Extraction

↓

CockroachDB Update
```

GrowthPilot does not simply answer questions.

Every conversation updates long-term business memory.

---

# Example Workflow

Founder:

> Launch Mosaic Kitchen.

GrowthPilot automatically:

1. Research competitors

2. Build ICP

3. Generate GTM strategy

4. Create launch content

5. Schedule outreach

6. Save company knowledge

7. Monitor campaign

8. Reflect on performance

9. Improve future launches

---

# Future Roadmap

## Phase 1

- Persistent Memory
- Research Agent
- Strategy Agent

## Phase 2

- Outreach Agent
- CRM Integration
- Analytics

## Phase 3

- Autonomous Launches
- Multi-product Memory
- Company Knowledge Graph

---

# Vision

GrowthPilot is not designed to replace marketers.

It is designed to become an AI growth teammate that continuously learns alongside founders.

Instead of forgetting every conversation, it builds an evolving memory of products, customers, experiments and decisions—helping startups compound knowledge over time.