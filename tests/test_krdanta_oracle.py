"""Tier 3 Golden Gate CI Test for Krdanta Subantas against ground-truth tables in data/subanta_test/."""
import json
import unittest
from pathlib import Path
from skt_morph_data.krdanta import (
    krt_table,
    normalize_pratyaya,
    krt_ref_slot,
)
from skt_morph_data.subanta import VIBHAKTIS, VACANAS, VIBHAKTI_INDEX, VACANA_INDEX

REPO_ROOT = Path(__file__).resolve().parents[1]
SUBANTA_TEST_DIR = REPO_ROOT / "data" / "subanta_test"

TABLE_VIBHAKTI_INDEX = {
    "praTamA": 1, "prathamA": 1,
    "dvitIyA": 2,
    "tFtIyA": 3, "tftIyA": 3,
    "caturTI": 4,
    "paYcamI": 5,
    "zazWI": 6,
    "saptamI": 7,
    "sambodana": 8, "saMboDana": 8, "sambodhana": 8,
}
TABLE_VACANA_INDEX = {
    "eka": 1, "dvi": 2, "bahu": 3,
}

def normalize_cell_forms(forms: list[str]) -> set[str]:
    return {f.removeprefix("he ").strip() for f in forms if f.strip()}

class TestKrdantaOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bu_file = SUBANTA_TEST_DIR / "01" / "01.0001.json"
        if not cls.bu_file.exists():
            raise unittest.SkipTest(f"Missing test data at {cls.bu_file}")
        with open(cls.bu_file, "r", encoding="utf-8") as f:
            cls.bu_data = json.load(f)

    def _verify_entries(self, entries: list[dict], family: str, dhatu_id: str):
        total_cells = 0
        passed_cells = 0
        discrepancies = []

        for entry in entries:
            if not entry.get("table_ok"):
                continue
            pratyaya = entry["pratyaya"]
            ref = entry["ref"]
            g_raw = entry.get("gender", "")
            gender = "m" if g_raw in ("pu", "puM", "m") else ("f" if g_raw in ("strI", "str", "f") else "n")
            exp_table = entry["table"]
            displays = entry.get("displays", [])
            val = displays[0] if displays else entry["pratipadika"]

            tab = krt_table(family, pratyaya, gender, val, dhatu_id)
            if tab is None:
                tab = krt_table(family, pratyaya, gender, entry["pratipadika"], dhatu_id)

            self.assertIsNotNone(tab, f"Failed to generate table for {dhatu_id} + {pratyaya} ({gender}) in {family}")

            for vibh, vac_dict in exp_table.items():
                v_idx = TABLE_VIBHAKTI_INDEX.get(vibh)
                if not v_idx:
                    continue
                for vac, exp_forms in vac_dict.items():
                    vc_idx = TABLE_VACANA_INDEX.get(vac)
                    if not vc_idx:
                        continue
                    exp_set = normalize_cell_forms(exp_forms)
                    slot = next((c for c in tab.cells if c.vibhakti == v_idx and c.vacana == vc_idx), None)
                    act_set = normalize_cell_forms(slot.forms) if slot else set()

                    total_cells += 1
                    if exp_set == act_set:
                        passed_cells += 1
                    else:
                        discrepancies.append((pratyaya, gender, ref, f"{vibh}.{vac}", exp_set, act_set))

        return total_cells, passed_cells, discrepancies

    def test_bu_all_5_families_base(self):
        """Test BU (01.0001) base across all 5 families: krut, san, nich, yang, yangluk."""
        for fam in ("krut", "san_krut", "nich_krut", "yang_krut", "yangluk_krut"):
            entries = self.bu_data.get("base", {}).get(fam, [])
            total, passed, discrepancies = self._verify_entries(entries, fam, "01.0001")
            self.assertGreater(total, 500, f"Expected >500 cells in {fam}")
            # Target >99% agreement on all 24 slots
            rate = passed / total
            self.assertGreaterEqual(rate, 0.99, f"Family {fam} pass rate {rate:.2%} below 99%: {discrepancies[:5]}")

    def test_bu_upasargas_sampled(self):
        """Test BU (01.0001) under sampled prefixes: pra, pari, sam, ud."""
        upas = self.bu_data.get("upasarga", {})
        for pfx in ("pra", "pari", "sam", "ud"):
            if pfx not in upas:
                continue
            pfx_obj = upas[pfx]
            entries = pfx_obj.get("tabs", {}).get("krut", [])
            total, passed, discrepancies = self._verify_entries(entries, "krut", "01.0001")
            self.assertGreater(total, 500, f"Expected >500 cells in {pfx}")
            rate = passed / total
            self.assertGreaterEqual(rate, 0.99, f"Prefix {pfx} pass rate {rate:.2%} below 99%: {discrepancies[:5]}")

if __name__ == "__main__":
    unittest.main()
