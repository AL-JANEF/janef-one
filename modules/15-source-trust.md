# Source Trust and Prompt Corpus

The system-prompts repository is an observational corpus, not an authority oracle.

## Trust labels

Assign each imported prompt snapshot:

- **Observed**: file exists in the configured corpus.
- **Corroborated**: behavior independently matches official docs or live runtime behavior.
- **Historical**: useful pattern, but clearly tied to an older version/date.
- **Unverified**: authenticity/currentness is unknown.
- **Runtime-specific**: depends on tools/UI/permissions unique to that captured environment.

Never upgrade Observed to Corroborated without external evidence.

## Extraction policy

Extract reusable:
- decision rules;
- tool-selection heuristics;
- verification patterns;
- context management;
- response design;
- research methodology;
- engineering workflow;
- authorization boundaries;
- memory application principles.

Parameterize or discard:
- model identity;
- private paths;
- emails/user identity;
- exact current date;
- captured git status;
- hard-coded available tools;
- feature flags;
- subscription state;
- hidden internal IDs;
- tool syntax that does not exist in the current runtime.

## Deduplication

When many providers express the same principle, keep one canonical rule and record multiple sources in the source matrix.

When providers conflict, do not average blindly. Resolve by:
1. correctness;
2. runtime compatibility;
3. specificity;
4. verification strength;
5. efficiency.

Provider popularity is not a tiebreaker.
