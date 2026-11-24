# Client Archive Workflow

## Workflow

```mermaid
flowchart TD
    A[Client Management] --> B{Choose client action}
    B -->|Archive| C[PATCH /customers/:id/archive]
    C --> D[Set client is_archived = true]
    D --> E[Client hidden from active client lists]
    E --> F[Existing challans, invoices, rates and IDs remain unchanged]

    G[Create challan or invoice] --> H[GET /customers]
    H --> I[Return active clients only]
    I --> J[User selects an active client]
    J --> K[API validates client is active]
    K --> L[Save new document]

    M[Historical challan, invoice or summary] --> N[GET /customers?include_archived=true]
    N --> O[Archived clients appear in history filters]
    O --> P[Existing documents fetched by their existing IDs]

    Q[Edit existing challan] --> R[Load challan and customer_id]
    R --> S[Load client by ID if absent from active list]
    S --> T[Keep that archived client attached]
    T --> U[Reject assigning a different archived client]

    V[Client Management: Archived filter] --> W[Archived clients list]
    W --> X[PATCH /customers/:id/restore]
    X --> Y[Set client is_archived = false]
    Y --> Z[Client returns to active lists]
```

## Affected areas

- **Backend model and startup migration:** add `customer.is_archived`, default existing clients to active, and serialize the status.
- **Customer API:** active-only list by default, explicit archived-inclusive list, ID lookup, archive and restore actions, and server-side guards for creating or reassigning documents.
- **Client Management:** active/archived filter and archive/restore controls for API-authorized roles.
- **Challan and invoice workflows:** active clients for new documents; historical lists and summaries include archived clients; archived clients cannot be assigned to new invoices or challans.
- **Existing records:** retain client IDs and relations so old challans, invoices, customer details, rates, and print/export paths keep working.

## API behavior

| Request | Behavior |
| --- | --- |
| `GET /api/customers` | Active clients only |
| `GET /api/customers?include_archived=true` | Active and archived clients |
| `GET /api/customers/:id` | Fetch a client by ID, including archived clients |
| `PATCH /api/customers/:id/archive` | Archive the client |
| `PATCH /api/customers/:id/restore` | Restore the client |

Archiving a client does not archive its challans or invoices. Their existing archive controls remain independent.
