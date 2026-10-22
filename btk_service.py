"""
SeeRPG BTK Service
Fetches and caches the official SeePD BTK dataset from https://btkapi.seepd.hu/btk
Reconstructs hierarchical full names for all subpoints.
"""
import json
import os
import urllib.request
import logging

logger = logging.getLogger(__name__)

CACHE_FILE = os.path.join(os.path.dirname(__file__), "btk_cache.json")
API_URL = "https://btkapi.seepd.hu/btk"

class BTKService:
    def __init__(self):
        self.categories = {}
        self.points = []
        self.points_by_id = {}
        self.points_by_code = {}
        self.load_data()

    def load_data(self, force_refresh=False):
        data = None
        if not force_refresh and os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")

        if not data:
            data = self.fetch_remote()

        if data and "data" in data:
            self._parse_data(data["data"])
        elif data:
            self._parse_data(data)

    def fetch_remote(self):
        try:
            req = urllib.request.Request(API_URL, headers={"User-Agent": "SeeRPG-VoiceAssistant/1.0"})
            with urllib.request.urlopen(req, timeout=8) as res:
                content = res.read().decode("utf-8")
                data = json.loads(content)
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"Updated BTK cache from {API_URL}")
                return data
        except Exception as e:
            logger.error(f"Error fetching BTK data from {API_URL}: {e}")
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None

    def _parse_data(self, raw_data):
        cats = raw_data.get("categories", [])
        self.categories = {c["id"]: c.get("name", "") for c in cats}

        all_points = raw_data.get("points", [])
        
        # Hierarchikus teljes név felépítése (a fejezetcímek / fejlécek hozzárendelése az alpontokhoz)
        self.points = []
        curr_header = ""
        for p in all_points:
            p_type = p.get("type", 0)
            p_name = p.get("name", "").strip()

            if p_type == 1: # Fejléc
                curr_header = p_name
            elif p_type == 0: # Érvényes tétel
                if p_name.startswith("-") and curr_header:
                    p["fullName"] = f"{curr_header} {p_name}"
                else:
                    p["fullName"] = p_name
                self.points.append(p)

        self.points_by_id = {p["id"]: p for p in self.points}
        self.points_by_code = {p["pNumber"].strip().upper(): p for p in self.points if p.get("pNumber")}
        self._cached_summary_context = None
        logger.info(f"Loaded {len(self.points)} valid BTK offenses with hierarchical full names.")

    def get_summary_context_for_ai(self):
        """Kompakt kontextus készítése a Gemini AI számára az összes BTK tételből (gyorsítótárazva)."""
        if getattr(self, "_cached_summary_context", None):
            return self._cached_summary_context

        lines = []
        for p in self.points:
            code = p.get("pNumber", "").strip()
            full_name = p.get("fullName", p.get("name", "")).strip()
            desc = (p.get("description") or "").strip()
            f_min, f_max = p.get("fineMin") or 0, p.get("fineMax") or 0
            j_min, j_max = p.get("jailMin") or 0, p.get("jailMax") or 0
            cat_name = self.categories.get(p.get("categoryId"), "")
            
            jail_str = f", Börtön: {j_min}-{j_max} perc" if (j_min or j_max) else ""
            fine_str = f"Bírság: {f_min}-{f_max} Ft"
            desc_str = f" [Leírás: {desc[:60]}...]" if desc else ""
            lines.append(f"[{code}] {full_name} ({cat_name}) - {fine_str}{jail_str}{desc_str}")
        self._cached_summary_context = "\n".join(lines)
        return self._cached_summary_context
