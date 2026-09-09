"""Unit tests for Sanskrit subanta (nominal declensions) module."""

import unittest
from skt_morph_data.subanta import (
    decline,
    decline_noun,
    decline_pronoun,
    decline_numeral,
    analyze_form,
    detect_paradigm,
    list_paradigms,
    PARADIGMS,
)


class TestSubanta(unittest.TestCase):
    def test_paradigms_registered(self):
        # We now have 60+ paradigms registered
        self.assertGreaterEqual(len(PARADIGMS), 60)

    def test_go_declension(self):
        # Masculine bull
        g_m = decline("go", gender="m")["forms"]
        self.assertEqual(g_m["prathamA"], ["gOH", "gAvO", "gAvaH"])
        self.assertEqual(g_m["dvitIyA"], ["gAm", "gAvO", "gAH"])
        self.assertEqual(g_m["tftIyA"], ["gavA", "goByAm", "goBiH"])
        self.assertEqual(g_m["caturTI"], ["gave", "goByAm", "goByaH"])
        self.assertEqual(g_m["paYcamI"], ["goH", "goByAm", "goByaH"])
        self.assertEqual(g_m["zazWI"], ["goH", "gavoH", "gavAm"])
        self.assertEqual(g_m["saptamI"], ["gavi", "gavoH", "gozu"])
        self.assertEqual(g_m["saMboDana"], ["gOH", "gAvO", "gAvaH"])

        # Feminine cow
        g_f = decline("go", gender="f")["forms"]
        self.assertEqual(g_f["prathamA"], ["gOH", "gAvO", "gAvaH"])
        self.assertEqual(g_f["dvitIyA"], ["gAm", "gAvO", "gAH"])
        self.assertEqual(g_f["tftIyA"], ["gavA", "goByAm", "goBiH"])

    def test_numerals_genitive_plural(self):
        # Fixed replace bug where zazWI bahuvacana was hardcoded to paYcAnAm
        s7 = decline("sapta")["genders"]["m"]["zazWI"][2]
        self.assertEqual(s7, "saptAnAm")
        s9 = decline("nava")["genders"]["m"]["zazWI"][2]
        self.assertEqual(s9, "navAnAm")
        s10 = decline("daSa")["genders"]["m"]["zazWI"][2]
        self.assertEqual(s10, "daSAnAm")
        s11 = decline("ekAdaSa")["genders"]["m"]["zazWI"][2]
        self.assertEqual(s11, "ekAdaSAnAm")
        # azwan variants
        a8 = decline("azwan")["genders"]["m"]
        self.assertIn("azwO / azwa", a8["prathamA"][2])
        self.assertEqual(a8["zazWI"][2], "azwAnAm")

    def test_bhavat_and_at_m(self):
        # Honorific Bavat (BavAn)
        b_m = decline("Bavat", gender="m")["forms"]
        self.assertEqual(b_m["prathamA"][0], "BavAn")
        self.assertEqual(b_m["tftIyA"], ["BavatA", "BavadByAm", "BavadBiH"])
        self.assertEqual(b_m["caturTI"], ["Bavate", "BavadByAm", "BavadByaH"])
        self.assertEqual(b_m["paYcamI"], ["BavataH", "BavadByAm", "BavadByaH"])
        self.assertEqual(b_m["saptamI"], ["Bavati", "BavatoH", "Bavatsu"])

        # Participle Bavat (Bavan) via paradigm at_m
        p_m = decline("Bavat", paradigm="at_m")["forms"]
        self.assertEqual(p_m["prathamA"][0], "Bavan")
        self.assertEqual(p_m["tftIyA"], ["BavatA", "BavadByAm", "BavadBiH"])

    def test_pati_uncompounded_vs_compound(self):
        # Uncompounded pati is irregular
        pati = decline("pati", gender="m")["forms"]
        self.assertEqual(pati["tftIyA"][0], "patyA")
        self.assertEqual(pati["caturTI"][0], "patye")
        self.assertEqual(pati["paYcamI"][0], "patyuH")
        self.assertEqual(pati["zazWI"][0], "patyuH")
        self.assertEqual(pati["saptamI"][0], "patyO")

        # Compounds like BUpati decline like hari (Panini 1.4.8 patiḥ samāsa eva)
        bhupati = decline("BUpati", gender="m")["forms"]
        self.assertEqual(bhupati["tftIyA"][0], "BUpatinA")
        self.assertEqual(bhupati["caturTI"][0], "BUpataye")
        self.assertEqual(bhupati["paYcamI"][0], "BUpateH")
        self.assertEqual(bhupati["zazWI"][0], "BUpateH")
        self.assertEqual(bhupati["saptamI"][0], "BUpatO")

    def test_atman_vs_rajan(self):
        # Atman (conjunct - no elision of 'a')
        atman = decline("Atman", gender="m")["forms"]
        self.assertEqual(atman["prathamA"], ["AtmA", "AtmAnO", "AtmAnaH"])
        self.assertEqual(atman["dvitIyA"], ["AtmAnam", "AtmAnO", "AtmanaH"])
        self.assertEqual(atman["tftIyA"][0], "AtmanA")
        self.assertEqual(atman["caturTI"][0], "Atmane")
        self.assertEqual(atman["paYcamI"][0], "AtmanaH")
        self.assertEqual(atman["saptamI"][0], "Atmani")

        # rAjan (elision of 'a' and j+n -> jY)
        rajan = decline("rAjan", gender="m")["forms"]
        self.assertEqual(rajan["prathamA"], ["rAjA", "rAjAnO", "rAjAnaH"])
        self.assertEqual(rajan["dvitIyA"], ["rAjAnam", "rAjAnO", "rAjYaH"])
        self.assertEqual(rajan["tftIyA"][0], "rAjYA")
        self.assertEqual(rajan["caturTI"][0], "rAjYe")
        self.assertEqual(rajan["paYcamI"][0], "rAjYaH")

    def test_karman_vs_naman(self):
        # karman (conjunct with m: karma, karmaRI, karmARi, karmaRA)
        karman = decline("karman", gender="n")["forms"]
        self.assertEqual(karman["prathamA"][0], "karma")
        self.assertEqual(karman["tftIyA"][0], "karmaRA")
        self.assertEqual(karman["caturTI"][0], "karmaRe")
        self.assertEqual(karman["paYcamI"][0], "karmaRaH")

        # nAman (simple consonant: nAma, nAmnI/nAmanI, nAmAni, nAmnA)
        naman = decline("nAman", gender="n")["forms"]
        self.assertEqual(naman["prathamA"][0], "nAma")
        self.assertEqual(naman["tftIyA"][0], "nAmnA")
        self.assertEqual(naman["caturTI"][0], "nAmne")

    def test_kartf_agent_vs_pitf_kinship(self):
        # kartf (agent noun in -tf takes vṛddhi Ar)
        kartf = decline("kartf", gender="m")["forms"]
        self.assertEqual(kartf["prathamA"], ["kartA", "kartArO", "kartAraH"])
        self.assertEqual(kartf["dvitIyA"], ["kartAram", "kartArO", "kartFn"])
        self.assertEqual(kartf["tftIyA"][0], "kartrA")
        self.assertEqual(kartf["paYcamI"][0], "kartuH")
        self.assertEqual(kartf["zazWI"][2], "kartFRAm")
        self.assertEqual(kartf["saMboDana"], ["kartaH", "kartArO", "kartAraH"])

        # pitf (kinship noun takes guṇa ar)
        pitf = decline("pitf", gender="m")["forms"]
        self.assertEqual(pitf["prathamA"], ["pitA", "pitarO", "pitaraH"])
        self.assertEqual(pitf["dvitIyA"], ["pitaram", "pitarO", "pitFn"])
        self.assertEqual(pitf["saMboDana"], ["pitaH", "pitarO", "pitaraH"])

        # svasf (sister)
        svasf = decline("svasf", gender="f")["forms"]
        self.assertEqual(svasf["prathamA"], ["svasA", "svasArO", "svasAraH"])
        self.assertEqual(svasf["dvitIyA"], ["svasAram", "svasArO", "svasFH"])

    def test_asmad_and_yuzmad(self):
        asmad = decline("asmad")["forms"]
        self.assertEqual(asmad["prathamA"], ["aham", "AvAm", "vayam"])
        self.assertEqual(asmad["caturTI"][0], "mahyam / me")  # with 'h', not 'H' visarga
        self.assertEqual(asmad["paYcamI"][2], "asmat")  # asmat, not asmaByam
        self.assertEqual(asmad["tftIyA"], ["mayA", "AvAByAm", "asmABiH"])  # no fake enclitics

        yuzmad = decline("yuzmad")["forms"]
        self.assertEqual(yuzmad["prathamA"], ["tvam", "yuvAm", "yUyam"])
        self.assertEqual(yuzmad["caturTI"][0], "tuByam / te")
        self.assertEqual(yuzmad["paYcamI"][2], "yuzmat")  # yuzmat, not yuzmaByam
        self.assertEqual(yuzmad["tftIyA"], ["tvayA", "yuvAByAm", "yuzmABiH"])

    def test_sarva_and_anya(self):
        sarva_m = decline("sarva", gender="m")["forms"]
        self.assertEqual(sarva_m["saMboDana"][0], "sarva")  # he sarva, no visarga
        sarva_f = decline("sarva", gender="f")["forms"]
        self.assertEqual(sarva_f["saMboDana"][0], "sarve")  # he sarve

        # ḍatara/ḍatama neuter takes -at
        anya_n = decline("anya", gender="n")["forms"]
        self.assertEqual(anya_n["prathamA"][0], "anyat")
        self.assertEqual(anya_n["dvitIyA"][0], "anyat")

    def test_asthy_adi_irregular_neuters(self):
        # daDi, akzi, asTi, sakTi (Panini 7.1.75)
        dadhi = decline("daDi", gender="n")["forms"]
        self.assertEqual(dadhi["tftIyA"][0], "daDnA")
        self.assertEqual(dadhi["caturTI"][0], "daDne")
        self.assertEqual(dadhi["paYcamI"][0], "daDnaH")

        akzi = decline("akzi", gender="n")["forms"]
        self.assertEqual(akzi["tftIyA"][0], "akzRA")
        self.assertEqual(akzi["caturTI"][0], "akzRe")
        self.assertEqual(akzi["paYcamI"][0], "akzRaH")

    def test_special_halanta_paradigms(self):
        # ahan
        ahan = decline("ahan", gender="n")["forms"]
        self.assertEqual(ahan["prathamA"][0], "ahaH")
        self.assertEqual(ahan["tftIyA"][1], "ahoByAm")

        # pums
        pums = decline("pums", gender="m")["forms"]
        self.assertEqual(pums["prathamA"], ["pumAn", "pumAMsO", "pumAMsaH"])
        self.assertEqual(pums["dvitIyA"][2], "puMsaH")

        # Svan & yuvan (samprasāraṇa)
        svan = decline("Svan", gender="m")["forms"]
        self.assertEqual(svan["tftIyA"][0], "SunA")
        self.assertEqual(svan["caturTI"][0], "Sune")
        yuvan = decline("yuvan", gender="m")["forms"]
        self.assertEqual(yuvan["tftIyA"][0], "yUnA")
        self.assertEqual(yuvan["caturTI"][0], "yUne")

        # ap (water, plural only)
        ap = decline("ap", gender="f")["forms"]
        self.assertEqual(ap["prathamA"], ["-", "-", "ApaH"])
        self.assertEqual(ap["tftIyA"], ["-", "-", "adBiH"])

        # diS
        dis = decline("diS", gender="f")["forms"]
        self.assertEqual(dis["prathamA"], ["dik", "diSO", "diSaH"])
        self.assertEqual(dis["tftIyA"], ["diSA", "digByAm", "digBiH"])

    def test_vidvas_sreyas_mahat(self):
        vidvas = decline("vidvas", gender="m")["forms"]
        self.assertEqual(vidvas["prathamA"], ["vidvAn", "vidvAMsO", "vidvAMsaH"])
        self.assertEqual(vidvas["dvitIyA"][2], "viduzaH")
        self.assertEqual(vidvas["tftIyA"][0], "viduzA")

        sreyas = decline("Sreyas", gender="m")["forms"]
        self.assertEqual(sreyas["prathamA"], ["SreyAn", "SreyAMsO", "SreyAMsaH"])
        self.assertEqual(sreyas["dvitIyA"][0], "SreyAMsam")

        mahat_m = decline("mahat", gender="m")["forms"]
        self.assertEqual(mahat_m["prathamA"], ["mahAn", "mahAntO", "mahAntaH"])
        self.assertEqual(mahat_m["tftIyA"][1], "mahadByAm")

        mahat_n = decline("mahat", gender="n")["forms"]
        self.assertEqual(mahat_n["prathamA"], ["mahat", "mahatI", "mahAnti"])

    def test_root_vowels_and_diphthongs(self):
        # SrI
        sri = decline("SrI", gender="f")["forms"]
        self.assertEqual(sri["prathamA"][0], "SrIH")
        self.assertEqual(sri["prathamA"][1], "SriyO")

        # BU
        bhu = decline("BU", gender="f")["forms"]
        self.assertEqual(bhu["prathamA"][0], "BUH")
        self.assertEqual(bhu["prathamA"][1], "BuvO")

        # strI
        stri = decline("strI", gender="f")["forms"]
        self.assertEqual(stri["prathamA"][0], "strI")
        self.assertEqual(stri["tftIyA"][0], "striyA")

        # lakzmI
        lakzmi = decline("lakzmI", gender="f")["forms"]
        self.assertEqual(lakzmi["prathamA"][0], "lakzmIH")

        # nO & glO & rE
        nau = decline("nO", gender="f")["forms"]
        self.assertEqual(nau["prathamA"], ["nOH", "nAvO", "nAvaH"])
        self.assertEqual(nau["tftIyA"][1], "nOByAm")

        rai = decline("rE", gender="m")["forms"]
        self.assertEqual(rai["prathamA"], ["rAH", "rAyO", "rAyaH"])
        self.assertEqual(rai["tftIyA"][1], "rAByAm")

    def test_natva_rules(self):
        # rAma vs deva
        self.assertEqual(decline("rAma", gender="m")["forms"]["tftIyA"][0], "rAmeRa")
        self.assertEqual(decline("rAma", gender="m")["forms"]["zazWI"][2], "rAmARAm")
        self.assertEqual(decline("deva", gender="m")["forms"]["tftIyA"][0], "devena")
        self.assertEqual(decline("deva", gender="m")["forms"]["zazWI"][2], "devAnAm")

        # guru vs sADu
        self.assertEqual(decline("guru", gender="m")["forms"]["tftIyA"][0], "guruRA")
        self.assertEqual(decline("sADu", gender="m")["forms"]["tftIyA"][0], "sADunA")

        # vAri vs asthi
        self.assertEqual(decline("vAri", gender="n")["forms"]["tftIyA"][0], "vAriRA")

    def test_reverse_analysis(self):
        # Enclitic pronoun forms
        self.assertTrue(any(h["lemma"] == "asmad" for h in analyze_form("mAm")))
        self.assertTrue(any(h["lemma"] == "asmad" for h in analyze_form("mA")))
        self.assertTrue(any(h["lemma"] == "asmad" for h in analyze_form("me")))
        self.assertTrue(any(h["lemma"] == "yuzmad" for h in analyze_form("tvAm")))
        self.assertTrue(any(h["lemma"] == "yuzmad" for h in analyze_form("tvA")))

        # Zero-base irregulars
        self.assertTrue(any(h["lemma"] == "paTin" for h in analyze_form("panTAH")))
        self.assertTrue(any(h["lemma"] == "go" for h in analyze_form("gOH")))
        self.assertTrue(any(h["lemma"] == "go" for h in analyze_form("gavA")))
        self.assertTrue(any(h["lemma"] == "ahan" for h in analyze_form("ahaH")))
        self.assertTrue(any(h["lemma"] == "pums" for h in analyze_form("pumAn")))
        self.assertTrue(any(h["lemma"] == "vidvas" for h in analyze_form("vidvAn")))


if __name__ == "__main__":
    unittest.main()
