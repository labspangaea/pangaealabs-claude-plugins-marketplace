# Code style + error wrapping (Go)

Local style rules baked into the scaffolder templates. The cross-cutting `peruri-code-standard/references/go.md` is the broader rulebook for the wider codebase; what's here is the subset the templates enforce by construction.

## Style table

| Rule | Do | Don't |
|------|----|-------|
| Format | `gofmt` on every file | any unformatted output |
| Package names | `handler`, `repository`, `service` | `httpHandler`, `order_repository` |
| Getters | `Owner()` | `GetOwner()` |
| Interfaces | `Reader`, `Publisher` (-er suffix, single method) | `IOrderRepository` |
| Casing | `MixedCaps` | `snake_case` in Go names |
| Stutter | `order.Service` | `order.OrderService` |
| Constructors | `New(...)` returns concrete type | `NewOrderService(...)` |
| Options | `...Option` for >2 constructor params | long positional arg lists |
| Context | first param on all I/O functions | omitting ctx or passing `context.Background()` deep in call stack |
| Comments | package doc + exported symbol doc comments | no comments on exported symbols |
| Imports | `stdlib` → *(blank)* → `external` → *(blank)* → `internal` | mixed import groups |

## Error wrapping pattern

```go
// repository layer — lowercase, no trailing punctuation, include id
return nil, fmt.Errorf("repository: find order %s: %w", id, err)

// service layer
return nil, fmt.Errorf("service: find order %s: %w", id, err)
```

## Error anti-patterns

| Anti-pattern | Correct pattern |
|---|---|
| `_ = err` | always handle or return |
| `errors.New("Error finding record")` | `fmt.Errorf("repository: find %s: %w", id, err)` |
| `return errors.New("not found")` | `return domain.ErrNotFound` (sentinel) |
| wrap at every layer without adding context | wrap only when adding new information |
