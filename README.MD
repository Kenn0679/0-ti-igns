# 0Ᵽti⟆igns Support Article Pipeline

An automated pipeline designed to retrieve, process, and ingest support documentation from `support.optisigns.com`. Currently, only **Phase 1** is implemented.

---

## 1. Scrape ⇒ Markdown (Current Phase)

This phase connects to the Zendesk Help Center API, retrieves all support articles, and converts their HTML body into clean, standardized Markdown format.

* **Key Functions:**
  * Pulls $\ge 30$ articles from the API.
  * Converts HTML structure to clean Markdown with consistent heading hierarchy.
  * Sanitizes content by stripping navigation panels, headers, footers, and tracking elements.
  * Resolves and preserves relative internal links by mapping them to local `<slug>.md` files.

### Setup

Ensure you have [Node.js](https://nodejs.org/) and [pnpm](https://pnpm.io/) installed.

1. Navigate to the scraper directory:
   ```bash
   cd Scrape
   ```
2. Install package dependencies:
   ```bash
   pnpm install
   ```
3. Create a `.env` file in the `Scrape/` directory with the following variables:
   ```env
   BASE_URL=support.optisigns.com
   ZENDESK_API=/api/v2/help_center/articles
   ```

### How to Run Locally

Execute the scraping script directly using the TypeScript runtime runner:

```bash
# Run from the Scrape directory
npx tsx src/migrate.ts
```

Output Markdown files will be generated and saved in `Scrape/src/dist_markdown/`.

### Link to Daily Job Logs

Automated cron-job outputs and scraping logs are tracked daily:
- [View Daily Job Logs]([link-to-logs])

### Sample Output / Verification

Below is a verification screenshot showing the processed articles or output format:

![Verification Screenshot]([screenshot-placeholder-url])

---

## 2. [Next Phase Title / Placeholder]

* **Status:** Planned
* **Details:** This phase is currently planned to handle indexing, tokenization, or vector embedding generation for the processed markdown documents.

---

## 3. [Final Phase Title / Placeholder]

* **Status:** Planned
* **Details:** The final phase will integrate the structured documentation data into downstream consumption layers, search interfaces, or LLM-based assistants.
