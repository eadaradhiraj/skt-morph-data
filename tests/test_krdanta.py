"""Tests for Kṛdanta (verbal participle) declension bridge."""

from __future__ import annotations

import unittest

from skt_morph_data.krdanta import (
    decline_participle,
    get_dhatu_participles_summary,
    list_participle_pratyayas,
    normalize_pratyaya,
)


class TestKrdanta(unittest.TestCase):
    def test_normalize_pratyaya(self):
        self.assertEqual(normalize_pratyaya("shatri"), "Satf")
        self.assertEqual(normalize_pratyaya("satr"), "Satf")
        self.assertEqual(normalize_pratyaya("anIya"), "anIyar")
        self.assertEqual(normalize_pratyaya("sanac"), "SAnac")
        self.assertEqual(normalize_pratyaya("trc"), "tfc")
        self.assertEqual(normalize_pratyaya("kta"), "kta")

    def test_list_participle_pratyayas(self):
        pratyayas = list_participle_pratyayas("BU")
        self.assertIn("kta", pratyayas)
        self.assertIn("ktavatu", pratyayas)
        self.assertIn("Satf", pratyayas)
        self.assertIn("tavya", pratyayas)

    def test_kta_participle(self):
        # BU + kta -> BUta
        res_m = decline_participle("BU", "kta", gender="m")
        self.assertEqual(res_m["gender"], "m")
        self.assertEqual(res_m["forms"]["prathamA"], ["BUtaH", "BUtO", "BUtAH"])
        self.assertEqual(res_m["forms"]["tftIyA"][0], "BUtena")

        res_f = decline_participle("BU", "kta", gender="f")
        self.assertEqual(res_f["gender"], "f")
        self.assertEqual(res_f["forms"]["prathamA"], ["BUtA", "BUte", "BUtAH"])

        res_n = decline_participle("BU", "kta", gender="n")
        self.assertEqual(res_n["gender"], "n")
        self.assertEqual(res_n["forms"]["prathamA"], ["BUtam", "BUte", "BUtAni"])

    def test_ktavatu_participle(self):
        # kf + ktavatu -> kftavat
        res = decline_participle("kf", "ktavatu")
        self.assertIn("m", res["genders"])
        self.assertIn("f", res["genders"])
        self.assertIn("n", res["genders"])

        self.assertEqual(res["genders"]["m"]["prathamA"], ["kftavAn", "kftavantO", "kftavantaH"])
        self.assertEqual(res["genders"]["f"]["prathamA"], ["kftavatI", "kftavatyO", "kftavatyaH"])
        self.assertEqual(res["genders"]["n"]["prathamA"], ["kftavat", "kftavatI", "kftavanti"])

    def test_satr_participle(self):
        # gam + Satf -> gacCat
        res_m = decline_participle("gam", "Satf", gender="m")
        self.assertEqual(res_m["forms"]["prathamA"], ["gacCan", "gacCantO", "gacCantaH"])
        self.assertEqual(res_m["forms"]["tftIyA"][0], "gacCatA")

        res_f = decline_participle("gam", "Satf", gender="f")
        self.assertEqual(res_f["forms"]["prathamA"], ["gacCantI", "gacCantyO", "gacCantyaH"])

        res_n = decline_participle("gam", "Satf", gender="n")
        self.assertEqual(res_n["forms"]["prathamA"], ["gacCat", "gacCatI", "gacCanti"])

    def test_tfc_agent_noun(self):
        # BU + tfc -> Bavitf
        res_m = decline_participle("BU", "tfc", gender="m")
        self.assertEqual(res_m["forms"]["prathamA"], ["BavitA", "BavitArO", "BavitAraH"])

        res_f = decline_participle("BU", "tfc", gender="f")
        self.assertEqual(res_f["forms"]["prathamA"], ["BavitrI", "BavitryO", "BavitryaH"])

    def test_gerundives_tavya_aniyar(self):
        # tavya
        res = decline_participle("BU", "tavya", gender="m")
        self.assertEqual(res["forms"]["prathamA"], ["BavitavyaH", "BavitavyO", "BavitavyAH"])

        # anIyar (alias anIya)
        res_aniyar = decline_participle("BU", "anIya", gender="n")
        self.assertEqual(res_aniyar["forms"]["prathamA"], ["BavanIyam", "BavanIye", "BavanIyAni"])

    def test_kvasu_participle(self):
        # BU + kvasu -> baBUvas
        res_m = decline_participle("BU", "kvasu", gender="m")
        self.assertEqual(res_m["forms"]["prathamA"], ["baBUvAn", "baBUvAMsO", "baBUvAMsaH"])
        self.assertEqual(res_m["forms"]["tftIyA"][1], "baBUvadByAm")

    def test_indeclinables(self):
        # ktvA
        res_ktva = decline_participle("BU", "ktvA")
        self.assertTrue(res_ktva["is_avyaya"])
        self.assertEqual(res_ktva["form"], "BUtvA")

        # tumun
        res_tumun = decline_participle("gam", "tumun")
        self.assertTrue(res_tumun["is_avyaya"])
        self.assertEqual(res_tumun["form"], "gantum")

    def test_participles_summary(self):
        summary = get_dhatu_participles_summary("BU")
        self.assertGreater(len(summary), 10)
        pratyayas = [s["pratyaya"] for s in summary]
        self.assertIn("kta", pratyayas)
        self.assertIn("ktavatu", pratyayas)


if __name__ == "__main__":
    unittest.main()
