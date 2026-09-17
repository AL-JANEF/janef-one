.PHONY: validate test benchmark quality package

validate:
	python3 scripts/validate.py

test:
	python3 scripts/test_runtime.py

benchmark:
	python3 scripts/benchmark_runtime.py

quality:
	python3 scripts/quality_gate.py

package:
	python3 scripts/package_release.py
