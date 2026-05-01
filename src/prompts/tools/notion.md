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

### Managing Tasks
- **To find tasks**: Always search for the tasks database first. Use `API-post-search` with `query: "Tareas"` (or the relevant name) and `filter: {"property": "object", "value": "database"}` to get the database `id`.
- **To read today's tasks**: Use `API-query-data-source` with the database `id` you just found. Do not guess the ID.
- **To add a task**: Use `API-post-page` setting the parent to the database `id`.

Never use a made-up ID. Always search for the page or database first to get its real `id`.

