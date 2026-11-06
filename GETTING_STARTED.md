# Getting Started

New here? Start with the [project overview](README.md), then choose one of the [seven topic areas](README.md#explore-the-seven-core-areas).

## In five minutes
1. Read the project's [design principles](architecture/design-principles.md).
2. Open a topic that matches your question.
3. Check whether a statement is a **verified capability**, **proposed design**, or **experimental observation**.
4. Read the [compatibility guide](architecture/chatgpt-compatibility.md) before assuming a ChatGPT feature exists in your plan or client.
5. Use the [document template](templates/document-template.md) if you want to add a concept.

## How to find things
- **What is known?** Go to [Research](research/README.md) or [Knowledge](knowledge/README.md).
- **What might work?** Go to [Concepts](concepts/README.md).
- **How should I ask?** Go to [Prompts](prompts/README.md).
- **How do context and preferences work?** Go to [Memory](memory/README.md) and [Context Engineering](context-engineering/README.md).
- **How should answers look?** Go to [Intelligent UI](intelligent-ui/README.md).
- **How do we check quality?** Go to [Quality](quality/quality-standards.md).

This repository is documentation, **not** an installed ChatGPT plugin, an active memory synchronization service, or a model control system.

## Optional local CLI setup

If you are using the offline-first Python generator runtime, begin with `python intel.py setup` for a read-only preview, then run `python intel.py setup --apply` to initialize language preferences. Use `python intel.py config validate` and `python intel.py config show` to diagnose settings. On Windows, `intel.cmd` forwards the same commands. [Configuration and safe import/export](architecture/local-configuration.md).

## Local Python CLI quick start

The local executable tooling is distinct from the ChatGPT conversation convention. From a trusted checkout run python intel.py help, python intel.py --json capabilities, and python intel.py setup (read-only). On Windows use intel.cmd help instead. To save language preferences, explicitly run python intel.py setup --apply. For details see [Local CLI](LOCAL_CLI.md), [Migration Guide](guides/local-cli-migration.md) and [Troubleshooting](guides/local-cli-troubleshooting.md).
