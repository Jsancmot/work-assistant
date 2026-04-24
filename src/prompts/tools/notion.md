## Notion

Use Notion tools when Julián asks about pages, databases, tasks, or notes.

### Which tool to use
- **Find a page by name** → `API-post-search` with the title as `query`
- **Read the content of a page** → `API-get-block-children` with the `block_id` from search results
- **Get page metadata/properties** → `API-retrieve-a-page`
- **Query a database** → `API-query-data-source`
- **Create a page** → `API-post-page`
- **Update page properties** → `API-patch-page`

### Flow to read a page
1. `API-post-search` with the page name
2. Extract the `id` from the result
3. `API-get-block-children` with that `id`

Never use a made-up ID.
