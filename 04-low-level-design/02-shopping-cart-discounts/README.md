# LLD 2 — Shopping Cart with Discount / Coupon Rules

[← Back to LLD](../README.md) · Status: ☐ not started · Priority: ⭐

## Requirements
- Add/remove/update items; compute subtotal, discounts, tax, total.
- Discount types: percentage off, fixed amount off, buy-X-get-Y, category-specific, minimum-spend, first-order, **coupon codes**.
- Rules must be **composable**: stacking, priority order, exclusivity ("not combinable with other coupons"), per-item vs per-cart scope.
- Explain which rules were applied (receipt breakdown).

## Entities (starting point)
`Cart`, `CartItem(sku, qty, unitPrice)`, `Money` (value object), `Coupon`, `DiscountRule`, `PricingResult(lines, discounts, total)`.

## Patterns to apply
- **Strategy** (each rule computes a discount), **Chain of Responsibility** or a rule pipeline for ordered application, **Specification** (is this rule applicable?), **Builder** for the cart/pricing context.

## Key decisions to discuss
- **Money:** `BigDecimal` with explicit rounding mode, or integer minor units (cents). Never `double`.
- **Order of application** changes the total (percentage-then-fixed vs fixed-then-percentage) — make it explicit and testable.
- Rule conflicts and a cap (a discount can never take the total below zero).
- Idempotent re-pricing: the same cart and rules always give the same total.
- Links: [choosing the right tool (records for value objects)](../../02-languages/java/01-java-basics/09-choosing-the-right-tool.md), [BigDecimal notes](../../02-languages/java/01-java-basics/02-primitives-wrappers-equality.md).

## Extension questions
Time-boxed promotions, usage limits per user, A/B pricing, tax by region, currency conversion.

## Test checklist
- [ ] Each rule alone; two rules stacked; exclusive coupon blocks others
- [ ] Rounding (e.g. 33.33% of 10.00); zero-quantity edge
- [ ] Discount never exceeds the subtotal

## Solution
_(add `src/` and links here)_
