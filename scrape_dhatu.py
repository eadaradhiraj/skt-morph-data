"""Scrape dhatu data from ashtadhyayi.com using Selenium."""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

import certifi
from typing import Any

from indic_transliteration import sanscript
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.remote.webdriver import WebDriver

SCRIPT_DIR = Path(__file__).resolve().parent
LOCAL_CHROMEDRIVER = SCRIPT_DIR / "chromedriver.exe"

BASE_URL = "https://ashtadhyayi.com/dhatu"
DHATU_LIST_URL = (
    "https://raw.githubusercontent.com/ashtadhyayi-com/data/master/dhatu/data.txt"
)
LOAD_WAIT_SECONDS = 30
FORM_LOAD_TIMEOUT_SECONDS = 240
PAGE_WAIT_SECONDS = 5
DEFAULT_PROGRESS_FILE = "completed.txt"
DEFAULT_FAILED_FILE = "failed.txt"
DEFAULT_IDS_FILE = "dhatu_ids.txt"

CONJUGATION_TABS = [
    "ting",
    "yak",
    "san",
    "san_yak",
    "nich",
    "nich_yak",
    "yang",
    "yang_yak",
    "yangluk",
    "yangluk_yak",
]

PARTICIPLE_TABS = [
    "krut",
    "san_krut",
    "nich_krut",
    "yang_krut",
    "yangluk_krut",
]

HTML_TAG_RE = re.compile(r"<[^>]+>")
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
DHATU_ID_RE = re.compile(r"^\d{2}\.\d{4}$")


class ScrapeSession:
    """Tracks whether the ashtadhyayi SPA has finished its initial load."""

    def __init__(self) -> None:
        self.app_loaded = False


def gana_folder(dhatu_id: str) -> str:
    return dhatu_id.split(".")[0]


def dhatu_output_path(output_dir: Path, dhatu_id: str) -> Path:
    return output_dir / gana_folder(dhatu_id) / f"{dhatu_id}.json"


def load_id_set(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def append_id(path: Path, dhatu_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{dhatu_id}\n")
        f.flush()
        os.fsync(f.fileno())


def fetch_dhatu_ids_from_github() -> list[str]:
    """Load all dhatu ids from the public ashtadhyayi-com/data repo (no browser)."""
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(DHATU_LIST_URL, timeout=120, context=context) as response:
        payload = json.load(response)
    ids = sorted(
        row["baseindex"]
        for row in payload.get("data", [])
        if isinstance(row, dict) and row.get("baseindex")
    )
    if not ids:
        raise RuntimeError("Could not read dhatu list from GitHub data repo")
    return ids


def fetch_all_dhatu_ids(
    driver: WebDriver | None = None,
    session: ScrapeSession | None = None,
) -> list[str]:
    """Return sorted dhatu ids. Prefer GitHub to avoid loading ~300MB in the browser."""
    try:
        return fetch_dhatu_ids_from_github()
    except Exception as github_error:
        if driver is None or session is None:
            raise RuntimeError(
                "Could not fetch dhatu ids from GitHub and no browser session is available"
            ) from github_error
        ensure_app_loaded(driver, session, bootstrap_id="01.0001", require_forms=False)
        ids = driver.execute_script(
            """
            return Dhatu.dhatuList
                .map(d => d.baseindex)
                .filter(Boolean)
                .sort();
            """
        )
        if not ids:
            raise RuntimeError("Could not read dhatu list from site") from github_error
        return ids


def ensure_app_loaded(
    driver: WebDriver,
    session: ScrapeSession,
    bootstrap_id: str = "01.0001",
    require_forms: bool = False,
) -> None:
    if session.app_loaded and not require_forms:
        return
    driver.get(f"{BASE_URL}/{bootstrap_id}?tab=info")
    deadline = time.time() + FORM_LOAD_TIMEOUT_SECONDS
    while time.time() < deadline:
        ready = driver.execute_script(
            """
            return typeof Dhatu !== 'undefined'
                && Dhatu.initDone
                && Dhatu.dhatuList
                && Dhatu.dhatuList.length > 0
                && (arguments[0] ? !!Dhatu.allDhatuforms : true);
            """,
            require_forms,
        )
        if ready:
            session.app_loaded = True
            return
        time.sleep(2)
    raise RuntimeError("Ashtadhyayi app did not finish loading")


class NoFormsAvailable(Exception):
    """Raised when a list entry exists but has no conjugation data (e.g. ganasutra)."""

    def __init__(self, dhatu_id: str, reason: str = "no_forms", label: str = ""):
        self.dhatu_id = dhatu_id
        self.reason = reason
        self.label = label
        super().__init__(f"{dhatu_id}: {reason}" + (f" ({label})" if label else ""))


def wait_for_dhatu(driver: WebDriver, dhatu_id: str, session: ScrapeSession) -> None:
    ensure_app_loaded(driver, session, bootstrap_id=dhatu_id, require_forms=False)
    driver.get(f"{BASE_URL}/{dhatu_id}?tab=info")
    deadline = time.time() + FORM_LOAD_TIMEOUT_SECONDS
    while time.time() < deadline:
        status = driver.execute_script(
            """
            const id = arguments[0];
            const entry = (Dhatu.dhatuList || []).find(d => d.baseindex === id);
            const formsReady = !!(Dhatu.allDhatuforms
                && Object.keys(Dhatu.allDhatuforms).length > 1000);
            const hasForms = !!(Dhatu.allDhatuforms && Dhatu.allDhatuforms[id]);
            const tags = entry && entry.tags ? entry.tags : [];
            return {
                initDone: !!Dhatu.initDone,
                entryFound: !!entry,
                formsReady,
                hasForms,
                isGanasutra: tags.includes('ganasutra'),
                label: entry ? (entry.dhatu || '') : '',
            };
            """,
            dhatu_id,
        )
        if status.get("hasForms"):
            session.app_loaded = True
            return
        # Forms catalog is loaded, but this id has none (ganasutra / meta entry)
        if status.get("formsReady") and status.get("entryFound") and not status.get("hasForms"):
            reason = "ganasutra" if status.get("isGanasutra") else "no_forms"
            raise NoFormsAvailable(dhatu_id, reason=reason, label=status.get("label", ""))
        time.sleep(2)
    raise RuntimeError(f"Dhatu data not available for {dhatu_id}")


def stub_no_forms_payload(dhatu_id: str, reason: str, label: str = "") -> dict[str, Any]:
    return {
        "id": dhatu_id,
        "skipped": True,
        "skip_reason": reason,
        "label": to_slp1(label) if label else "",
        "info": [],
        "conjugations": {},
        "participles": {},
        "upasarga": {"dhatu": "", "entries": []},
        "chandrika": [],
        "prayoga": [],
        "upasarga_forms": {},
    }


def contains_devanagari(text: str) -> bool:
    return bool(text and DEVANAGARI_RE.search(text))


def to_slp1(text: str) -> str:
    if not text or not text.strip():
        return text
    return sanscript.transliterate(text.strip(), sanscript.DEVANAGARI, sanscript.SLP1)


def slp1_or_plain(text: str) -> str:
    """Transliterate Devanagari to SLP1; leave Latin/English text unchanged."""
    if not text:
        return text
    cleaned = strip_html(text)
    if contains_devanagari(cleaned):
        return to_slp1(cleaned)
    return cleaned


def slp1_url(url: str) -> str:
    if not url or not contains_devanagari(url):
        return url
    return DEVANAGARI_RE.sub(lambda m: to_slp1(m.group(0)), url)


def to_slp1_list(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part:
                result.append(to_slp1(part))
    return result


def slp1_variant_field(value: str) -> str:
    """Transliterate one participle field; preserve / between variants."""
    if not value or not value.strip():
        return ""
    parts = []
    for piece in value.split("/"):
        piece = piece.strip()
        if not piece:
            continue
        parts.append(to_slp1(piece) if contains_devanagari(piece) else piece)
    return "/".join(parts)


def parse_participle_row(csv_row: str) -> dict[str, str]:
    """
    Parse one krdanta row from site data.

    Site format is comma-separated: base, masculine, feminine, neuter.
    Empty fields are allowed. Slashes inside a field mean alternate forms.
    """
    fields = [field.strip() for field in csv_row.split(",")]
    while len(fields) < 4:
        fields.append("")
    base, masculine, feminine, neuter = fields[:4]
    entry = {
        "base": slp1_variant_field(base),
        "m": slp1_variant_field(masculine),
        "f": slp1_variant_field(feminine),
        "n": slp1_variant_field(neuter),
    }
    return entry


def convert_participle_map(raw: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    converted: dict[str, list[dict[str, str]]] = {}
    for key, rows in raw.items():
        if not isinstance(rows, list):
            continue
        entries = [
            parse_participle_row(row)
            for row in rows
            if isinstance(row, str) and row.strip()
        ]
        if entries:
            converted[to_slp1(key)] = entries
    return converted


def strip_html(text: str) -> str:
    return HTML_TAG_RE.sub("", text or "").strip()


def _chrome_binary_candidates() -> list[str]:
    local = os.environ.get("LOCALAPPDATA", "")
    return [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(local, r"Google\Chrome\Application\chrome.exe"),
    ]


def _apply_common_options(options: ChromeOptions, headless: bool) -> None:
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-background-networking")
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.add_experimental_option(
        "prefs", {"profile.default_content_setting_values.notifications": 2}
    )


def create_driver(headless: bool = True) -> WebDriver:
    """Create a silent headless Chrome session using local chromedriver.exe."""
    if not LOCAL_CHROMEDRIVER.is_file():
        raise FileNotFoundError(f"chromedriver.exe not found at {LOCAL_CHROMEDRIVER}")

    chrome_bin = next((p for p in _chrome_binary_candidates() if os.path.isfile(p)), None)
    if not chrome_bin:
        raise FileNotFoundError(
            "Google Chrome browser binary not found. "
            "Please install Chrome to use this scraper."
        )

    options = ChromeOptions()
    _apply_common_options(options, headless)
    options.binary_location = chrome_bin
    service = ChromeService(str(LOCAL_CHROMEDRIVER), log_output=os.devnull)
    return webdriver.Chrome(service=service, options=options)


def wait_for_dhatu_app(driver: WebDriver, dhatu_id: str) -> None:
    wait_for_dhatu(driver, dhatu_id, ScrapeSession())


def js_get_entry(driver: WebDriver, dhatu_id: str) -> dict[str, Any]:
    entry = driver.execute_script(
        """
        return Dhatu.dhatuList.find(d => d.baseindex === arguments[0]);
        """,
        dhatu_id,
    )
    if not entry:
        raise RuntimeError(f"Dhatu entry not found: {dhatu_id}")
    return entry


def js_get_info(driver: WebDriver, entry: dict[str, Any]) -> list[dict[str, Any]]:
    return driver.execute_script("return Dhatu.getInfoData(arguments[0]);", entry)


def js_get_upasarga_tab(driver: WebDriver, entry: dict[str, Any]) -> dict[str, Any]:
    return driver.execute_script("return Dhatu.getUpasargaData(arguments[0]);", entry)


def js_get_chandrika_raw(driver: WebDriver, dhatu_id: str) -> list[dict[str, Any]]:
    return driver.execute_script(
        """
        return Dhatu.upasargarthaChandrikaData[arguments[0]] || [];
        """,
        dhatu_id,
    )


def name_to_prefix_code(name: str) -> str:
    """Convert upasarga label (Devanagari or SLP1, with + or spaces) to URL code."""
    parts = [p.strip() for p in name.replace("+", " ").split() if p.strip()]
    codes = [to_slp1(p) if contains_devanagari(p) else p for p in parts]
    return ";".join(c for c in codes if c)


def collect_upasarga_prefixes(
    upasarga_tab: dict[str, Any],
    chandrika_raw: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Gather unique prefixes from upasarga tab and chandrika; skip duplicates."""
    seen_codes: set[str] = set()
    prefixes: list[dict[str, Any]] = []

    def add(name: str, artha_hindi: str = "") -> None:
        code = name_to_prefix_code(name)
        if not code or code in seen_codes:
            return
        seen_codes.add(code)
        prefixes.append(
            {
                "prefix": code,
                "artha_hindi": artha_hindi,
            }
        )

    # Upasarga tab first (includes meanings)
    for item in upasarga_tab.get("data", []):
        add(item.get("name", ""), item.get("artha_hindi", ""))

    # Chandrika tab (examples-only prefixes; skip if already seen)
    for item in chandrika_raw:
        add(item.get("upasarga", ""))

    return prefixes


def js_get_prayoga(driver: WebDriver, dhatu_id: str) -> list[dict[str, Any]]:
    return driver.execute_script(
        "return Dhatu.getTingPrayogaData(arguments[0]);", dhatu_id
    )


def js_get_forms(
    driver: WebDriver, entry: dict[str, Any], tab: str, upasarga_code: str = ""
) -> dict[str, Any]:
    url = f"{BASE_URL}/{entry['baseindex']}?tab={tab}"
    if upasarga_code:
        url += f"&upasarga={upasarga_code}"
    driver.get(url)
    time.sleep(8)
    return driver.execute_script(
        """
        const entry = arguments[0];
        const tab = arguments[1];
        return Dhatu.getCorrectDhatuForms(entry, tab)[tab] || {};
        """,
        entry,
        tab,
    )


def convert_form_map(raw: dict[str, Any]) -> dict[str, list[str]]:
    converted: dict[str, list[str]] = {}
    for key, values in raw.items():
        if not isinstance(values, list):
            continue
        converted[to_slp1(key)] = to_slp1_list(values)
    return converted


def scrape_form_sets(
    driver: WebDriver,
    entry: dict[str, Any],
    upasarga_code: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    conjugations: dict[str, Any] = {}
    participles: dict[str, Any] = {}

    for tab in CONJUGATION_TABS:
        raw = js_get_forms(driver, entry, tab, upasarga_code)
        if raw:
            conjugations[tab] = convert_form_map(raw)

    for tab in PARTICIPLE_TABS:
        raw = js_get_forms(driver, entry, tab, upasarga_code)
        if raw:
            participles[tab] = convert_participle_map(raw)

    return conjugations, participles


def normalize_info(info_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for row in info_rows:
        name = row.get("name", "")
        value = row.get("value", "")
        item = {
            "name": slp1_or_plain(name) if name != "English Meaning" else name,
            "value": value if name == "English Meaning" else slp1_or_plain(value),
        }
        if row.get("note"):
            item["note"] = slp1_or_plain(row["note"])
        if row.get("extLink"):
            item["ext_link"] = slp1_url(row["extLink"])
        normalized.append(item)
    return normalized


def normalize_upasarga_tab(data: dict[str, Any]) -> dict[str, Any]:
    seen: set[str] = set()
    entries = []
    for item in data.get("data", []):
        prefix = name_to_prefix_code(item.get("name", ""))
        if not prefix or prefix in seen:
            continue
        seen.add(prefix)
        entries.append(
            {
                "prefix": prefix,
                "artha_hindi": slp1_or_plain(item.get("artha_hindi", "")),
            }
        )
    return {"dhatu": to_slp1(data.get("dhatu", "")), "entries": entries}


def normalize_chandrika_tab(chandrika_raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    results = []
    for item in chandrika_raw:
        prefix = name_to_prefix_code(item.get("upasarga", ""))
        if not prefix or prefix in seen:
            continue
        seen.add(prefix)
        results.append(
            {
                "prefix": prefix,
                "examples": [
                    slp1_or_plain(ex) if isinstance(ex, str) else slp1_or_plain(ex.get("example", ""))
                    for ex in item.get("examples", [])
                ],
            }
        )
    return results


def normalize_prayoga(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        examples = []
        for ex in row.get("data", []):
            examples.append(
                {
                    "book": slp1_or_plain(ex.get("book", "")),
                    "reference": slp1_or_plain(ex.get("num", "")),
                    "text": slp1_or_plain(ex.get("text", "")),
                    "external": ex.get("external", ""),
                }
            )
        normalized.append(
            {
                "form": to_slp1(row.get("form", "")),
                "lakaar": slp1_or_plain(row.get("lakaar", "")),
                "purusha": slp1_or_plain(row.get("purusha", "")),
                "vachana": slp1_or_plain(row.get("vachana", "")),
                "examples": examples,
            }
        )
    return normalized


def scrape_dhatu(
    driver: WebDriver,
    dhatu_id: str,
    session: ScrapeSession | None = None,
) -> dict[str, Any]:
    scrape_session = session or ScrapeSession()
    try:
        wait_for_dhatu(driver, dhatu_id, scrape_session)
    except NoFormsAvailable as exc:
        return stub_no_forms_payload(exc.dhatu_id, exc.reason, exc.label)

    entry = js_get_entry(driver, dhatu_id)

    info = normalize_info(js_get_info(driver, entry))
    upasarga_tab_raw = js_get_upasarga_tab(driver, entry)
    chandrika_raw = js_get_chandrika_raw(driver, dhatu_id)
    upasarga_tab = normalize_upasarga_tab(upasarga_tab_raw)
    chandrika = normalize_chandrika_tab(chandrika_raw)
    prayoga = normalize_prayoga(js_get_prayoga(driver, dhatu_id))

    conjugations, participles = scrape_form_sets(driver, entry)

    upasarga_forms: dict[str, Any] = {}
    for prefix_info in collect_upasarga_prefixes(upasarga_tab_raw, chandrika_raw):
        code = prefix_info["prefix"]
        up_conj, up_part = scrape_form_sets(driver, entry, code)
        upasarga_forms[code] = {
            "prefix": code,
            "artha_hindi": slp1_or_plain(prefix_info.get("artha_hindi", "")),
            "conjugations": up_conj,
            "participles": up_part,
        }

    return {
        "id": dhatu_id,
        "info": info,
        "conjugations": conjugations,
        "participles": participles,
        "upasarga": upasarga_tab,
        "chandrika": chandrika,
        "prayoga": prayoga,
        "upasarga_forms": upasarga_forms,
    }


def save_dhatu_json(data: dict[str, Any], output_dir: Path) -> Path:
    out_path = dhatu_output_path(output_dir, data["id"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    tmp_path.replace(out_path)
    return out_path


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Scrape ashtadhyayi.com dhatu data")
    parser.add_argument("dhatu_id", help="Dhatu id, e.g. 06.0147")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="output",
        help="Directory for JSON output (default: output)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with UI visible",
    )
    args = parser.parse_args()

    driver = create_driver(headless=not args.no_headless)
    try:
        data = scrape_dhatu(driver, args.dhatu_id)
        out_path = save_dhatu_json(data, Path(args.output_dir))
        print(f"Saved {out_path}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
