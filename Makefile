.PHONY: test test-local test-e2e compile verify proof verify-external-runtime-gate external-runtime-blocked-proof

PYTHON ?= $(shell if [ -x /opt/homebrew/bin/python3 ]; then echo /opt/homebrew/bin/python3; else command -v python3; fi)

compile:
	$(PYTHON) -m compileall -q strategy_studio cli rusr services contracts

test:
	$(PYTHON) -m pytest -q

test-local:
	$(PYTHON) -m pytest -q --ignore=tests/test_system_e2e_sio.py

test-e2e:
	@if [ "$$RIG_ALLOW_EXTERNAL_RUNTIME" != "YES" ]; then \
		$(MAKE) external-runtime-blocked-proof; \
		echo "BLOCKED: set RIG_ALLOW_EXTERNAL_RUNTIME=YES only after OpenClaw/fleet runtime proof exists."; \
		exit 2; \
	fi
	$(PYTHON) -m pytest -q tests/test_system_e2e_sio.py

verify: compile test-local proof

verify-external-runtime-gate: external-runtime-blocked-proof

external-runtime-blocked-proof:
	@mkdir -p proof
	@printf '{\n  "repo": "strategy-studio",\n  "status": "BLOCKED_EXTERNAL_RUNTIME_APPROVAL_REQUIRED",\n  "target": "test-e2e",\n  "required_env": "RIG_ALLOW_EXTERNAL_RUNTIME=YES",\n  "required_proof": "OpenClaw/fleet runtime proof packet",\n  "external_side_effects": "not_executed"\n}\n' > proof/external-runtime-blocked-proof.json
	@cat proof/external-runtime-blocked-proof.json

proof:
	@mkdir -p proof
	@printf '{\n  "repo": "strategy-studio",\n  "status": "LOCAL_VERIFY_COMMANDS_DEFINED",\n  "external_side_effects": "not_executed",\n  "proof_standard": "RIG Verification Doctrine"\n}\n' > proof/local-verification-proof.json
	@cat proof/local-verification-proof.json
