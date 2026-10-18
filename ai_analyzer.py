"""
SeeRPG AI Analyzer
Connects to Google Gemini API via official google-genai SDK.
Optimized for ultra-fast response (~1.5s) and precise Hungarian police speech recognition.
"""
import json
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self, btk_service, google_api_key: str = "", model_name: str = "gemini-2.0-flash-lite"):
        self.btk_service = btk_service
        self.google_api_key = google_api_key
        self.model_name = model_name
        self._client = None
        if self.google_api_key:
            self._init_client()

    def _init_client(self):
        try:
            from google import genai
            self._client = genai.Client(api_key=self.google_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize google-genai client: {e}")
            self._client = None

    def set_api_keys(self, google_api_key: str, groq_api_key: str = "", model_name: str = None):
        self.google_api_key = google_api_key
        if model_name:
            self.model_name = model_name
        self._init_client()

    def analyze_audio(self, wav_bytes: bytes) -> Dict[str, Any]:
        """
        Analyzes audio bytes directly using Google Gemini API.
        Returns dict with keys: 'transcription', 'offenses' (list of {'code': str, 'name': str, 'count': int})
        """
        if not self.google_api_key:
            return {
                "error": "Nincs beállítva Google Gemini API kulcs! Kérlek add meg a Beállításokban.",
                "transcription": "",
                "offenses": []
            }

        if len(wav_bytes) < 1000:
            return {
                "error": "A rögzített hang túl rövid volt.",
                "transcription": "",
                "offenses": []
            }

        if not self._client:
            self._init_client()
            if not self._client:
                return {
                    "error": "Nem sikerült csatlakozni a Google API-hoz.",
                    "transcription": "",
                    "offenses": []
                }

        try:
            from google.genai import types

            btk_context = self.btk_service.get_summary_context_for_ai()
            
            prompt = f"""
Te egy magyar SeeRPG (FiveM GTA V) rendvédelmi BTK asszisztens vagy.
A csatolt hangfájlban kizárólag MAGYAR nyelvű beszéd hallható: egy rendőr / járőr beszél igazoltatás vagy intézkedés közben.

FONTOS BESZÉDFELISMERÉSI ÉS BTK ÉRTELMEZÉSI SZABÁLYOK:
1. Pontosan írd le az elhangzott magyar szöveget a 'transcription' mezőbe!
2. A leirat alapján azonosítsd be a megvalósult hivatalos SeePD BTK tételeket.
3. KIFEJEZÉSEK ÉS PÁROSÍTÁSI SZABÁLYOK:
   - "fegyver volt nála engedély nélkül / illegális fegyver" ➡️ [IFBK] Illegális fegyver birtoklás - Engedélyköteles fegyverek (VIGYÁZAT: az IFAB az FegyverALKATRÉSZ birtoklása, azt csak akkor válaszd, ha kifejezetten alkatrészt mondott!)
   - "gyorshajtás", "átment a piroson / nem állt meg a pirosnál" ➡️ [KSZTM] KRESZ Szabálypont megsértése
   - "nem állt meg a stop táblánál" ➡️ [STFK] STOP Tábla figyelmen kívül hagyása
   - "nem volt nála jogosítvány" ➡️ [JNV] Jogosítvány nélküli vezetés
4. EGYEDISÉG (DEDUPLIKÁCIÓ):
   - Egy adott BTK kód (pl. KSZTM) KIZÁRÓLAG EGYSZER szerepelhet a listában! Ha több KRESZ szabályt is megszegett (pl. gyorshajtás + piros lámpa), a KSZTM akkor is CSAK 1X adható!
5. KIZÁRÓLAG egy érvényes JSON objektumot adj vissza:

{{
  "transcription": "a pontosan elhangzott magyar szöveg",
  "offenses": [
    {{
      "code": "A hivatalos BTK rövidítés (pl. IFBK, KSZTM, STFK, FF, stb.)",
      "name": "A szabálysértés teljes neve",
      "count": 1,
      "accomplice": false
    }}
  ]
}}

HIVATALOS BTK TÉTELEK ÉS RÖVIDÍTÉSEIK:
{btk_context}

Kizárólag a fenti listában létező 'code' (rövidítés) kódokat használd! Ne duplikálj kódokat! Ne írj semmi más szöveget a JSON-ön kívül!
"""

            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"),
                        prompt
                    ]
                )
            except Exception as model_err:
                if "404" in str(model_err) or "not found" in str(model_err).lower():
                    logger.warning(f"Model {self.model_name} returned 404, fallback to gemini-2.5-flash: {model_err}")
                    response = self._client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"),
                            prompt
                        ]
                    )
                else:
                    raise model_err

            response_text = response.text or ""
            if not response_text:
                raise Exception("Üres válasz érkezett az AI-tól.")

            # JSON kinyerése a válaszból
            json_str = response_text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            parsed = json.loads(json_str)
            raw_offenses = parsed.get("offenses", [])
            
            # Kódok deduplikálása (egy embernek egy tételt csak 1x lehet adni)
            seen_codes = set()
            unique_offenses = []
            for off in raw_offenses:
                c = off.get("code", "").strip().upper()
                if c and c not in seen_codes:
                    seen_codes.add(c)
                    unique_offenses.append(off)

            return {
                "transcription": parsed.get("transcription", ""),
                "offenses": unique_offenses
            }

        except Exception as e:
            logger.error(f"Error in Gemini AI analysis: {e}")
            return {
                "error": f"AI hiba: {str(e)}",
                "transcription": "",
                "offenses": []
            }

    def analyze_text_direct(self, text: str) -> Dict[str, Any]:
        """Szöveg közvetlen elemzése teszteléshez."""
        if not self._client:
            self._init_client()
        if not self._client:
            return {"error": "Nincs API kulcs", "offenses": []}
        try:
            btk_context = self.btk_service.get_summary_context_for_ai()
            prompt = f"""
Azonosítsd be a magyar szövegből a SeeRPG BTK tételeket: "{text}"
Szabályok:
- "fegyver volt nála engedély nélkül" ➡️ [IFBK] Illegális fegyver birtoklás - Engedélyköteles fegyverek (az IFAB csak alkatrész!)
- "gyorshajtás" vagy "piros lámpa" ➡️ [KSZTM] KRESZ Szabálypont megsértése
- Egy BTK kód (pl. KSZTM) csak EGYSZER szerepelhet a listában!
Válaszként kizárólag JSON-t adj vissza:
{{
  "transcription": "{text}",
  "offenses": [
    {{"code": "RÖVIDÍTÉS", "name": "Név", "count": 1, "accomplice": false}}
  ]
}}
BTK lista:
{btk_context}
"""
            try:
                res = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
            except Exception as model_err:
                if "404" in str(model_err) or "not found" in str(model_err).lower():
                    logger.warning(f"Model {self.model_name} returned 404 for text, falling back to gemini-2.5-flash")
                    res = self._client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                else:
                    raise model_err
            json_str = res.text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            parsed = json.loads(json_str)

            seen_codes = set()
            unique_offenses = []
            for off in parsed.get("offenses", []):
                c = off.get("code", "").strip().upper()
                if c and c not in seen_codes:
                    seen_codes.add(c)
                    unique_offenses.append(off)

            return {
                "transcription": parsed.get("transcription", ""),
                "offenses": unique_offenses
            }
        except Exception as e:
            return {"error": str(e), "offenses": []}
