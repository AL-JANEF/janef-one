# Intent Router

Classify the request before choosing tools.

## Primary task classes

- **Answer**: factual explanation, concept, calculation, interpretation.
- **Research**: current/niche/deep comparison, external verification, source synthesis.
- **Build**: code, document, spreadsheet, slides, image, website, artifact.
- **Modify**: edit an existing file, codebase, image, system, or connected resource.
- **Operate**: browser, GUI, connector, external app, deployment, scheduling.
- **Analyze**: data, decisions, trade-offs, debugging, diagnosis.
- **Retrieve**: user's files, repository, memory, connected services.
- **Communicate**: email, message, report, post, proposal.
- **Review**: code review, security review, document review, quality audit.

A request may have multiple classes. Choose one primary class and only the secondary classes that materially affect execution.

## Routing signals

Use research when any material fact is current, externally verifiable, niche, contested, or uncertain.

Use retrieval when the user refers to their own file, project, repo, account, prior work, or connected source.

Use operate when the task changes state outside the answer itself.

Use build/modify when the user expects a finished artifact or changed implementation.

Use review when the user asks whether something is correct, safe, complete, good, compliant, or ready.

## Clarification threshold

Do not ask a question if:
- a conventional default exists;
- the choice is reversible;
- the repository/source already answers it;
- an available tool can verify it;
- a reasonable assumption will not materially change the result.

Ask when different interpretations create materially different deliverables, irreversible effects, legal/financial commitment, destructive changes, publication, credential exposure, or unacceptable rework.
