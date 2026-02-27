# Copilot Instructions — Software Design & Architecture

> These instructions govern every code suggestion produced in this workspace.
> They are **language-agnostic** and **framework-agnostic**.
> They encode the **Gang of Four design patterns**, **SOLID**, **architectural patterns**,
> and **modern software engineering principles**.

---

## 0. Foundational Principles

These rules take precedence over any other consideration and apply to every generated line.

### SOLID
| Letter | Principle | Rule |
|--------|-----------|------|
| **S** | Single Responsibility | One class = one reason to change. Split any class that serves more than one actor. |
| **O** | Open / Closed | Extend behavior by adding new code, never by modifying existing code. Use abstractions and hooks. |
| **L** | Liskov Substitution | A subtype must honor the full contract of its parent. Never weaken preconditions or strengthen postconditions in a subclass. |
| **I** | Interface Segregation | Prefer many small, focused interfaces over one large general-purpose one. Clients must not depend on methods they do not use. |
| **D** | Dependency Inversion | High-level modules must not depend on low-level modules. Both must depend on abstractions. Inject dependencies; never instantiate concrete dependencies inside business logic. |

### Other Core Heuristics
- **DRY** — Every piece of knowledge must have a single, authoritative representation.
- **YAGNI** — Only implement what is needed right now. No speculative abstractions.
- **KISS** — The simplest solution that works is always preferred.
- **Fail Fast** — Validate inputs at boundaries immediately. Never let invalid state propagate.
- **Composition over Inheritance** — Prefer object composition for behavior reuse. Reserve inheritance for genuine IS-A relationships.
- **Principle of Least Surprise** — A component must do exactly what its name and contract imply, nothing more.
- **Law of Demeter** — A unit should only talk to its immediate collaborators. Never chain more than one level of delegation (`a.getB().getC().doSomething()` is forbidden).

---

## 1. GoF — Creational Patterns

> **Purpose:** Control how objects are created; decouple creation from usage.

### 1.1 Singleton
**Intent:** Ensure a class has exactly one instance and provide a global access point.

- Apply only when a single shared instance is a true architectural constraint (registry, config hub).
- Never use Singleton as a substitute for proper dependency injection.
- The instance must be thread-safe.
- Prefer a container-managed or module-level instance over a hand-rolled lock.

```
Singleton
  - static instance: Singleton
  + static getInstance(): Singleton
  - constructor()                    // private
```

### 1.2 Factory Method
**Intent:** Define an interface for creating an object, but let subclasses decide which class to instantiate.

- The base class declares an abstract `factoryMethod()`.
- Concrete subclasses override it to return a specific product.
- The caller never references a concrete product class.
- Use when the exact type of object to create is not known at compile-time.

```
AbstractCreator
  + templateMethod()           // calls factoryMethod()
  # abstract factoryMethod(): Product

ConcreteCreator
  # factoryMethod(): ConcreteProduct
```

### 1.3 Abstract Factory
**Intent:** Provide an interface for creating families of related objects without specifying concrete classes.

- Define one abstract factory interface with one creation method per product type.
- Concrete factories implement the interface for a specific product family.
- Clients are coded against the abstract factory and abstract product interfaces only.
- Swap the entire product family by replacing the factory implementation.

### 1.4 Builder
**Intent:** Separate the construction of a complex object from its representation.

- Define a `Builder` interface with one method per construction step.
- A `Director` orchestrates the steps; the builder accumulates the partial product.
- The terminal `build()` / `getResult()` method returns the final product.
- Fluent builder (`return this`) is acceptable; the Director is optional.
- Apply when an object requires many optional parameters or ordered assembly steps.

```
Director
  + construct(builder: Builder): void

Builder (interface)
  + stepA(): Builder
  + stepB(): Builder
  + build(): Product
```

### 1.5 Prototype
**Intent:** Create new objects by copying an existing instance.

- Declare a `clone()` method on a `Prototype` interface.
- Decide explicitly whether a shallow or deep copy is required and document the choice.
- Apply when construction is expensive and the new object differs only slightly from the source.

---

## 2. GoF — Structural Patterns

> **Purpose:** Compose classes and objects into larger structures while keeping them flexible and efficient.

### 2.1 Adapter
**Intent:** Convert the interface of a class into the interface the client expects.

- The adapter wraps the adaptee; the client never knows the adaptee exists.
- Third-party or legacy types must not leak beyond the adapter boundary.
- Prefer **object adapter** (composition) over class adapter (multiple inheritance).

```
Client → Target (interface)
              ↑
          Adapter  ──wraps──> Adaptee
```

### 2.2 Bridge
**Intent:** Decouple an abstraction from its implementation so both can vary independently.

- The abstraction holds a reference to an `Implementor` interface.
- Concrete implementors are injected at construction time, not hardcoded.
- Apply when both the abstraction hierarchy and the implementation hierarchy must be extensible independently.

```
Abstraction ──[implementor]──> Implementor (interface)
     │                               ↑
RefinedAbstraction          ConcreteImplementorA / B
```

### 2.3 Composite
**Intent:** Compose objects into tree structures to represent part-whole hierarchies.

- Define a `Component` interface with operations common to both leaves and composites.
- `Leaf` implements the operation directly.
- `Composite` delegates to its children and may aggregate results.
- Clients treat leaves and composites uniformly through the `Component` interface.

### 2.4 Decorator
**Intent:** Attach additional responsibilities to an object dynamically, without subclassing.

- The decorator implements the same interface as the wrapped component.
- It holds a reference to the component and delegates to it, adding behavior before or after.
- Decorators are stackable; their order is significant and must be intentional.
- Never mutate the internal state of the wrapped object.

```
Component (interface)
    ↑ implements
BaseComponent        Decorator (holds ref to Component)
                          ↑
                 ConcreteDecoratorA
                 ConcreteDecoratorB
```

### 2.5 Facade
**Intent:** Provide a unified, simplified interface to a complex subsystem.

- The facade orchestrates existing subsystem classes; it adds no new behavior of its own.
- Each public method on the facade represents one coherent high-level use case.
- Clients interact with the facade only; direct subsystem access should be discouraged.
- The facade depends on the subsystem — the subsystem must not depend on the facade.

### 2.6 Flyweight
**Intent:** Use sharing to support a large number of fine-grained objects efficiently.

- Separate **intrinsic state** (shared, immutable, stored in the flyweight) from **extrinsic state** (context-specific, passed by the caller on each call).
- A `FlyweightFactory` caches and reuses instances.
- Apply only when memory profiling confirms the cost of many similar objects is a real problem.

### 2.7 Proxy
**Intent:** Provide a surrogate that controls access to another object.

| Proxy Type | Use Case |
|---|---|
| Virtual Proxy | Lazy initialization of expensive objects |
| Protection Proxy | Authorization / access control |
| Remote Proxy | Network transparency |
| Caching / Logging Proxy | Cross-cutting concerns |

- The proxy implements the same interface as the real subject.
- It forwards calls to the real subject, adding its concern around them.
- Clients must be unaware they are talking to a proxy.

---

## 3. GoF — Behavioral Patterns

> **Purpose:** Define how objects communicate and how responsibility is distributed.

### 3.1 Chain of Responsibility
**Intent:** Pass a request along a chain of handlers until one processes it.

- Each handler holds an optional reference to the next handler.
- A handler either handles the request and stops, or forwards it unchanged.
- The sender is fully decoupled from all potential receivers.
- Apply for validation pipelines, middleware stacks, approval workflows.

```
Handler (abstract)
  - next: Handler
  + setNext(h: Handler): Handler
  + handle(request): Result       // abstract
```

### 3.2 Command
**Intent:** Encapsulate a request as an object, enabling parameterisation, queuing, logging, and undo.

- Define a `Command` interface with `execute()`.
- Add `undo()` when reversibility is required.
- An `Invoker` stores and triggers commands without knowing their implementation.
- A `Receiver` contains the actual business logic.

```
Invoker ──> Command (interface: execute, undo)
                    ↑
             ConcreteCommand ──> Receiver
```

### 3.3 Interpreter
**Intent:** Define a grammar for a language and provide an interpreter for it.

- Each grammar rule maps to a class.
- Apply only for small, well-bounded grammars (expression evaluators, rule engines).
- For complex grammars, use a dedicated parser generator instead.

### 3.4 Iterator
**Intent:** Provide a way to access elements of a collection sequentially without exposing its internal structure.

- Define an `Iterator` interface with `hasNext()` and `next()`.
- The collection returns a concrete iterator via `createIterator()`.
- Clients iterate via the interface; the collection's structure is hidden.
- Never reimplement iteration when the language or framework already provides it natively.

### 3.5 Mediator
**Intent:** Define an object that encapsulates how a set of objects interact.

- Components hold a reference to the mediator only — never to each other.
- Components notify the mediator of events; the mediator coordinates the response.
- Apply to reduce a tangled many-to-many dependency graph to a hub-and-spoke model.

```
ComponentA ──notify()──> Mediator <──notify()── ComponentB
             <──handle()──┘  └──handle()──>
```

### 3.6 Memento
**Intent:** Capture and externalise an object's internal state so it can be restored later, without violating encapsulation.

- The **Originator** creates mementos from its state and restores state from them.
- The **Memento** is opaque to all other objects.
- The **Caretaker** stores mementos without ever inspecting their contents.
- Apply for undo/redo, snapshots, and checkpoints.

### 3.7 Observer (Publish / Subscribe)
**Intent:** Define a one-to-many dependency so that when one object changes state, all its dependents are notified automatically.

- `Subject` maintains a list of observers and calls `update()` on each when state changes.
- Observers register and deregister at runtime.
- Choose consistently between **push** (subject sends data) and **pull** (observer queries subject).
- Guard against re-entrant notifications and notification storms.

```
Subject
  + attach(o: Observer): void
  + detach(o: Observer): void
  + notify(): void

Observer (interface)
  + update(event): void
```

### 3.8 State
**Intent:** Allow an object to alter its behavior when its internal state changes.

- Encapsulate each state as a class implementing a `State` interface.
- The context delegates all state-dependent behavior to the current state object.
- Manage transitions either in the context or in the state objects — choose one approach consistently throughout the codebase.
- Never model state logic as a chain of `if/else` or `switch` blocks.

```
Context ──[currentState]──> State (interface: handle())
                                ↑
                     StateA   StateB   StateC
```

### 3.9 Strategy
**Intent:** Define a family of algorithms, encapsulate each one, and make them interchangeable.

- Extract each algorithm variant into a class implementing a `Strategy` interface.
- The context receives the strategy via constructor injection or a setter.
- Clients select the strategy; the context executes it.
- **Replace every `if/else` or `switch` that selects behavior at runtime with Strategy.**

```
Context ──[strategy]──> Strategy (interface: execute())
                            ↑
                  StrategyA   StrategyB   StrategyC
```

### 3.10 Template Method
**Intent:** Define the skeleton of an algorithm in a base class, deferring some steps to subclasses.

- The base class implements the invariant steps and calls abstract hook methods.
- Subclasses override only the variable steps, never the skeleton itself.
- Mark the template method as `final` (or equivalent) to prevent structural overrides.

```
AbstractClass
  + final templateMethod()         // orchestrates primitive operations
  # abstract primitiveOp1(): void
  # abstract primitiveOp2(): void
  # hook(): void                   // optional override — default no-op
```

### 3.11 Visitor
**Intent:** Define a new operation on elements of an object structure without changing the classes of those elements.

- Each element implements `accept(visitor: Visitor)`.
- The visitor declares one `visit(ConcreteElement)` overload per element type.
- Double dispatch routes the call to the correct overload.
- Apply when the object structure is stable but operations on it change frequently.

---

## 4. Architectural Patterns

### 4.1 Layered Architecture (N-Tier)
- Standard layers (top → bottom): **Presentation → Application → Domain → Infrastructure**.
- Dependencies flow **downward only** — a lower layer never imports from a higher one.
- Each layer exposes a well-defined interface to the layer immediately above it.
- Business rules live exclusively in the **Domain** layer.

### 4.2 Hexagonal Architecture (Ports & Adapters)
- The **domain core** has zero dependency on frameworks, databases, HTTP, or UI.
- **Primary ports**: interfaces the application exposes to the outside (inbound use-case contracts).
- **Secondary ports**: interfaces the application requires from the outside (repository, messaging, email).
- **Adapters** implement ports; they are the only layer allowed to reference external systems.
- All source-code dependencies point **inward** toward the domain core.

```
[REST Adapter] ──> [Primary Port] ──> [Domain Core] ──> [Secondary Port] ──> [DB Adapter]
[CLI Adapter]  ↗                                                           ↗  [MQ Adapter]
```

### 4.3 Clean Architecture
- Concentric rings: **Entities → Use Cases → Interface Adapters → Frameworks & Drivers**.
- **Dependency Rule**: source-code dependencies must point **inward only** across every ring.
- *Entities* contain enterprise-wide business rules; they know nothing of use cases.
- *Use Cases* orchestrate entities for application-specific business rules.
- *Interface Adapters* convert data between the inner format and the outside format.
- *Frameworks & Drivers* are plug-ins; the inner rings must not know they exist.

### 4.4 Domain-Driven Design (DDD)
| Building Block | Rule |
|---|---|
| **Entity** | Identity-based. Tracked through its lifecycle by a unique ID. |
| **Value Object** | Identity-free. Defined entirely by its attributes. Must be immutable. |
| **Aggregate** | Cluster of objects with one root Entity. Consistency boundary. External access via root only. |
| **Domain Service** | Stateless operation that does not naturally belong to any entity or value object. |
| **Repository** | Abstracts data access per aggregate. Hides all persistence details from the domain. |
| **Domain Event** | Immutable record of something significant that happened in the domain. |
| **Bounded Context** | Explicit boundary within which a model is defined and consistent. |
| **Anti-Corruption Layer** | Translation layer between two bounded contexts with differing models. |

### 4.5 CQRS (Command Query Responsibility Segregation)
- **Commands**: mutate state; return nothing (or a minimal acknowledgment); may produce domain events.
- **Queries**: read-only; no side effects whatsoever; may use a dedicated, denormalised read model.
- Command handlers and query handlers must reside in separate classes.
- The write model and read model may use entirely different data structures.

### 4.6 Event Sourcing
- State is derived by replaying an ordered, immutable log of domain events.
- Events are the single source of truth; current state is always a projection.
- Events are **append-only** — never mutate or delete them.
- Combine with CQRS: commands produce events; queries read from projections.

### 4.7 Microservices
- Each service owns its data store; no direct database sharing across service boundaries.
- Services communicate via stable, versioned contracts (REST, gRPC, message queues).
- Design for failure: apply circuit breakers, retries with exponential back-off, and idempotent operations.
- Each service is independently deployable; avoid creating a distributed monolith.

### 4.8 Repository Pattern
- Centralise all query and persistence logic for an aggregate behind a `Repository` interface.
- The domain and application layers depend on the repository interface only.
- Never scatter data-access calls across services, controllers, or domain objects.

### 4.9 Service Layer / Application Services
- Orchestrate use cases: load aggregates via repositories, invoke domain logic, persist results.
- Contain no business rules and no persistence logic of their own.
- One public method = one use case.
- Are typically the transaction boundary.

### 4.10 Specification Pattern
- Encapsulate a single business rule as a `Specification` object with `isSatisfiedBy(candidate)`.
- Combine specifications with `and`, `or`, `not` operators.
- Use for filtering, validation, and selection rules that must be composable and independently testable.

```
Specification (interface)
  + isSatisfiedBy(candidate): boolean
  + and(other: Specification): Specification
  + or(other: Specification): Specification
  + not(): Specification
```

### 4.11 Unit of Work
- Track all changes made to aggregates within a business transaction.
- Commit all tracked changes atomically, or roll back the entire unit on failure.
- The application service demarcates the unit-of-work boundary.

---

## 5. General Design Rules

### Object Design
- **Encapsulate what varies** — identify what is likely to change and isolate it behind an abstraction.
- **Program to interfaces, not implementations** — all dependency declarations must reference abstractions.
- **Prefer immutability** — make objects immutable by default; mutation requires explicit justification.
- **Avoid primitive obsession** — wrap meaningful domain concepts in dedicated Value Objects.
- **Explicit over implicit** — name things for what they are; never rely on hidden side effects.

### Coupling & Cohesion
- Aim for **high cohesion** (elements within a module are strongly related) and **low coupling** (modules know as little as possible about each other).
- **Stable Dependencies Principle**: depend in the direction of stability; volatile packages must not be depended on by stable ones.
- **Acyclic Dependencies Principle**: the dependency graph between components must contain no cycles.

### Error Handling
- Use specific, domain-meaningful error types — not generic base exceptions.
- Validate all input at system boundaries before it enters the domain.
- Never use exceptions for normal flow control.
- Document every error condition a public method can raise.

### Naming
- Names must reveal intent without requiring a comment.
- Boolean-returning methods should read as questions: `isValid()`, `hasPermission()`, `canProceed()`.
- Mutating methods should use imperative verbs: `createOrder()`, `sendNotification()`, `cancelBooking()`.
- Query methods should use declarative form: `getOrderById()`, `findActiveUsers()`, `countPendingTasks()`.

---

## 6. Anti-Patterns — Never Generate

| Anti-Pattern | Symptom | Correct Alternative |
|---|---|---|
| **God Class** | One class does everything | Split by SRP; apply bounded context |
| **Anemic Domain Model** | Domain objects are mere data bags | Move business logic into domain methods |
| **Spaghetti Code** | Arbitrary control flow, no clear structure | Layered design, pattern-based decomposition |
| **Golden Hammer** | One pattern applied to every problem | Select the pattern that fits the actual problem |
| **Premature Optimization** | Complex optimisation without measurement | YAGNI first; measure before optimising |
| **Leaky Abstraction** | Internal details bleed through the public interface | Enforce encapsulation at every boundary |
| **Magic Numbers / Strings** | Unexplained literals scattered in code | Named constants or enumerations |
| **Deep Inheritance Chains** | More than 3 levels of inheritance | Composition + interface segregation |
| **Type-Switching / instanceof chains** | `if x is TypeA … else if x is TypeB …` | Polymorphism or Visitor pattern |
| **Circular Dependencies** | Module A depends on B, B depends on A | Dependency inversion; introduce mediating abstraction |
| **Singleton Abuse** | Singletons used as global mutable state | Dependency injection |
| **Feature Envy** | A method uses more data from another class than its own | Move the method to the class whose data it uses |
| **Shotgun Surgery** | One logical change requires edits in many classes | DRY + cohesion improvement |
| **Data Clumps** | Same group of fields repeated across classes | Introduce a Value Object |
| **Long Parameter List** | More than 3–4 parameters on a method | Introduce a Parameter Object or use Builder |
| **Divergent Change** | One class changes for multiple unrelated reasons | Split by SRP |

---

## 7. Pattern Selection Guide

### I need to control **object creation**
- Exactly one instance → **Singleton**
- Subclass decides the type to create → **Factory Method**
- Family of related objects → **Abstract Factory**
- Complex step-by-step construction → **Builder**
- Copy an existing object → **Prototype**

### I need to compose **object structures**
- Incompatible interface → **Adapter**
- Abstraction + implementation vary independently → **Bridge**
- Tree / part-whole hierarchy → **Composite**
- Add responsibilities dynamically → **Decorator**
- Simplify a subsystem → **Facade**
- Many fine-grained shared objects → **Flyweight**
- Control or intercept access → **Proxy**

### I need to manage **behavior and communication**
- Pipeline of handlers → **Chain of Responsibility**
- Encapsulate a request / support undo → **Command**
- Sequential traversal without exposing internals → **Iterator**
- Decouple many communicating objects → **Mediator**
- Snapshot and restore state → **Memento**
- One-to-many change notification → **Observer**
- Behavior changes with internal state → **State**
- Interchangeable algorithms → **Strategy**
- Invariant algorithm skeleton with variable steps → **Template Method**
- New operation on a stable object hierarchy → **Visitor**

---

## 8. Pattern Interaction Rules

- **Strategy + Factory Method**: use the factory to decide which strategy to inject.
- **Command + Memento**: combine when undo/redo capability is required.
- **Observer + Mediator**: use Observer for simple pub-sub; switch to Mediator when observers also interact with each other.
- **Composite + Visitor**: classic pairing — Composite provides the structure; Visitor provides operations over it.
- **Decorator + Strategy**: Decorator adds cross-cutting concerns (logging, caching); Strategy swaps core logic.
- **Template Method vs. Strategy**: Template Method uses inheritance for variation; Strategy uses composition. Prefer Strategy when variation is needed at runtime.
- **Facade + any internal patterns**: the facade is free to use any structural or behavioral patterns in its implementation.

---

*Scope: all languages · all frameworks · last revised 2026*
