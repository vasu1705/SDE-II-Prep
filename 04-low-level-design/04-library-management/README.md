# LLD 4 — Library Management System

[← Back to LLD](../README.md) · Status: ☐ not started

## Requirements
- Catalog of **books** with multiple physical **copies**; search by title/author/ISBN.
- Members borrow and return copies; **borrowing limit** per member (e.g. 5), loan period (e.g. 14 days).
- **Fine calculation** for overdue returns; block borrowing when fines are unpaid.
- Reservations/holds when no copy is available; notify the next member on return.

## Entities
`Book` (the title) vs `BookItem` (a physical copy with a barcode and status), `Member`, `Librarian`, `Loan(item, member, issuedAt, dueAt, returnedAt)`, `Fine`, `Reservation`, `Catalog`.

## Patterns to apply
- **Strategy** for fine rules (per-day rate, caps, member tiers), **Observer** for reservation notifications, **Factory** for item/member types, **Repository** for storage.

## Key decisions to discuss
- Book vs copy separation (the most common modelling mistake is merging them).
- Time handling: use `java.time.Clock` so overdue logic is testable.
- Who owns the invariants (borrowing limit lives in `Member`/`LoanService`, not in the UI).
- Links: [JPA note for how this would map to tables](../../02-languages/java/06-spring-boot/03-jpa-hibernate.md).

## Extension questions
Different loan periods per item type, renewals, multi-branch libraries, e-books with licence counts.

## Test checklist
- [ ] Borrow up to the limit; the next borrow is rejected
- [ ] Return on time (no fine), 3 days late (fine), fine blocks new loans
- [ ] Reservation fulfilled in order when a copy returns

## Solution
_(add `src/` and links here)_
