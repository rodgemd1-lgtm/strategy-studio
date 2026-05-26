"""Tests for Innovation Ingestion module."""

import json

import pytest

from strategy_studio.studios.innovation_ingestion import (
    METHODOLOGIES,
    MethodologyLibrary,
)


# ---------------------------------------------------------------------------
# Catalog tests
# ---------------------------------------------------------------------------

class TestMethodologiesCatalog:
    def test_at_least_8_entries(self):
        assert len(METHODOLOGIES) >= 8

    def test_all_16_frameworks_present(self):
        expected_ids = [
            "strategos", "ideo", "frog", "sit", "board_of_innovation",
            "innosight", "doblin", "synectics", "brainzooming", "cps",
            "triz", "scamper", "biomimicry", "blue_ocean", "jobs_to_be_done",
            "effectuation",
        ]
        for fw_id in expected_ids:
            assert fw_id in METHODOLOGIES, f"Missing framework: {fw_id}"

    def test_each_has_required_keys(self):
        required = {
            "id", "name", "firm", "year", "creator", "steps",
            "mechanism", "evaluation_criteria", "banned_phrases",
            "cross_domain_potential", "category",
        }
        for _k, v in METHODOLOGIES.items():
            missing = required - set(v.keys())
            assert not missing, f"{_k} missing keys: {missing}"

    def test_steps_is_nonempty_list(self):
        for _k, v in METHODOLOGIES.items():
            assert isinstance(v["steps"], list), f"{_k} steps not a list"
            assert len(v["steps"]) >= 3, f"{_k} has fewer than 3 steps"

    def test_year_is_int(self):
        for _k, v in METHODOLOGIES.items():
            assert isinstance(v["year"], int), f"{_k} year not int"

    def test_categories_are_strings(self):
        for _k, v in METHODOLOGIES.items():
            assert isinstance(v["category"], str) and v["category"], f"{_k} bad category"

    def test_banned_phrases_populated(self):
        for _k, v in METHODOLOGIES.items():
            assert len(v["banned_phrases"]) >= 1, f"{_k} has no banned phrases"


# ---------------------------------------------------------------------------
# MethodologyLibrary tests
# ---------------------------------------------------------------------------

@pytest.fixture
def lib():
    return MethodologyLibrary()


class TestGetAll:
    def test_returns_list(self, lib):
        result = lib.get_all()
        assert isinstance(result, list)

    def test_returns_all_16(self, lib):
        assert len(lib.get_all()) == len(METHODOLOGIES)

    def test_no_internal_mutation(self, lib):
        all_items = lib.get_all()
        all_items[0]["name"] = "MUTATED"
        assert lib.get_all()[0]["name"] != "MUTATED"


class TestGetByCategory:
    def test_existing_category(self, lib):
        results = lib.get_by_category("design")
        assert len(results) >= 2  # IDEO + Frog

    def test_case_insensitive(self, lib):
        assert lib.get_by_category("Design") == lib.get_by_category("design")

    def test_nonexistent_returns_empty(self, lib):
        assert lib.get_by_category("nonexistent_category_xyz") == []

    def test_entries_have_correct_category(self, lib):
        results = lib.get_by_category("strategy")
        for item in results:
            assert item["category"] == "strategy"


class TestGetRandom:
    def test_returns_n_items(self, lib):
        result = lib.get_random(3, seed=42)
        assert len(result) == 3

    def test_deterministic_with_seed(self, lib):
        a = lib.get_random(5, seed=99)
        b = lib.get_random(5, seed=99)
        assert a == b

    def test_different_seeds_differ(self, lib):
        a = lib.get_random(5, seed=1)
        b = lib.get_random(5, seed=2)
        assert a != b

    def test_n_exceeds_catalog(self, lib):
        result = lib.get_random(100, seed=7)
        assert len(result) == len(METHODOLOGIES)

    def test_all_items_valid_ids(self, lib):
        result = lib.get_random(16, seed=0)
        for item in result:
            assert item["id"] in METHODOLOGIES


class TestCombine:
    def test_returns_hybrid(self, lib):
        hybrid = lib.combine("ideo", "blue_ocean")
        assert hybrid["source_ids"] == ["ideo", "blue_ocean"]

    def test_hybrid_has_interleaved_steps(self, lib):
        hybrid = lib.combine("cps", "scamper")
        steps = hybrid["steps"]
        # Every step carries a source tag
        for s in steps:
            assert s.startswith("[")
        assert len(steps) >= len(METHODOLOGIES["cps"]["steps"])
        assert len(steps) >= len(METHODOLOGIES["scamper"]["steps"])

    def test_hybrid_has_merged_criteria(self, lib):
        hybrid = lib.combine("triz", "biomimicry")
        a = METHODOLOGIES["triz"]
        b = METHODOLOGIES["biomimicry"]
        # All original criteria present
        for c in a["evaluation_criteria"]:
            assert c in hybrid["evaluation_criteria"]
        for c in b["evaluation_criteria"]:
            assert c in hybrid["evaluation_criteria"]

    def test_hybrid_has_merged_banned_phrases(self, lib):
        hybrid = lib.combine("jobs_to_be_done", "effectuation")
        for phrase in METHODOLOGIES["jobs_to_be_done"]["banned_phrases"]:
            assert phrase in hybrid["banned_phrases"]

    def test_hybrid_category_is_composite(self, lib):
        hybrid = lib.combine("strategos", "synectics")
        assert "+" in hybrid["category"]

    def test_hybrid_year_is_max(self, lib):
        a = METHODOLOGIES["triz"]["year"]
        b = METHODOLOGIES["scamper"]["year"]
        hybrid = lib.combine("triz", "scamper")
        assert hybrid["year"] == max(a, b)

    def test_hybrid_mechanism_text(self, lib):
        hybrid = lib.combine("brainzooming", "cps")
        assert "brainzooming" in hybrid["mechanism"].lower()
        assert "cps" in hybrid["mechanism"].lower()


class TestFindMouth:
    def test_exact_id_match(self, lib):
        result = lib.find_mouth("ideo")
        assert result["id"] == "ideo"

    def test_partial_name_match(self, lib):
        result = lib.find_mouth("Blue Ocean")
        assert result["id"] == "blue_ocean"

    def test_partial_firm_match(self, lib):
        result = lib.find_mouth("IDEO")
        assert result["id"] == "ideo"

    def test_partial_creator_match(self, lib):
        result = lib.find_mouth("Altshuller")
        assert result["id"] == "triz"

    def test_unknown_raises(self, lib):
        with pytest.raises(KeyError):
            lib.find_mouth("totally_unknown_framework_12345")


class TestScoreGenericPenalty:
    def test_clean_text_scores_zero(self, lib):
        score = lib.score_generic_penalty(
            "We analyzed the contradiction using systematic inventive thinking "
            "and mapped job-to-be-done outcomes for the underserved segment."
        )
        assert score == 0.0

    def test_banned_phrase_detected(self, lib):
        score = lib.score_generic_penalty(
            "This disruptive innovation creates a seamless experience with network effects."
        )
        assert score > 0.0

    def test_higher_for_more_banned(self, lib):
        low = lib.score_generic_penalty("synergy")
        high = lib.score_generic_penalty("synergy disruption pivot paradigm shift")
        assert high >= low

    def test_case_insensitive(self, lib):
        score_lower = lib.score_generic_penalty("synergy core competency")
        score_upper = lib.score_generic_penalty("SYNERGY CORE COMPETENCY")
        assert score_lower == score_upper

    def test_score_in_range(self, lib):
        for text in ["", "clear", "synergy disruption pivot best practice revolutionary game-changing"]:
            s = lib.score_generic_penalty(text)
            assert 0.0 <= s <= 1.0


class TestToJson:
    def test_returns_valid_json(self, lib):
        raw = lib.to_json()
        data = json.loads(raw)
        assert isinstance(data, dict)

    def test_json_contains_all_entries(self, lib):
        data = json.loads(lib.to_json())
        assert len(data) == len(METHODOLOGIES)

    def test_key_order_sorted(self, lib):
        data = json.loads(lib.to_json())
        keys = list(data.keys())
        assert keys == sorted(keys)

    def test_writes_to_file(self, lib, tmp_path):
        out = tmp_path / "output" / "methodologies.json"
        lib.to_json(out)
        assert out.exists()
        parsed = json.loads(out.read_text(encoding="utf-8"))
        assert "ideo" in parsed

    def test_roundtrip(self, lib, tmp_path):
        out = tmp_path / "roundtrip.json"
        lib.to_json(out)
        raw = out.read_text(encoding="utf-8")
        data = json.loads(raw)
        rebuilt = MethodologyLibrary(methodologies=data)
        assert len(rebuilt.get_all()) == len(lib.get_all())


class TestCustomMethodologies:
    def test_custom_lib_ignores_defaults(self):
        custom = {"custom_fw": {"id": "custom_fw", "name": "Custom", "firm": "TestCo", "year": 2025,
                                "creator": "Test", "steps": [""], "mechanism": "",
                                "evaluation_criteria": [], "banned_phrases": [],
                                "cross_domain_potential": [], "category": "test"}}
        lib = MethodologyLibrary(methodologies=custom)
        assert len(lib.get_all()) == 1
        assert lib.get_all()[0]["id"] == "custom_fw"
