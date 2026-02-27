---
description: "JavaScript and TypeScript development standards: strict typing, async/await, ESLint, Prettier. For JS/TS files."
applyTo: "**/*.{js,ts,jsx,tsx,mjs,cjs}"
---

# JavaScript / TypeScript Development

- TypeScript > JavaScript for type safety
- Use `const` by default, `let` when reassignment is needed, never `var`
- Use strict equality (`===` / `!==`)
- Prefer `async/await` over raw Promises or callbacks
- Use ESLint and Prettier for consistent formatting
- Avoid `any` type in TypeScript — define proper interfaces/types
- Use named exports over default exports for better refactoring support
- Handle errors in async functions with try/catch
- Avoid mutating function arguments
