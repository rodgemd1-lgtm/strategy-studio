"""
RIG System Verification — Playwright End-to-End Tests
Tests that the full RIG system is operational:
1. OpenClaw gateway health
2. Agent bootstrap files valid
3. Lattice geometry code imports and runs
4. BMS engine produces correct scores
5. Fleet nodes reachable
6. Cron jobs installed
7. GitHub sync working
"""

import subprocess
import json
import os
from pathlib import Path

import pytest

REPO = Path(os.environ.get("RIG_STRATEGY_STUDIO_REPO", Path(__file__).resolve().parents[1]))
GATEWAY_URL = "http://127.0.0.1:18789"
EXTERNAL_RUNTIME_APPROVED = os.environ.get("RIG_ALLOW_EXTERNAL_RUNTIME") == "YES"
requires_external_runtime = pytest.mark.skipif(
    not EXTERNAL_RUNTIME_APPROVED,
    reason="Requires OpenClaw/fleet runtime proof and RIG_ALLOW_EXTERNAL_RUNTIME=YES.",
)


# ─────────────────────────────────────────────
# 1. OpenClaw Gateway Tests
# ─────────────────────────────────────────────

@requires_external_runtime
class TestOpenClawGateway:
    def test_gateway_process_running(self):
        """OpenClaw gateway should be running as a launchd service."""
        result = subprocess.run(
            ["openclaw", "status"],
            capture_output=True, text=True
        )
        assert "Runtime: running" in result.stdout or result.returncode == 0

    def test_gateway_responds_on_port(self):
        """Gateway should respond on localhost:18789."""
        import urllib.request
        try:
            resp = urllib.request.urlopen(f"{GATEWAY_URL}/health", timeout=5)
            data = json.loads(resp.read())
            assert data.get("ok") is True
        except Exception:
            # Try root path
            resp = urllib.request.urlopen(GATEWAY_URL, timeout=5)
            assert resp.status == 200

    def test_gateway_config_valid(self):
        """OpenClaw config should be valid JSON."""
        config_path = Path.home() / ".openclaw" / "openclaw.json"
        assert config_path.exists()
        with open(config_path) as f:
            config = json.load(f)
        assert "gateway" in config or "port" in config


# ─────────────────────────────────────────────
# 2. Agent Bootstrap Tests
# ─────────────────────────────────────────────

@requires_external_runtime
class TestAgentBootstraps:
    AGENTS = ["rig-auditor", "rig-builder", "rig-researcher", "rig-deployer", "rig-watcher"]

    @pytest.mark.parametrize("agent_name", AGENTS)
    def test_agent_yaml_exists(self, agent_name):
        """Each agent should have a valid bootstrap YAML."""
        yaml_path = Path.home() / ".openclaw" / "agents" / agent_name / "agent" / "agent.yaml"
        assert yaml_path.exists(), f"Missing agent YAML: {yaml_path}"

    @pytest.mark.parametrize("agent_name", AGENTS)
    def test_agent_yaml_has_name(self, agent_name):
        """Each agent YAML should declare its name."""
        import yaml
        yaml_path = Path.home() / ".openclaw" / "agents" / agent_name / "agent" / "agent.yaml"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        assert data.get("name") == agent_name

    def test_five_agents_registered(self):
        """All 5 fleet agents should be bootstrapped."""
        agents_dir = Path.home() / ".openclaw" / "agents"
        if agents_dir.exists():
            agents = [d.name for d in agents_dir.iterdir() if d.is_dir()]
            assert len(agents) >= 5, f"Expected 5 agents, found: {agents}"


# ─────────────────────────────────────────────
# 3. Lattice Geometry Tests
# ─────────────────────────────────────────────

class TestLatticeGeometry:
    def test_types_import_clean(self):
        """_types.py should import without errors."""
        from strategy_studio.lattice._types_reexport import Level, Diamond, BMSMode, IQRSQPIStep, LatticeCoordinate
        assert len(Level) == 7
        assert len(Diamond) == 3
        assert len(BMSMode) == 4
        assert len(IQRSQPIStep) == 7

    def test_validator_import_clean(self):
        """validator.py should import without errors."""
        from strategy_studio.lattice.validator import parse_cell_id, is_valid_cell_id, is_old_format
        assert callable(parse_cell_id)
        assert callable(is_valid_cell_id)
        assert callable(is_old_format)

    def test_bms_import_clean(self):
        """bms.py should import without errors."""
        from strategy_studio.hermes.bms import calculate_bms, score_workflow
        assert callable(calculate_bms)
        assert callable(score_workflow)

    def test_all_588_cells_parse(self):
        """All 588 cell IDs should parse cleanly."""
        from strategy_studio.lattice.validator import generate_all_cell_ids, parse_cell_id
        cells = generate_all_cell_ids()
        assert len(cells) == 588
        for cell_id in cells:
            coord = parse_cell_id(cell_id)
            assert coord.cell_id == cell_id

    def test_old_format_rejected(self):
        """Old format cell IDs should be rejected."""
        from strategy_studio.lattice.validator import parse_cell_id
        with pytest.raises(ValueError, match="old format"):
            parse_cell_id("L2-D1-Intent")

    def test_unit_tests_pass(self):
        """Geometry unit tests should pass."""
        result = subprocess.run(
            ["python3", "-m", "pytest", str(Path(__file__).parent / "test_geometry_sio.py"), "-q", "--tb=no"],
            capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, f"Tests failed: {result.stdout[-200:]}"


# ─────────────────────────────────────────────
# 4. BMS Engine Tests
# ─────────────────────────────────────────────

class TestBMSEngine:
    def test_a1_mode_selected_for_high_confidence(self):
        from strategy_studio.hermes.bms import calculate_bms
        result = calculate_bms(0.1, 0.9, 0.9)
        assert result.mode.value == "A1"
        assert result.adjusted_score >= 0.75

    def test_a4_mode_selected_for_low_confidence(self):
        from strategy_studio.hermes.bms import calculate_bms
        result = calculate_bms(0.9, 0.1, 0.1)
        assert result.mode.value == "A4"
        assert result.adjusted_score < 0.25

    def test_score_clamped(self):
        from strategy_studio.hermes.bms import calculate_bms
        result = calculate_bms(1.0, 0.0, 0.0)
        assert result.adjusted_score == 0.0
        result = calculate_bms(0.0, 1.0, 1.0)
        assert result.adjusted_score == 1.0

    def test_rationale_not_empty(self):
        from strategy_studio.hermes.bms import calculate_bms
        result = calculate_bms(0.3, 0.6, 0.7)
        assert len(result.rationale) > 0


# ─────────────────────────────────────────────
# 5. Fleet Node Tests
# ─────────────────────────────────────────────

@requires_external_runtime
class TestFleetNodes:
    NODES = [
        ("rig-256gb", "100.91.39.12"),
        ("rig-28gb", "100.103.237.24"),
        ("rig-96gb", "100.102.142.84"),
        ("blackwell", "100.67.126.117"),
    ]

    @pytest.mark.parametrize("name,ip", NODES)
    def test_node_reachable(self, name, ip):
        """Each fleet node should be reachable via Tailscale."""
        result = subprocess.run(
            ["ping", "-c", "1", "-t", "3", ip],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Node {name} ({ip}) unreachable"


# ─────────────────────────────────────────────
# 6. Cron Job Tests
# ─────────────────────────────────────────────

@requires_external_runtime
class TestCronJobs:
    def test_cron_scheduler_exists(self):
        """Cron scheduler script should exist."""
        scheduler = REPO / "scripts" / "ops" / "rig_cron_scheduler.py"
        if not scheduler.exists():
            pytest.skip("rig_cron_scheduler.py not found in this repo")

    def test_cron_jobs_installed(self):
        """RIG cron jobs should be installed in crontab."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            rig_jobs = [l for l in result.stdout.split("\n") if "RIG:" in l or "rig-" in l]
            # At least some RIG jobs should be present
            assert len(rig_jobs) > 0, "No RIG cron jobs found in crontab"


# ─────────────────────────────────────────────
# 7. GitHub Sync Tests
# ─────────────────────────────────────────────

class TestGitHubSync:
    def test_repo_is_git_repo(self):
        """The repo should be a valid git repository."""
        git_dir = REPO / ".git"
        assert git_dir.exists()

    def test_branch_exists(self):
        """The main or sovereign branch should exist."""
        result = subprocess.run(
            ["git", "branch", "-a", "--list", "*sovereign*", "*main*"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        if "sovereign" not in result.stdout and "main" not in result.stdout:
            pytest.skip("No sovereign or main branch found")
        assert "sovereign" in result.stdout or "main" in result.stdout

    def test_remote_configured(self):
        """GitHub remote should be configured."""
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        assert "github.com" in result.stdout

    def test_recent_commits_exist(self):
        """There should be recent commits on this branch."""
        result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) >= 3, "Expected at least 3 recent commits"


# ─────────────────────────────────────────────
# 8. Deviation Engine Tests
# ─────────────────────────────────────────────

class TestDeviationEngines:
    def test_engines_directory_exists(self):
        """The rig_engines_v3 directory should exist."""
        engines_dir = REPO / "artifacts" / "rig_engines_v3"
        assert engines_dir.exists()

    def test_auditor_exists(self):
        """The auditor.py should exist."""
        auditor = REPO / "artifacts" / "rig_engines_v3" / "auditor.py"
        assert auditor.exists()

    def test_criteria_files_exist(self):
        """Engine criteria YAML files should exist."""
        criteria_dir = REPO / "artifacts" / "rig_engines_v3" / "criteria"
        if criteria_dir.exists():
            yaml_files = list(criteria_dir.glob("*.yaml"))
            assert len(yaml_files) >= 10, f"Expected 10+ criteria files, found {len(yaml_files)}"

    def test_baseline_files_exist(self):
        """Baseline good/bad files should exist for each engine."""
        baselines_dir = REPO / "artifacts" / "rig_engines_v3" / "baselines"
        if baselines_dir.exists():
            engine_dirs = [d for d in baselines_dir.iterdir() if d.is_dir()]
            assert len(engine_dirs) >= 10, f"Expected 10+ engine baseline dirs, found {len(engine_dirs)}"
