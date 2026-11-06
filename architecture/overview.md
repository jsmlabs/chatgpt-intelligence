---
title: Architecture Overview
status: proposed
version: 0.2.0
updated: 2026-11-06
classification: proposed-design
---

# Architecture Overview

## What is this?
A readable map of how the project's **seven knowledge areas** connect. This is a reference framework, not a claim about ChatGPT's hidden implementation.

## Seven core areas
- [Research](../research/README.md) - investigate and verify.
- [Concepts](../concepts/README.md) - propose and compare ideas.
- [Prompts](../prompts/README.md) - design reusable instructions.
- [Knowledge](../knowledge/README.md) - manage reference facts and sources.
- [Memory](../memory/README.md) - explore remembered preferences, controls, and limitations.
- [Context Engineering](../context-engineering/README.md) - select task-relevant information.
- [Intelligent UI](../intelligent-ui/README.md) - present information effectively.

## Shared architecture specifications
1. [Design principles](design-principles.md) - project-wide standards.
2. [Response lifecycle](response-lifecycle.md) - a conceptual response workflow.
3. [Instruction and conflict resolution](instruction-and-conflict-resolution.md) - instruction authority and ambiguity.
4. [Context and information boundaries](context-and-information-boundaries.md) - what is known, remembered, relevant, and authorized.
5. [Intelligent UI decision model](intelligent-ui-decision-model.md) - choose useful presentation.
6. [Documentation contracts](documentation-contracts.md) - naming, metadata, and ownership.
7. [ChatGPT compatibility](chatgpt-compatibility.md) - version and evidence boundaries.

## Conversational use
- [Activation and source resolution](activation-and-source-resolution.md) - the proposed `/INTEL` contract and evidence gates.
- [Command reference](../COMMANDS.md) - user-facing command grammar.

## Verification and delivery
- [Quality standards](../quality/quality-standards.md)
- [Foundation verification](../quality/foundation-verification.md)
- [Roadmap](../ROADMAP.md)

## Scope and limits
The repository documents research and design. It does not implement an orchestrator, mutate ChatGPT memory, or grant authority to override product restrictions.
