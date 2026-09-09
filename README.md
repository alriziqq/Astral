# Astral

Astral is a local-first AI agent designed to act as a personal assistant on your computer.

Instead of functioning as a chatbot that only generates text, Astral can interact with your workspace, search the internet, execute tools, manipulate files, and chain multiple actions together to complete tasks.

Astral is built around a simple idea:

> An AI assistant should be able to do things, not just talk about doing them.

---

## What Is Astral?

Astral is an experimental AI agent and personal assistant built with Python and a local LLM backend.

It connects a language model to a collection of tools that allow it to interact with the environment around it.

Depending on the enabled tools, Astral can:

* Understand natural-language instructions
* Search the internet
* Inspect files and directories
* Read and write files
* Create directories
* Move files
* Delete files
* Chain multiple tool calls together
* Execute shell commands
* Interact with applications
* Maintain persistent memory
* Work with a dedicated workspace
* Operate as a continuously available desktop assistant

The goal isn't to build another chat interface.

The goal is to create an agent that can actually operate a computer environment while remaining understandable, modular, and controllable.

---

## Why Astral?

Traditional AI chat interfaces are mostly request-response systems.

You ask something.

The model answers.

You perform the action yourself.

Astral is designed around a different workflow.

You give Astral an objective.

Astral determines what tools are required, executes them, observes the results, and continues working until the task is complete or it needs additional input.

For example:

```text
You:
Organize the files in my Downloads folder.

Astral:
→ Inspect Downloads
→ Identify files
→ Create appropriate directories
→ Move files
→ Verify the result
→ Report what changed
```

The important part is not that the model can generate the words "I can do that."

The important part is that it can actually perform the operations.

---

## Core Architecture

Astral follows an agent-based architecture where the language model acts as the reasoning layer while external tools provide the ability to interact with the environment.

A simplified version of the architecture looks like this:

```text
                    ┌─────────────────┐
                    │      User       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     Astral      │
                    │      Agent      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │       LLM       │
                    │ Reasoning Layer │
                    └────────┬────────┘
                             │
                    Tool Selection
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
       Filesystem        Internet          Shell
            │                │                │
            └────────────────┼────────────────┘
                             │
                             ▼
                    Tool Execution Result
                             │
                             ▼
                    ┌─────────────────┐
                    │       LLM       │
                    │   Next Action   │
                    └────────┬────────┘
                             │
                             ▼
                    Final Response
```

This allows Astral to operate as a loop rather than a single model call.

---

## Agent Loop

The core agent loop can be thought of as:

```text
Receive Task
     ↓
Understand Task
     ↓
Decide Whether a Tool Is Required
     ↓
Select Tool
     ↓
Execute Tool
     ↓
Receive Result
     ↓
Evaluate Result
     ↓
Continue or Finish
```

This enables tool chaining.

For example, a request such as:

```text
Find my physics notes and move them into a new folder called School.
```

may require several operations:

```text
List Directory
      ↓
Inspect Files
      ↓
Identify Physics Notes
      ↓
Create Directory
      ↓
Move Files
      ↓
Verify
      ↓
Respond
```

The model doesn't need a hardcoded workflow for every possible task.

Instead, the agent can dynamically determine which tools it needs.

---

## Features

### Internet Access

Astral can access the internet through its search tooling.

This allows the agent to retrieve information that isn't available in its local model context.

The current setup uses a self-hosted search layer based around SearXNG.

Example:

```text
You:
Search for the latest Python release and summarize the important changes.

Astral:
→ Search web
→ Inspect results
→ Extract relevant information
→ Summarize findings
```

The search system is intentionally separated from the core agent so it can be replaced or extended later.

---

### Filesystem Access

Astral includes filesystem tools for interacting with a workspace.

Currently supported operations include:

```text
list_directory
read_file
write_file
create_directory
delete_file
move_file
```

This gives Astral the ability to work with actual files rather than merely describing what the user should do.

Example:

```text
You:
Create a folder called projects and move my Python files there.

Astral:
→ Inspect current directory
→ Create projects/
→ Identify Python files
→ Move files
→ Verify
```

---

### Workspace Awareness

Astral is designed around the concept of a workspace.

Instead of treating every request as an isolated chat message, the agent can understand the environment it is currently working inside.

This becomes especially useful for development workflows.

For example:

```text
You:
Fix the bug in the agent.

Astral:
→ Inspect project
→ Locate relevant files
→ Read implementation
→ Identify issue
→ Modify code
→ Run verification
```

The workspace becomes part of the agent's operational context.

---

### Tool Chaining

One of the most important parts of Astral is tool chaining.

A tool call doesn't necessarily end the agent's execution.

The result of one operation can become the input for the next operation.

For example:

```text
Search
  ↓
Read Result
  ↓
Extract Information
  ↓
Write Report
```

Or:

```text
List Files
  ↓
Read File
  ↓
Modify File
  ↓
Save File
```

This allows Astral to perform multi-step tasks without requiring the user to manually direct every individual operation.

---

### Shell Access

Astral is being expanded with shell access so it can interact with the operating system beyond filesystem operations.

This enables workflows such as:

```text
Run a program
Install a dependency
Inspect system information
Execute development commands
Run tests
Build a project
```

Shell access is treated as a separate capability because it provides significantly broader system interaction than ordinary file operations.

---

### Application Control

Astral is designed to eventually control desktop applications.

This allows natural-language commands such as:

```text
Open VS Code
Close the browser
Launch a program
```

to become actual system actions rather than instructions for the user.

Application control is part of Astral's larger goal of becoming a computer-level personal assistant.

---

### Memory

Astral is designed to support persistent memory.

Memory allows information from previous interactions to remain available instead of disappearing when a conversation ends.

Potential uses include:

```text
User Preferences
Important Projects
Recurring Tasks
Long-Term Goals
Workflow Preferences
Context About Ongoing Projects
```

Memory is intentionally separated from the core agent so that it can evolve independently.

---

## Local-First Design

Astral is designed with a strong preference toward local execution.

The language model can run locally through a compatible LLM server such as LM Studio or another OpenAI-compatible backend.

A typical setup looks like:

```text
┌───────────────────────────┐
│          Astral           │
│           Python          │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│      Local LLM Server     │
│    OpenAI-Compatible API  │
└─────────────┬─────────────┘
              │
              ▼
        Local Language Model
```

This approach provides several advantages:

* Lower dependency on external AI APIs
* Greater control over the model
* Local processing
* Easier experimentation
* Customizable model selection
* Potentially lower long-term inference cost

Astral can still use external services when a specific tool requires them, such as internet search.

---

## Model Independence

Astral isn't intended to be permanently tied to a single model.

The agent communicates with the LLM through an OpenAI-compatible interface.

This makes it possible to experiment with different models without rebuilding the entire application.

Conceptually:

```text
Astral
   │
   ▼
OpenAI-Compatible API
   │
   ├── Local Model
   ├── LM Studio
   ├── Ollama
   └── Other Compatible Backend
```

The agent layer and model layer remain separate.

---

## Tool Architecture

Tools are exposed to the model through structured definitions.

Conceptually:

```python
tool = {
    "name": "read_file",
    "description": "Read the contents of a file",
    "parameters": {
        ...
    }
}
```

The model determines when a tool should be used.

Astral then:

1. Receives the tool call
2. Validates the arguments
3. Executes the corresponding function
4. Captures the result
5. Sends the result back to the model
6. Continues the agent loop

This separation makes it possible to add new capabilities without rewriting the entire agent.

---

## Current Tool Ecosystem

Astral currently revolves around several major capability groups.

### Filesystem

```text
list_directory
read_file
write_file
create_directory
delete_file
move_file
```

### Internet

```text
SearXNG Search
```

### System

```text
Shell Execution
Application Control
```

### Memory

```text
Persistent Memory
Context Retrieval
```

### Planning

```text
create_todo
update_todo
delete_todo
list_todos
list_calendar_events
desktop_time
```


The exact available tools depend on the current Astral version and configuration.

---

## Project Structure

The project is organized into separate modules so that the agent, model interface, memory system, and tools can evolve independently.

A simplified structure looks like:

```text
Astral/
|-- Astral.py            entry point, chat loop, slash commands
|-- agent.py             agent loop, tool orchestration, safety gate
|-- llm.py               OpenAI-compatible transport (streaming, tool calls)
|-- config.py            runtime settings, every value env-overridable
|-- ui.py                console rendering helpers
|-- astral.bat           Windows launcher (Docker + SearXNG + Astral)
|-- requirements.txt
|-- LICENSE
|-- README.md
|-- tools/               one module per capability
|   |-- __init__.py      tool registry
|   |-- applications.py  launch, inspect, and close Windows processes
|   |-- filesystem.py    file operations inside allowed roots
|   |-- memory.py        persistent long-term memory
|   |-- planner.py       planning and context budgeting
|   |-- searxng.py       internet search through self-hosted SearXNG
|   `-- shell.py         PowerShell execution behind confirmation
|-- tests/               pytest suite (safety, tools, UI, context budget)
|-- docs/                MODELS.md, DEVELOPMENT_LOG.md
|-- .github/             CONTRIBUTING.md, CODE_OF_CONDUCT.md
`-- data/                runtime state, gitignored, created on first run
```

### Astral.py

The application entry point.

It starts the console session, parses slash commands (`/model`, `/thinking`, `/reasoning`, `/permissions`, `/quit`), and initializes the components Astral needs.

### agent.py

Contains the agent loop and orchestration logic.

This is where Astral decides how to process user requests, which tools may be called, and which actions have to be confirmed first.

### llm.py

Handles communication between Astral and the model backend.

Every provider, local or hosted, goes through one OpenAI-compatible client, so model-specific logic stays isolated from the rest of the application.

### config.py

The single source of runtime settings: allowed filesystem roots, context budget, model endpoints, and credentials.

Every value can be overridden by an environment variable, so nothing secret needs to live in the source code.

### tools/

One module per capability, registered through `tools/__init__.py`.

This acts as the bridge between model-generated tool calls and actual Python functions.

Keeping each tool independent is what lets the capability set grow without the agent loop growing along with it.

### tests/

The pytest suite. It covers the behaviour that must not regress: the path allowlist, write and execution confirmation, tool schema rendering, memory persistence, and context budgeting.

### docs/

Focused guides instead of one endlessly growing README.

---

## Installation

### Requirements

Astral currently expects a Python environment with the required dependencies installed.

A local LLM backend is also required.

For example:

```text
Python 3.x
Local LLM Server
SearXNG
```

Clone the repository:

```bash
git clone <repository-url>
cd astral
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the LLM backend according to the current configuration used by the project.

Then start Astral:

```bash
python Astral.py
```

Or start it with `astral.bat`, which also brings up Docker Desktop and the SearXNG container before launching the agent.

---

## Configuration

Astral uses configuration values for things such as:

```text
LLM Endpoint
Model Name
Workspace Location
Search Endpoint
Memory Configuration
```

Keep environment-specific configuration outside the core agent logic whenever possible.

A typical configuration flow is:

```text
Environment
     ↓
Astral Startup
     ↓
Load Configuration
     ↓
Initialize LLM
     ↓
Initialize Tools
     ↓
Initialize Memory
     ↓
Start Agent
```

---

## Example Interactions

Astral is intended to understand tasks rather than require rigid commands.

### File Management

```text
You:
Show me what's inside my projects folder.
```

Astral can inspect the directory and return its contents.

---

### Creating Files

```text
You:
Create a Python file called test.py with a simple Hello World program.
```

Astral can create the file through its filesystem tooling.

---

### Multi-Step Workflow

```text
You:
Find my physics notes, create a folder called physics, and move them there.
```

Astral may perform:

```text
List Directory
↓
Identify Files
↓
Create Folder
↓
Move Files
↓
Verify
```

---

### Research Workflow

```text
You:
Search the internet for information about Ollama and save a summary into a text file.
```

Possible execution:

```text
Search Web
↓
Inspect Results
↓
Extract Information
↓
Generate Summary
↓
Write File
```

This is the type of workflow Astral is being built around.

---

## Development Philosophy

Astral follows a few principles.

### 1. The Model Should Not Be the Application

The language model is one component of the system.

It should not contain every piece of application logic.

The agent, tools, memory, interfaces, and execution layer should remain modular.

---

### 2. Tools Should Be Composable

Individual tools should solve specific problems.

Rather than creating one giant "do everything" function, Astral exposes smaller capabilities that the agent can combine.

```text
Small Tools
    +
Agent Reasoning
    =
Complex Workflows
```

---

### 3. Observable Behavior

Agent systems can become difficult to debug very quickly.

Astral therefore aims to make execution visible.

Tool calls, processing states, errors, and important execution events should be understandable from the interface.

This makes debugging considerably easier.

---

### 4. Modularity

Astral is still evolving.

Features such as memory, shell access, application control, and voice should be independently replaceable where possible.

This allows experimentation without tightly coupling every component to the agent loop.

---

## Roadmap

The 1.x roadmap focuses on building a complete local computer agent.

### v1.4

Internet + filesystem + workspace + tool chaining

Status:

```text
Completed
```

Current capabilities include:

* Internet search
* Filesystem interaction
* Workspace interaction
* Multiple tool calls
* Chained tool execution

---

### v1.5

Shell access

Planned capabilities:

* Execute shell commands
* Capture command output
* Return execution results to the agent
* Integrate shell execution into tool chaining
* Improve command execution feedback

---

### v1.6

Speech Interface

Planned capabilities:

* Speech input
* Speech-to-text
* Text-to-speech
* Natural voice interaction
* Unified text and voice agent interface

---

### v1.7

Memory

Planned capabilities:

* Persistent memory
* Memory retrieval
* User preferences
* Long-term project context
* Improved continuity between sessions

---

### v1.8

Application Control

Planned capabilities:

* Launch applications
* Close applications
* Interact with desktop workflows
* Integrate application control into the agent loop

---

### v1.9

1.x Refactor and Cleanup

Focus:

* Architecture cleanup
* Code quality
* Stability
* Error handling
* Configuration cleanup
* Documentation
* Performance
* Developer experience

---

### v2.0

The 2.0 direction is intentionally broader.

The long-term objective is to move Astral from an experimental agent into a complete personal computer assistant.

Potential areas include:

```text
Continuous Operation
Proactive Assistance
Deeper Workspace Awareness
Calendar Integration
Task Management
Voice-First Interaction
System Awareness
Automation
Richer Memory
Computer Interaction
```

The exact v2 architecture will depend on what is learned during the 1.x development cycle.

---

## Long-Term Vision

Astral is being built toward a personal assistant that exists as a persistent layer between the user and their computer.

Instead of opening separate applications for every small task, the user should eventually be able to communicate an objective directly.

For example:

```text
"Prepare my workspace for studying."

"Find the notes from yesterday."

"Organize this project."

"Check what I need to do today."

"Open everything I need for this project."

"Research this topic and save the useful information."
```

Astral should be able to understand the intent, determine the necessary actions, perform them, and report the result.

The long-term goal is not simply a smarter chatbot.

It is an agent capable of operating within a real computing environment.

---

## Security

Giving an AI access to a computer introduces a fundamentally different class of problems compared with ordinary chatbots.

Filesystem access, shell commands, application control, and persistent memory can all affect the user's environment.

Astral therefore treats tool access as a capability that should be explicitly designed and controlled.

Important areas include:

* Workspace boundaries
* Command validation
* Permission handling
* Tool isolation
* Execution visibility
* Error handling
* Confirmation mechanisms
* Safe defaults

The objective is to make Astral powerful without making its behavior opaque.

---

## Limitations

Astral is still an experimental project.

Current limitations can include:

* Model-dependent reasoning quality
* Imperfect tool selection
* Occasional incorrect assumptions
* Local inference performance limitations
* Dependency on the configured LLM backend
* Incomplete application control
* Evolving memory architecture
* Limited error recovery
* Incomplete security hardening

Agent systems are difficult because a model can produce a technically valid tool call while still misunderstanding the user's actual intention.

Astral is therefore being developed incrementally rather than attempting to solve every problem at once.

---

## About the Project

Astral is an independent project developed by a high school student currently in their final year of high school.

The project is also part of an ongoing learning process in software engineering, artificial intelligence, Python development, system architecture, and computer automation.

Astral is not presented as a finished or production-ready AI system. It is an evolving project built through continuous experimentation, implementation, debugging, and refactoring.

Many parts of the project are still being learned and improved while the system itself is being developed.

This means that the architecture, implementation, and available features may change significantly over time.

The development process is an important part of the project.

Astral is intended to demonstrate not only the final system, but also the process of learning how to design, build, debug, and improve a complex software project.

As development continues, the project will gradually evolve from an experimental AI agent into a more capable personal computer assistant.

---

## Learning Through Development

Astral is being developed alongside the learning process behind it.

Rather than waiting until every concept is fully understood before starting implementation, new concepts are explored by applying them directly to the project.

This approach allows Astral to serve both as software and as a practical learning environment.

Not every implementation is expected to be the final solution.

Some components may be rewritten, replaced, or removed as better approaches are discovered.

Experiments, failed implementations, debugging sessions, and refactoring are considered part of the development process rather than something to hide.

The project follows an incremental approach:

```text
Learn
  ↓
Build
  ↓
Test
  ↓
Encounter Problems
  ↓
Debug
  ↓
Refactor
  ↓
Improve
  ↓
Learn More
```

The objective is not to immediately create a complete AI assistant.

The objective is to continuously improve the system while developing a deeper understanding of how each component works.

---

## Technology

The project currently revolves around:

```text
Python
Local LLM Inference
OpenAI-Compatible APIs
SearXNG
Filesystem Tools
Shell Tooling
Agent Orchestration
Persistent Memory
```

The architecture is intentionally designed so individual components can be replaced.

---

## Documentation

Focused guides live next to this README:

```text
docs/MODELS.md            Model lineup and provider switching
docs/DEVELOPMENT_LOG.md   Version-by-version development history
.github/CONTRIBUTING.md   How to report issues or propose changes
LICENSE                   Source-available, view-only terms
```

---

## Contributing

Astral is an experimental project.

Suggestions, bug reports, and pull requests are welcome.

Contributing does not change the license of the project: everything outside an accepted contribution stays under the terms in [`LICENSE`](LICENSE).

Contributions can focus on areas such as:

```text
New Tools
Agent Reliability
Memory Systems
LLM Integrations
Desktop Automation
Voice Interfaces
Security
Performance
Testing
Documentation
```

When adding a new capability, prefer integrating it as an independent component rather than coupling it directly into the agent loop.

Good agent architecture should make adding capabilities straightforward.

---

## Project Status

Astral is currently under active development.

The 1.x series is focused on establishing the foundation required for a reliable local computer agent.

The project is not intended to be presented as production-ready software.

Features are being implemented, tested, refactored, and replaced as the architecture develops.

Expect breaking changes during development.

Astral is currently a learning-driven project, and its development is expected to continue throughout the transition from high school into higher education.

---

## Philosophy

Astral started from a simple question:

> What happens if an AI assistant isn't limited to a chat box?

The project explores that question through a local-first agent architecture.

The goal is to combine:

```text
Language Models
+
Tools
+
Memory
+
Computer Access
+
Automation
```

into a single system that can actually operate in the user's environment.

Astral is not trying to be the biggest AI system.

It is trying to be useful.

---

## License

Astral is **not** open source.

This project is published as a portfolio / personal-use project under the **Astral Source-Available License (View-Only)**.

In short:

* You **may** read the source, study how it works, write about it, and run an unmodified copy for personal, non-commercial use.
* You **may not** modify and republish it, sell it, rebrand it, or use it as a base for a similar product.
* Bug reports and suggested improvements are welcome; third-party components stay under their own licenses.

See the [`LICENSE`](LICENSE) file for the complete terms and for how to ask about other kinds of use.

---

## Author

Astral is an independent project built as an exploration of local AI agents, computer automation, and personal assistant systems.

The project is developed as part of an ongoing journey of learning software engineering, artificial intelligence, and system development.

---

## Status

```text
Astral 1.x
Local-First
Agent-Based
Actively Developed
Learning-Driven
```

The project is still evolving.

The architecture today is not necessarily the architecture tomorrow.

That's intentional.
