# RNG Parity Tests (JS <-> Python)

This folder stores parity assets for RNG contract v1.

## Files
- parity_vectors.json: canonical expected outputs.

## Required test flow
1) Implement RNG in JS and Python according to docs/RNG_CONTRACT.md.
2) Load each case from parity_vectors.json.
3) For each case, run:
   - set_seeds(seed_a, seed_b)
   - derive_seed_c(context)
   - compare expected seed_c
   - compare first10_u32
   - compare first3_float
   - compare sample randint values for ranges [0,0], [0,5], [10,20]

## Error parity checks (must be added in both suites)
- next_u32 before set_seeds => must fail.
- non-integer seeds/context => must fail.
- randint(min, max) where min > max => must fail.
- randint range size > 2^32 => must fail.

## Acceptance
- All vector checks pass in both languages with exact equality.
- Any mismatch blocks migration to next phase.
