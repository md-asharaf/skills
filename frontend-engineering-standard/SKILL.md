---
name: frontend-engineering-standard
description: |
  Universal, component-agnostic frontend engineering standards, UI/UX craftsmanship laws, and design system principles.
  Covers the Zero Raw HTML Primitives Law (custom components & variants everywhere), the Five Mandatory View Lifecycle States
  (Loading/Skeleton, Pending, Success, Empty, Error), Optimistic UI with automatic rollback, URL-as-state deep-linking,
  floating bulk action bar patterns, design token exclusivity, strict component prop contracts, UI/UX golden rules
  (Shneiderman / Nielsen / Apple HIG / WCAG 2.2 AA), plain-language human UI text (zero developer jargon), data-driven forms & tables,
  layout stability (zero CLS), visual screenshot verification, and responsive accessibility.
---

# Universal Frontend Engineering Standard & UI/UX Craftsmanship Specification

**Classification:** Global Frontend Architectural Standard & UI/UX Craftsmanship Constitution  
**Target Environments:** React, Next.js, Vue, Nuxt, Svelte, Vite, React Native, Tailwind CSS, Web Components  
**Core Invariant:** Accessible and resilient user interfaces that follow the project's design system, avoid layout shifts, and use clear language.

> **Domain Separation Notice:** This standard governs user interfaces: components, states, tokens, UX rules, UI copy, accessibility and UI tests.
> * Agent process, verification strategy, git, and the code rules shared by every language (comments, types, naming in code): **`agentic-engineering-standard`**.
> * Server code: **`backend-engineering-standard`**. Workspace topology and build pipelines: **`universal-enterprise-monorepo`**.

---

## 1. Prefer Design-System Primitives for Reusable UI

When a project has a design system, use its existing primitives for interactive controls and repeated visual patterns. Native semantic HTML remains appropriate for landmarks, text, lists, and structural layout, and where the project has no suitable primitive. Do not add wrapper components only to avoid using semantic HTML. Follow the project specification and its accessibility requirements.

| Ad hoc pattern | Prefer the shared primitive when one exists | Useful props and variants |
| :--- | :--- | :--- |
| `<button className="...">` | `<Button variant="primary">` | `variant`, `size`, `isLoading`, `icon` |
| `<input type="text" className="...">` | `<Input label="..." error="..." />` | `label`, `error`, `helperText` |
| `<select className="...">` | `<Select options={...} />` | `options`, `value`, `onChange` |
| `<textarea className="...">` | `<Textarea label="..." />` | `label`, `error`, `rows` |
| `<span className="bg-green-100...">` | `<Badge variant="success">` | `variant="neutral \| success \| warning \| error"` |
| `<div className="border rounded...">` | `<Card><CardContent>...</Card>` | `variant="flat \| raised \| outline"` |
| `<table className="...">` | `<DataTable columns={...} data={...} />` | `columns`, `data`, `sorting`, `pagination` |
| `<h1 className="text-2xl font-bold...">` | `<Heading level={1}>` | `level={1..6}` |
| `<p className="text-sm text-gray-500">` | `<Text variant="muted">` | `variant="lead \| body \| caption \| muted"` |
| `<div className="w-full h-8 bg-gray-200">` | `<Skeleton variant="rectangular" />` | `variant="text \| circular \| rectangular"` |

### 1.1 The Rationale & Invariants:
1. **Centralized Accessibility (WCAG 2.2 AA):**
   - Focus rings (`focus-visible:ring-2`), keyboard listeners (`Enter`, `Space`, `Esc`), `aria-disabled`, and `aria-busy` are defined once in the primitive. A raw `<button>` scattered in feature views inevitably forgets focus states.
2. **Zero "Tailwind Class Spaghetti" in Views:**
   - Feature views must contain semantic UI logic, not 25 copy-pasted Tailwind utility classes.
   - All visual variants (`primary`, `secondary`, `outline`, `ghost`, `destructive`, `sm`, `md`, `lg`) are defined in the component primitive using CVA (Class Variance Authority) or design tokens.
3. **Atomic Brand & Token Evolution:**
   - If button border-radius, active-state animations, or primary surface tokens change, updating the primitive instantly updates all 500 views across the application with zero visual drift.
4. **Built-in Ergonomic States:**
   - Primitives come pre-wired with `isLoading`, `icon`, `helperText`, and `error` contracts. Developers never manually splice spinner `<div>`s or error text inline.

### 1.2 Exhaustive Variant System (Every Custom Component Has Typed Variants)
Every custom component primitive in the design system MUST define an exhaustive set of typed variants. Feature views **MUST NOT** override visual appearance by appending ad-hoc colors, borders, or paddings via `className`:

* **Exhaustive Variant Dimension Unions:**
  - **Visual Hierarchy (`variant`):** `'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'subtle' | 'link'`
  - **Semantic Intent (`intent` / `tone`):** `'default' | 'neutral' | 'success' | 'warning' | 'error' | 'info' | 'brand'`
  - **Size Scaling (`size`):** `'xs' | 'sm' | 'md' | 'lg' | 'xl'`
  - **Density & Padding (`density`):** `'compact' | 'comfortable' | 'spacious'`
  - **Surface Elevation (`elevation`):** `'flat' | 'raised' | 'overlay' | 'sunken'`
* **The No-Inline-Style-Hacking Rule:** If a feature view needs a specific visual treatment (e.g. a destructive secondary button, or an alert banner for warning), developers MUST select from the component's defined variant props (`<Button variant="destructive" size="sm">`), NOT hack it inline with Tailwind utilities like `className="bg-red-50 text-red-700 border-red-300"`.
* **The Variant Extension Law:** If a genuinely new visual pattern is required, add the variant to the custom component's definition (with proper CVA tokens, light/dark mode contrast, and focus states) so every view in the application can use it.

### 1.3 Complete Custom Component Taxonomy Checklist
Every modern production frontend project MUST implement and consume these custom primitives instead of raw HTML:
* **Interactive & Actions:** `<Button>`, `<LinkButton>`, `<IconButton>`, `<SegmentedControl>`, `<ButtonGroup>`, `<DropdownMenu>`
* **Form Controls:** `<Input>`, `<Textarea>`, `<Select>`, `<Combobox>`, `<Checkbox>`, `<RadioGroup>`, `<SettingToggle>` / `<Switch>`, `<DatePicker>`, `<FileUpload>`
* **Surfaces & Containers:** `<Card>`, `<CardHeader>`, `<CardContent>`, `<CardFooter>`, `<Dialog>` / `<Modal>`, `<Drawer>` / `<Sheet>`, `<Popover>`, `<Tooltip>`, `<Separator>`
* **Data Display & Tables:** `<DataTable>`, `<Badge>`, `<Tag>`, `<Avatar>`, `<StatCard>`, `<KeyValueList>`, `<EmptyState>`
* **Typography:** `<Heading level={1..6}>`, `<Text variant="lead | body | caption | muted | mono">`, `<Kbd>`
* **Feedback & Loaders:** `<Skeleton>`, `<Spinner>`, `<Toast>`, `<Alert>`, `<ProgressBar>`

---

## 2. Strict Component Prop Contracts

Shared UI primitives are strict API contracts; never hack or bypass their internal ergonomics with ad-hoc child elements.

* **Dedicated Icon Props:** Always pass icons into primitives via the dedicated `icon` prop:
  - 🟢 **Correct:** `<Button icon={<TrashIcon />} variant="destructive">Delete</Button>`
  - 🔴 **Wrong:** `<Button><TrashIcon /> Delete</Button>`
* **Dedicated Loading State:** Always trigger loading indicators via the `isLoading` prop:
  - 🟢 **Correct:** `<Button isLoading={isSubmitting}>Save Changes</Button>`
  - 🔴 **Wrong:** `<Button>{isSubmitting ? <Spinner /> : null} Save Changes</Button>`
* **Dedicated Navigation Link Buttons:** Never nest a `<button>` inside an `<a>` tag or `<Link>` component:
  - 🟢 **Correct:** `<LinkButton href="/settings" variant="outline">Settings</LinkButton>`
  - 🔴 **Wrong:** `<Link href="/settings"><Button>Settings</Button></Link>`
* **Accessible Icon-Only Buttons:** Every button that renders only an icon MUST carry an explicit `aria-label`:
  - 🟢 **Correct:** `<Button icon={<SettingsIcon />} aria-label="Account Settings" variant="ghost" />`
  - 🔴 **Wrong:** `<Button icon={<SettingsIcon />} />`

---

## 3. The Five Mandatory View Lifecycle States

Every page, data view, table, drawer, modal, and interactive component MUST explicitly handle all five lifecycle states. A view that only renders the "happy path" is fundamentally defective.

| Lifecycle State | Trigger & Condition | Mandatory UI Behavior |
| :--- | :--- | :--- |
| **1. Loading & Skeleton** | Initial data fetching or route transition | Structured skeleton screen mirroring exact dimensions; zero layout shift (CLS). |
| **2. Success** | Data resolves successfully | Populated view using design system primitives with typed variants. |
| **3. Empty** | Collection or search returns 0 items | Semantic illustration/icon + human-readable explanation + primary CTA button. |
| **4. Pending / Mutation** | User triggers an action or mutation | Immediate (<100ms) visual indicator (`isLoading={true}`), double-click prevention. |
| **5. Error & Recovery** | Network error or rejected request | Human-readable explanation (zero raw tech dumps) + actionable `[Retry]` trigger. |

### 3.1 Loading & Structured Skeleton State
* **Zero Layout Shift (Zero CLS):** Skeletons must mirror the exact dimensions, grid layout, card spacing, and typography heights of the content they precede.
* **No Blank White Screens:** Never display an empty white screen or a lonely centered spinner for page-level data fetching.
* **Text-Free Skeletons:** Skeletons must contain neutral placeholder geometry only (pulses/shimmers); never render fake placeholder text or dummy labels that confuse screen readers.

### 3.2 Pending & Optimistic Mutation State (With Automatic Rollback)
* **Immediate Visual Feedback (<100ms):** Every button click, form submit, or switch toggle must immediately indicate an in-flight operation.
* **Double-Submission Prevention:** Action buttons must be automatically disabled while their mutation promise is pending to prevent duplicate API requests.
* **Optimistic UI with Automatic Rollback:**
  - For high-frequency, low-latency user interactions (toggling switches, reordering list rows, archiving items, starring/favoriting):
    1. Update the local UI state immediately (<10ms) without waiting for the server response.
    2. Dispatch the network mutation in the background.
    3. If the server request succeeds, silently reconcile server-generated fields (updated timestamps, new versions).
    4. If the server request fails, **automatically rollback** the UI to the pre-mutation snapshot, and display an actionable Toast notification with a retry trigger (*"Unable to save changes. [Retry]"*). Never leave the UI in an un-synced optimistic state after a network rejection.

### 3.3 Success State & Feedback
* **Clear State Closure:** State-changing operations (saving settings, creating records, deleting assets) must provide unequivocal feedback:
  - Non-intrusive Toast notifications for background saves.
  - Confirmation banners or updated status badges for significant transitions.
  - Automated cache invalidation to instantly refresh all stale counters and badges across the UI.

### 3.4 Contextual Empty State
* **No Collapsed Cards:** Never render an empty table, a collapsed blank card, or an empty screen with zero guidance.
* **The 3 Mandatory Elements of an Empty State:**
  1. A friendly, semantic icon or illustration representing the missing resource.
  2. A clear, plain-language heading and explanation (e.g. *"No invoices created yet. Generate your first invoice to bill a customer."*).
  3. A prominent primary Call-to-Action (CTA) button (e.g. `[Create Invoice]`) or filter-reset button.

### 3.5 Resilient Error State & Boundaries
* **No Raw Tech Dumps:** Never present raw JSON error responses, SQL error codes, or unhandled promise rejections to users.
* **Actionable Error Recovery:** Every error state must state what happened in plain human terms and provide a concrete recovery action (`[Retry]`, inline field errors).
* **Granular Error Boundaries:** Isolate component errors using React Error Boundaries so that a single failing chart or widget does not crash the entire application navigation shell.

---

## 4. Design System Consistency & Token Exclusivity

### 4.1 Design Token Exclusivity (Zero Arbitrary Magic Values)
* **The Rule:** Always use established semantic design tokens from the design system / stylesheet (`globals.css` or theme config).
* **Forbidden:**
  - Arbitrary hex colors (`bg-[#1a2b3c]`, `#f4f4f4`).
  - Hardcoded RGB/HSL values.
  - Arbitrary pixel dimensions (`p-[13px]`, `w-[327px]`).
  - One-off opacity hacks (`bg-white/40` where a semantic surface token exists).
* **The Token Extension Law:** If a genuinely novel visual role is required that the design system lacks, define the semantic CSS variable first in the root stylesheet (with both Light and Dark mode values) and then consume that token.

---

## 5. UI/UX Craftsmanship & Golden Rules

These principles synthesize Nielsen's 10 Heuristics, Shneiderman's 8 Golden Rules, Apple Human Interface Guidelines, and WCAG 2.2 AA.

### 5.1 Settings Live with the Thing They Change
* Settings for a specific object (a product, a module, an API integration) must be edited **directly on that object's view or settings tab**.
* A centralized dashboard overview displays status and links to the object; it must never be the sole place to edit a single object's properties, and two separate pages must never edit the same setting.

### 5.2 Group by Dependency
* Features that cannot function without a parent feature must live inside that parent feature (as a nested tab or sub-panel), not as an equal top-level navigation sibling.

### 5.3 Recognition Over Recall
* **Display Human Labels, Never Internal Slugs:** Never render raw database column names, UUIDs, integer IDs, internal slug names, or configuration syntax in UI text.
* **Select, Don't Type:** Offer searchable pickers, dropdowns, and radio cards instead of forcing users to remember and type raw foreign key values.

### 5.4 One Primary Action per View
* Every view, card, or modal must have exactly **one visually prominent Primary Action** (solid accent background).
* Secondary actions must be styled as Outline, Ghost, or Secondary variants.
* Destructive actions (Delete, Archive, Revoke) must be visually separated, styled in red/destructive variants, named by their exact effect (*"Delete Project"*, not *"OK"*), and protected by a confirmation dialog.

### 5.5 Say Each Fact Once (Progressive Disclosure)
* Avoid redundant copy that repeats adjacent headings, labels, or badges.
* Keep copy clean, tight, and focused on the task. Move supplementary documentation or edge-case explanations behind inline helper tooltips or help links.

### 5.6 User Control & Error Prevention
* **Universal Cancellation:** Every modal, drawer, or dropdown must close immediately when clicking the background overlay or pressing the `Escape` key.
* **Unsaved Changes Guard:** Warn users before navigating away from a dirty form with unsaved changes.
* **Inline Validation:** Validate fields inline as the user types or blurs out of the field, highlighting the exact issue before form submission.
* **Review Before Destructive Changes:** Require explicit confirmation or two-step review before applying irreversible actions.

### 5.7 One Name per Concept
* A feature, action, or object MUST have exactly **one consistent name** across navigation, page titles, cards, buttons, breadcrumbs, toasts, error messages, and documentation.
* Titles and labels shown in multiple places must derive from a single shared constants source, never copy-pasted strings.

### 5.8 Fewest Steps (The Click Count Law)
* Never introduce an unnecessary page, extra picker, or intermediary click between a user and their primary task.
* Count the clicks required for common user workflows before and after a UI change; increasing click count requires explicit justification.

### 5.9 Consistent Patterns Across Views
* The same task must look and work identically everywhere:
  - Same card geometry, header hierarchy, and footer actions (e.g. `[Reset]` on left, `[Review Changes]` / `[Save]` on right).
  - Identical empty, loading, and error boundaries.
  - Consistent ordering of standard fields (Name, Web Address, Description, Status).

### 5.10 Help in Context (Zero Tooltip Dependency)
* Short helper text placed directly under an input control explains its effect in plain user language.
* **No Tooltips for Essential Information:** Essential instructions, required format notes, and warnings must be visible inline. Tooltips are completely inaccessible on mobile touchscreens and hidden from casual scanning.

### 5.11 Responsive Integrity & Zero Horizontal Scroll
* Views must render cleanly without clipping, overlapping, or horizontal scrolling at any viewport width down to **320px**.
* Use equal-height card grids (`grid items-stretch`), clean flex wrapping, and responsive typography scales.

### 5.12 URL-As-State for Data Views (Deep-Linking & Shareability)
All data-filtering views (data tables, filter sheets, search cockpits) MUST mirror their active view parameters into the browser URL search query:
* **Mirror State in Search Params:** `?page=2&pageSize=25&q=john&status=active&sort=createdAt:desc`.
* **The 3 Invariants of URL State:**
  1. **Shareability:** Copying the URL and opening it in another tab or sharing it with a colleague must render the exact same filtered and sorted view.
  2. **Browser History Resilience:** Pressing the browser's Back/Forward buttons must step through search and pagination filters without reloading the application shell.
  3. **Clean Param Hygiene:** Default values (e.g. `page=1`, empty search `q=""`) MUST be omitted from the URL to keep addresses clean and readable.

### 5.13 Floating Bulk Action Bar Pattern
When managing collections with multi-select checkboxes (data tables, file asset grids):
* **Zero Button Clutter:** Never permanently clutter the top navigation header with disabled bulk action buttons.
* **The Floating Selection Dock:** As soon as $\ge 1$ item is selected, surface an anchored, floating bottom action bar (docked above the viewport footer):
  - Prominently display the exact count: *"12 items selected"*.
  - Surface distinct, typed batch actions: `[Publish]`, `[Export]`, and a destructive `[Move to Trash]`.
  - Provide an instant `[Deselect All]` trigger (or `Escape` key shortcut) to dismiss selection cleanly.

---

## 6. Plain Human Language & Zero Developer Jargon

### 6.1 Plain English Rule
* All user-facing copy (navigation titles, card descriptions, empty states, error messages, form field helpers) must use **plain everyday language that a non-technical person understands**.

### 6.2 Developer Jargon Ban
* **Strictly Banned in User-Facing Text:**
  - "UUID", "ID", "Slug", "Database", "Entity"
  - "Null", "Undefined", "Payload", "Mutation"
  - "Tenant ID", "Control Plane", "API endpoint"
  - "Failed to fetch", "500 Internal Server Error"
* **Plain Language Translations:**
  - 🔴 *"Failed to mutate entity: duplicate slug error"*
  - 🟢 *"A project with this web address already exists. Please choose a different address."*

---

## 7. Accessibility Standards (WCAG 2.2 AA)

1. **Color Contrast Ratio:**
   - Body text against background must maintain at least **4.5:1** contrast.
   - Large text (18pt+) and UI controls must maintain at least **3:1** contrast.
2. **Color Cannot Be the Sole Carrier of Meaning:**
   - Error states must include an icon or text label in addition to red text.
   - Active status badges must pair color with descriptive text.
3. **Full Keyboard Operability:**
   - Every interactive control must be reachable via `Tab` and activatable via `Enter` or `Space`.
   - All interactive controls must display a visible, high-contrast focus outline when navigated via keyboard.
4. **Touch Target Dimensions:**
   - Minimum touch target size is $24 \times 24\text{px}$ (preferably $44 \times 44\text{px}$ on touch screens) with adequate spacing between adjacent buttons.
5. **Semantic HTML Landmarks:**
   - Use `<main>`, `<header>`, `<nav>`, `<aside>`, `<section>`, and `<article>` tags properly.
6. **Server Components by Default:**
   - Default to Server Components; use `"use client"` strictly for components requiring React hooks, state, effects, or browser DOM APIs.

---

## 8. Visual Verification & Screenshot Proof Gate

Static compilation and passing linter checks do NOT prove a UI looks right.
* **The "Verify by Looking" Law:** Every changed view or component MUST be verified visually across 4 critical dimensions:
  1. **Viewport Widths:** Desktop ($1280\text{px}+$) and Mobile Phone ($320\text{px}$ to $375\text{px}$).
  2. **Theme Modes:** Light mode and Dark mode.
  3. **Data States:** Loading skeleton state vs. populated success state.
  4. **Boundary States:** Contextual empty state vs. error boundary recovery state.

---

## 9. Frontend Test-Based Engineering (Component & Screen TDD)

Frontend user interfaces must be backed by automated component and integration tests that verify interaction contracts and state resilience.

| 🔴 Forbidden Practice | 🟢 Mandatory Frontend Testing Standard |
| :--- | :--- |
| "It compiled, so the UI works" | Automated component tests verifying all 5 lifecycle states |
| Querying brittle CSS utility classes (`.btn-primary`) | Querying accessible roles and names (`getByRole('button', { name: '...' })`) |
| Unhandled API rejection white-screens | Error boundary tests proving fallback UI and retry recovery work |
| Silent double-submissions | Interaction tests proving action triggers disable while mutation is pending |

### 9.1 The Five-State Component Test Contract
For every complex view, table, or form, automated tests (e.g. React Testing Library, Vitest) MUST verify:
1. **Loading State:** Skeletons or loading indicators appear during data fetching; actions are disabled.
2. **Success State:** Populated data displays correctly with expected variant badges, table rows, and headers.
3. **Empty State:** When API returns an empty collection, the view renders a clear explanatory heading, semantic illustration/icon, and a primary CTA.
4. **Pending / Mutation State:** Submitting a form immediately toggles `isLoading={true}` and disables action buttons to prevent double submissions.
5. **Error State & Recovery:** Simulating network failure (500/404) triggers inline error messages or error boundaries, with an operable `[Retry]` action that re-triggers the query.

### 9.2 Prop Contract & Accessibility Testing
* **Accessible Role Verification:** Query elements by `getByRole('button', { name: '...' })` or `getByLabelText('...')`, never by CSS class selectors (`.btn-primary`).
* **Icon-Only Accessible Name:** Automated tests prove icon-only buttons carry an explicit `aria-label`.
* **Keyboard Navigation:** Prove modals and drawers close on `Escape` keydown, and forms submit on `Enter`.
