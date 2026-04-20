# RNG Contract v1 (JS <-> Python)

## 1 Purpose
This contract defines a deterministic RNG module that can be mirrored in JavaScript and Python with parity guarantees.

Primary goals:
- Same input seeds + same context => same output sequence in both languages.
- RNG logic fully independent from rendering, UI, and game loop.
- Stable API for migration phases.

Out of scope:
- Computer vision integration.
- Replacing gameplay logic in this phase.

## 2 Public API (must match in JS and Python)

Required methods:
- set_seeds(seed_a, seed_b)
- derive_seed_c(context)
- next_u32()
- next_float()
- randint(min, max)

Behavior summary:
- set_seeds(seed_a, seed_b): stores normalized seeds and resets internal stream using default context.
- derive_seed_c(context): deterministically computes seed_c from seed_a, seed_b, and context; resets stream.
- next_u32(): returns next unsigned 32-bit integer in [0, 4294967295].
- next_float(): returns next double in [0.0, 1.0), computed as next_u32() / 2^32.
- randint(min, max): returns integer in inclusive range [min, max], unbiased (rejection sampling).

## 3 Data Types and Normalization

### 3.1 u32 normalization
All internal arithmetic must be modulo 2^32.

Formal function:
- to_u32(x) = ((x mod 2^32) + 2^32) mod 2^32

### 3.2 Accepted numeric input
- seed_a, seed_b, and all context fields must be integers.
- Non-integer values (NaN, Infinity, float with decimals, string, null) must fail.

Language mapping:
- JS: throw TypeError for non-integer input.
- Python: raise TypeError for non-integer input.

## 4 Context Schema for derive_seed_c(context)

Context is a dictionary/object with optional u32 fields:
- version (default 1)
- session_nonce (default 0)
- round (default 0)
- map_index (default 0)
- mode (default 0)

All missing fields use defaults above.
All provided fields are normalized with to_u32.

## 5 Normative Algorithms

## 5.1 rotl32
rotl32(x, r): left rotate u32 x by r bits.

## 5.2 mix32 (Murmur3 finalizer style)
Given x (u32):
1) x = x xor (x >>> 16)
2) x = (x * 0x85EBCA6B) mod 2^32
3) x = x xor (x >>> 13)
4) x = (x * 0xC2B2AE35) mod 2^32
5) x = x xor (x >>> 16)
6) return x

## 5.3 derive_seed_c(context)
Starting with c = 0x9E3779B9, apply in order:
1) c = mix32(c xor seed_a)
2) c = mix32(c xor rotl32(seed_b, 16))
3) c = mix32(c xor context.version)
4) c = mix32(c xor context.session_nonce)
5) c = mix32(c xor context.round)
6) c = mix32(c xor context.map_index)
7) c = mix32(c xor context.mode)

If c == 0, replace with fallback 0xA341316C.

State reset rule:
- After derive_seed_c(context), stream state is reset:
  - x = seed_a != 0 ? seed_a : 0x6D2B79F5
  - y = seed_b != 0 ? seed_b : 0x1B56C4E9
  - z = seed_c
- If (x | y | z) == 0, force z = 0xA341316C.
- calls counter resets to 0.

## 5.4 Core generator: xorshift96
next_u32() uses xorshift96 with state (x, y, z):
1) t = x
2) t = t xor ((t << 16) mod 2^32)
3) t = t xor (t >>> 5)
4) t = t xor ((t << 1) mod 2^32)
5) x = y
6) y = z
7) z = t xor x xor y
8) return to_u32(z)

## 5.5 next_float()
- Return next_u32() / 4294967296.0
- Range: [0.0, 1.0)

## 5.6 randint(min, max)
- Inclusive bounds [min, max].
- Preconditions:
  - min and max must be integers.
  - min <= max.
  - span = max - min + 1 must be in [1, 4294967296].

Unbiased algorithm:
1) span = max - min + 1
2) if span == 1: return min
3) limit = floor(4294967296 / span) * span
4) repeat r = next_u32() while r >= limit
5) return min + (r mod span)

## 6 Edge Cases and Expected Results

### 6.1 Seed edge cases
- seed_a = 0 and seed_b = 0: valid; fallback protection must still avoid all-zero stream.
- Negative seed input: valid only if integer; normalized via to_u32.
- seed > 2^32 - 1: valid only if integer; normalized via to_u32.

### 6.2 Context edge cases
- Missing context: use defaults.
- Partial context: missing keys use defaults.
- Non-integer context value: fail (TypeError).

### 6.3 API misuse
- Calling next_u32/next_float/randint before set_seeds: fail (state not initialized).
- randint(min, max) with min > max: fail (RangeError/ValueError).
- randint with span > 2^32: fail (RangeError/ValueError).

### 6.4 Determinism guarantees
- Same normalized seed_a, seed_b, and context => same seed_c and same sequence.
- Any change in seed or context field must change the sequence (avalanche expected, not cryptographic).

## 7 Parity Test Specification

## 7.1 Canonical vectors
Use file:
- tests/rng/parity_vectors.json

Each test case defines:
- seed_a, seed_b, context
- expected seed_c
- expected first10_u32
- expected first3_float
- expected sample randint outputs

## 7.2 Required parity suites

Suite A: deterministic replay (per language)
- Same seeds/context run twice => identical outputs.

Suite B: JS vs Python vector parity
- For each vector case, assert exact equality for:
  - seed_c
  - first10_u32
  - first3_float
  - sample randint outputs

Suite C: normalization parity
- Include negative and overflow seeds.
- Assert same normalized seed behavior in both languages.

Suite D: edge/error parity
- Invalid types must fail.
- Invalid ranges must fail.
- Uninitialized generator must fail.

Suite E: statistical sanity (non-blocking)
- 1e6 samples rough uniformity checks (buckets).
- This suite validates gross mistakes, not cryptographic quality.

## 7.3 Acceptance criteria
A build is parity-compliant only if:
- 100% pass in Suites A-D.
- No mismatch in any canonical vector.
- Any algorithm change requires contract version bump and new vectors.

## 8 Versioning Policy
- Contract starts at v1.
- Any change to normalization, derive order, generator core, or randint bias logic is a breaking change.
- Breaking changes require:
  - v2 contract document
  - new vector file
  - migration note for both JS and Python implementations.
