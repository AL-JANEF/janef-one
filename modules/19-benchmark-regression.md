# Benchmark and Regression Engine

Do not claim superiority from architecture alone. Measure it.

## Required benchmark dimensions
- task completion;
- factual correctness;
- instruction adherence;
- tool routing accuracy;
- skill routing accuracy;
- verification discipline;
- security violations;
- false completion claims;
- recovery after context/state loss;
- context and tool-call efficiency.

## Release gate
A candidate release must not regress critical safety or correctness cases. Performance improvements must be tied to reproducible cases, model/runtime versions, and judge methodology.

Do not convert benchmark scores into universal claims. Scores apply only to the tested tasks, versions, environments, and evaluation protocol.
