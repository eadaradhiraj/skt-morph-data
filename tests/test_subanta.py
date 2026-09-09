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

    def test_anaquh_paradigm(self):
        forms = decline("anaquh", gender="m")["forms"]
        self.assertEqual(forms["prathamA"], ["anaqvAn", "anaqvAhO", "anaqvAhaH"])
        self.assertEqual(forms["dvitIyA"], ["anaqvAham", "anaqvAhO", "anaquhaH"])
        self.assertEqual(forms["tftIyA"][0], "anaquhA")
        self.assertEqual(forms["tftIyA"][1], "anaqudByAm")
        self.assertEqual(forms["tftIyA"][2], "anaqudBiH")
        self.assertIn("anaqutsu", forms["saptamI"][2])
        self.assertEqual(forms["saMboDana"][0], "anaqvan")
        self.assertTrue(any(h["lemma"] == "anaquh" for h in analyze_form("anaqvAn")))

    def test_root_a_masculine(self):
        forms = decline("viSvapA", gender="m")["forms"]
        self.assertEqual(forms["prathamA"], ["viSvapAH", "viSvapO", "viSvapAH"])
        self.assertEqual(forms["dvitIyA"], ["viSvapAm", "viSvapO", "viSvapaH"])
        self.assertEqual(forms["tftIyA"][0], "viSvapA")
        self.assertEqual(forms["tftIyA"][1], "viSvapAByAm")
        self.assertEqual(forms["caturTI"][0], "viSvape")
        self.assertEqual(forms["saptamI"][0], "viSvapi")
        self.assertEqual(forms["saptamI"][2], "viSvapAsu")
        self.assertTrue(any(h["lemma"] == "viSvapA" for h in analyze_form("viSvapAH")))

    def test_root_i_masculine_sudhi_and_senani(self):
        # suDI: iyaN-AdeSa
        sudhi = decline("suDI", gender="m")["forms"]
        self.assertEqual(sudhi["prathamA"], ["suDIH", "suDiyO", "suDiyaH"])
        self.assertEqual(sudhi["dvitIyA"], ["suDiyam", "suDiyO", "suDiyaH"])
        self.assertEqual(sudhi["tftIyA"][0], "suDiyA")
        self.assertEqual(sudhi["tftIyA"][1], "suDIByAm")
        self.assertEqual(sudhi["saptamI"][2], "suDIzu")
        self.assertTrue(any(h["lemma"] == "suDI" for h in analyze_form("suDIH")))

        # senAnI: yaR-AdeSa
        senani = decline("senAnI", gender="m")["forms"]
        self.assertEqual(senani["prathamA"], ["senAnIH", "senAnyO", "senAnyaH"])
        self.assertEqual(senani["dvitIyA"], ["senAnyam", "senAnyO", "senAnyaH"])
        self.assertEqual(senani["tftIyA"][0], "senAnyA")
        self.assertEqual(senani["tftIyA"][1], "senAnIByAm")
        self.assertEqual(senani["saptamI"][2], "senAnIzu")
        self.assertTrue(any(h["lemma"] == "senAnI" for h in analyze_form("senAnIH")))

    def test_r_stems_gir_pur_dvar(self):
        # gir
        gir = decline("gir", gender="f")["forms"]
        self.assertEqual(gir["prathamA"], ["gIH", "girO", "giraH"])
        self.assertEqual(gir["dvitIyA"][0], "giram")
        self.assertEqual(gir["tftIyA"], ["girA", "gIrByAm", "gIrBiH"])
        self.assertEqual(gir["saptamI"][2], "gIrzu")
        self.assertTrue(any(h["lemma"] == "gir" for h in analyze_form("gIH")))

        # pur
        pur = decline("pur", gender="f")["forms"]
        self.assertEqual(pur["prathamA"], ["pUH", "purO", "puraH"])
        self.assertEqual(pur["tftIyA"], ["purA", "pUrByAm", "pUrBiH"])
        self.assertEqual(pur["saptamI"][2], "pUrzu")
        self.assertTrue(any(h["lemma"] == "pur" for h in analyze_form("pUH")))

        # dvAr
        dvar = decline("dvAr", gender="f")["forms"]
        self.assertEqual(dvar["prathamA"], ["dvAH", "dvArO", "dvAraH"])
        self.assertEqual(dvar["tftIyA"], ["dvArA", "dvArByAm", "dvArBiH"])
        self.assertEqual(dvar["saptamI"][2], "dvArzu")
        self.assertTrue(any(h["lemma"] == "dvAr" for h in analyze_form("dvAH")))

    def test_div_and_dyu(self):
        div_f = decline("div", gender="f")["forms"]
        self.assertEqual(div_f["prathamA"], ["dyOH", "divO", "divaH"])
        self.assertEqual(div_f["dvitIyA"], ["divam", "divO", "divaH"])
        self.assertEqual(div_f["tftIyA"], ["divA", "dyuByAm", "dyuBiH"])
        self.assertEqual(div_f["caturTI"][0], "dive")
        self.assertEqual(div_f["saptamI"], ["divi", "divoH", "dyuzu"])
        self.assertEqual(div_f["saMboDana"][0], "dyOH")

        dyu = decline("dyu", gender="f")["forms"]
        self.assertEqual(dyu["prathamA"][0], "dyOH")
        self.assertEqual(dyu["tftIyA"][1], "dyuByAm")
        self.assertTrue(any(h["lemma"] == "div" for h in analyze_form("dyOH")))

    def test_directional_anc_stems(self):
        pranc = decline("prAYc", gender="m")["forms"]
        self.assertEqual(pranc["prathamA"], ["prAN", "prAYcO", "prAYcaH"])
        self.assertEqual(pranc["dvitIyA"], ["prAYcam", "prAYcO", "prAcaH"])
        self.assertEqual(pranc["tftIyA"], ["prAcA", "prAgByAm", "prAgBiH"])
        self.assertEqual(pranc["saptamI"][2], "prAkzu")
        self.assertTrue(any(h["lemma"] == "prAYc" for h in analyze_form("prAN")))

        pratyanc = decline("pratyaYc", gender="m")["forms"]
        self.assertEqual(pratyanc["prathamA"], ["pratyaN", "pratyaYcO", "pratyaYcaH"])
        self.assertEqual(pratyanc["dvitIyA"], ["pratyaYcam", "pratyaYcO", "pratIcaH"])
        self.assertEqual(pratyanc["tftIyA"], ["pratIcA", "pratyagByAm", "pratyagBiH"])
        self.assertEqual(pratyanc["saptamI"][2], "pratyakzu")
        self.assertTrue(any(h["lemma"] == "pratyaYc" for h in analyze_form("pratyaN")))

        udanc = decline("udaYc", gender="m")["forms"]
        self.assertEqual(udanc["prathamA"], ["udaN", "udaYcO", "udaYcaH"])
        self.assertEqual(udanc["dvitIyA"], ["udaYcam", "udaYcO", "udIcaH"])
        self.assertEqual(udanc["tftIyA"], ["udIcA", "udagByAm", "udagBiH"])
        self.assertEqual(udanc["saptamI"][2], "udakzu")
        self.assertTrue(any(h["lemma"] == "udaYc" for h in analyze_form("udaN")))

    def test_krozwu_paradigm(self):
        kroztu = decline("krozwu", gender="m")["forms"]
        self.assertEqual(kroztu["prathamA"], ["krozwA", "krozwArO", "krozwAraH"])
        self.assertEqual(kroztu["dvitIyA"], ["krozwAram", "krozwArO", "krozwUn"])
        self.assertIn("krozwrA", kroztu["tftIyA"][0])
        self.assertEqual(kroztu["tftIyA"][1], "krozwuByAm")
        self.assertIn("krozwre", kroztu["caturTI"][0])
        self.assertIn("krozwari", kroztu["saptamI"][0])
        self.assertEqual(kroztu["saptamI"][2], "krozwuzu")
        self.assertEqual(kroztu["saMboDana"][0], "krozwo")
        self.assertTrue(any(h["lemma"] == "krozwu" for h in analyze_form("krozwA")))

    def test_candramas_paradigm(self):
        candramas = decline("candramas", gender="m")["forms"]
        self.assertEqual(candramas["prathamA"], ["candramAH", "candramasO", "candramasaH"])
        self.assertEqual(candramas["dvitIyA"], ["candramasam", "candramasO", "candramasaH"])
        self.assertEqual(candramas["tftIyA"], ["candramasA", "candramoByAm", "candramoBiH"])
        self.assertEqual(candramas["saptamI"][0], "candramasi")
        self.assertIn("candramaHsu", candramas["saptamI"][2])
        self.assertEqual(candramas["saMboDana"][0], "candramaH")
        self.assertTrue(any(h["lemma"] == "candramas" for h in analyze_form("candramAH")))

    def test_yuj_paradigm(self):
        yuj = decline("yuj", gender="m")["forms"]
        self.assertEqual(yuj["prathamA"], ["yuN", "yuYjO", "yuYjaH"])
        self.assertEqual(yuj["dvitIyA"], ["yuYjam", "yuYjO", "yujaH"])
        self.assertEqual(yuj["tftIyA"], ["yujA", "yugByAm", "yugBiH"])
        self.assertEqual(yuj["saptamI"], ["yuji", "yujoH", "yukzu"])
        self.assertEqual(yuj["saMboDana"], ["yuN", "yuYjO", "yuYjaH"])
        self.assertTrue(any(h["lemma"] == "yuj" for h in analyze_form("yuN")))

    def test_bhuj_and_j_stem(self):
        # Bizaj (verifying gByAm fix)
        bhishaj = decline("Bizaj", gender="m")["forms"]
        self.assertEqual(bhishaj["tftIyA"][1], "BizagByAm")

        # Buj
        bhuj = decline("Buj", gender="m")["forms"]
        self.assertEqual(bhuj["prathamA"], ["Buk", "BujO", "BujaH"])
        self.assertEqual(bhuj["dvitIyA"], ["Bujam", "BujO", "BujaH"])
        self.assertEqual(bhuj["tftIyA"], ["BujA", "BugByAm", "BugBiH"])
        self.assertEqual(bhuj["saptamI"], ["Buji", "BujoH", "Bukzu"])
        self.assertTrue(any(h["lemma"] == "Buj" for h in analyze_form("Buk")))

    def test_kzuD_and_dh_stems(self):
        # kzuD
        kzhudh = decline("kzuD", gender="f")["forms"]
        self.assertIn("kzut", kzhudh["prathamA"][0])
        self.assertEqual(kzhudh["prathamA"][1], "kzuDO")
        self.assertEqual(kzhudh["tftIyA"], ["kzuDA", "kzudByAm", "kzudBiH"])
        self.assertEqual(kzhudh["saptamI"], ["kzuDi", "kzuDoH", "kzutsu"])
        self.assertTrue(any(h["lemma"] == "kzuD" for h in analyze_form("kzut")))

        # samiD
        samidh = decline("samiD", gender="f")["forms"]
        self.assertEqual(samidh["prathamA"][1], "samiDO")
        self.assertEqual(samidh["tftIyA"][1], "samidByAm")
        self.assertEqual(samidh["saptamI"][2], "samitsu")

    def test_vftrahan_and_maghavan(self):
        # vftrahan
        vritrahan = decline("vftrahan", gender="m")["forms"]
        self.assertEqual(vritrahan["prathamA"], ["vftrahA", "vftrahaRO", "vftrahaRaH"])
        self.assertEqual(vritrahan["dvitIyA"][0], "vftrahaRam")
        self.assertIn("vftraGRaH", vritrahan["dvitIyA"][2])
        self.assertEqual(vritrahan["tftIyA"][1], "vftrahaByAm")
        self.assertEqual(vritrahan["saptamI"][2], "vftrahasu")
        self.assertEqual(vritrahan["saMboDana"][0], "vftrahan")
        self.assertTrue(any(h["lemma"] == "vftrahan" for h in analyze_form("vftrahA")))

        # Satruhan
        satruhan = decline("Satruhan", gender="m")["forms"]
        self.assertEqual(satruhan["prathamA"][0], "SatruhA")
        self.assertEqual(satruhan["tftIyA"][1], "SatruhaByAm")

        # maGavan
        maghavan = decline("maGavan", gender="m")["forms"]
        self.assertEqual(maghavan["prathamA"], ["maGavAn", "maGavAntO", "maGavAntaH"])
        self.assertEqual(maghavan["dvitIyA"], ["maGavAntam", "maGavAntO", "maGonaH"])
        self.assertEqual(maghavan["tftIyA"], ["maGonA", "maGavadByAm", "maGavadBiH"])
        self.assertEqual(maghavan["caturTI"][0], "maGone")
        self.assertEqual(maghavan["saptamI"], ["maGoni", "maGonoH", "maGavatsu"])
        self.assertEqual(maghavan["saMboDana"][0], "maGavan")
        self.assertTrue(any(h["lemma"] == "maGavan" for h in analyze_form("maGavAn")))

    def test_purvadi_pronouns(self):
        # Panini 1.1.32 vibhāṣā jasi, 1.1.34-36 pūrvaparāvara...
        p_m = decline("pUrva", category="pronoun", gender="m")["forms"]
        # Nom.pl has both pronoun -e and nominal -AH
        self.assertEqual(p_m["prathamA"][2], "pUrve / pUrvAH")
        self.assertEqual(p_m["saMboDana"][2], "pUrve / pUrvAH")
        # Abl.sg has asmAt and At
        self.assertEqual(p_m["paYcamI"][0], "pUrvasmAt / pUrvAt")
        # Loc.sg has asmin and e
        self.assertEqual(p_m["saptamI"][0], "pUrvasmin / pUrvAt".replace("At", "e"))
        # Natva applied properly in gen.pl and loc.pl
        self.assertEqual(p_m["zazWI"][2], "pUrvezAm")
        self.assertEqual(p_m["saptamI"][2], "pUrvezu")

        # Feminine optional forms (1.1.34-36)
        p_f = decline("pUrva", category="pronoun", gender="f")["forms"]
        self.assertEqual(p_f["caturTI"][0], "pUrvasyE / pUrvAyE")
        self.assertEqual(p_f["paYcamI"][0], "pUrvasyAH / pUrvAyAH")
        self.assertEqual(p_f["zazWI"][0], "pUrvasyAH / pUrvAyAH")
        self.assertEqual(p_f["saptamI"][0], "pUrvasyAm / pUrvAyAm")

        # Reverse analysis finds pUrva for both variants
        hits_pe = analyze_form("pUrve")
        self.assertTrue(any(h["lemma"] == "pUrva" for h in hits_pe))
        hits_pah = analyze_form("pUrvAH")
        self.assertTrue(any(h["lemma"] == "pUrva" for h in hits_pah))
        hits_psmat = analyze_form("pUrvasmAt")
        self.assertTrue(any(h["lemma"] == "pUrva" for h in hits_psmat))
        hits_pat = analyze_form("pUrvAt")
        self.assertTrue(any(h["lemma"] == "pUrva" for h in hits_pat))

    def test_formatters(self):
        from skt_morph_data.subanta import (
            to_markdown,
            to_html,
            to_csv,
            to_latex,
            to_anki,
            format_declension,
        )
        res = decline("rAma", gender="m")
        # Markdown
        md = to_markdown(res)
        self.assertIn("| vibhakti | ekavacana | dvivacana | bahuvacana |", md)
        self.assertIn("| prathamA | rAmaH | rAmO | rAmAH |", md)

        # HTML
        html_out = to_html(res)
        self.assertIn('<table class="subanta-table">', html_out)
        self.assertIn("<td>prathamA</td><td>rAmaH</td>", html_out)

        # CSV
        csv_out = to_csv(res)
        self.assertIn("vibhakti,ekavacana,dvivacana,bahuvacana", csv_out)
        self.assertIn("prathamA,rAmaH,rAmO,rAmAH", csv_out)

        # LaTeX
        latex_out = to_latex(res)
        self.assertIn("\\begin{tabular}{|l|l|l|l|}", latex_out)
        self.assertIn("prathamA & rAmaH & rAmO & rAmAH \\\\", latex_out)

        # Anki
        anki_out = to_anki(res)
        self.assertIn("rAma [m] - prathamA ekavacana\trAmaH\tsubanta:a_m", anki_out)

        # format_declension dispatcher
        self.assertEqual(format_declension(res, "markdown"), md)
        self.assertEqual(format_declension(res, "csv"), csv_out)
        self.assertEqual(format_declension(res, "latex"), latex_out)
        self.assertEqual(format_declension(res, "anki"), anki_out)
        self.assertEqual(format_declension(res, "html"), html_out)

        # Multi-gender format
        tad_res = decline("tad")
        self.assertIn("gender: m", to_markdown(tad_res))
        self.assertIn("gender: f", to_markdown(tad_res))
        self.assertIn("gender,vibhakti,ekavacana,dvivacana,bahuvacana", to_csv(tad_res))

        # Avyaya format
        avyaya_res = {"dhatu": "BU", "pratyaya": "ktvA", "is_avyaya": True, "form": "BUtvA"}
        self.assertIn("BUtvA", to_markdown(avyaya_res))
        self.assertIn("BUtvA", to_html(avyaya_res))
        self.assertIn("BUtvA", to_csv(avyaya_res))
        self.assertIn("BUtvA", to_anki(avyaya_res))


if __name__ == "__main__":
    unittest.main()

