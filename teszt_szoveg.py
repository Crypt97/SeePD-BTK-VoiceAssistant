"""
SeeRPG BTK Voice Assistant - Szöveges tesztelő szkript
Ezzel mikrofon nélkül is tesztelheted, hogy a mondataidból mit számolna a rendszer.
"""
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from btk_service import BTKService
from calculator import BTKCalculator
from ai_analyzer import AIAnalyzer
from settings_dialog import load_config

def main():
    cfg = load_config()
    key = cfg.get("google_api_key", "")
    
    print("=" * 60)
    print("[SeePD BTK] Szoveges Kalkulator Teszt")
    print("=" * 60)

    btk = BTKService()
    calc = BTKCalculator(btk)
    ai = AIAnalyzer(btk, google_api_key=key)

    if not key:
        print("\nFigyelem: Nincs Google API kulcs beallitva a config.json-ben.")
        print("Kozvetlen BTK kod minta-szamitas:\n")
        sample_offenses = [{"code": "GYH", "count": 1}, {"code": "FF", "count": 1}]
        res = calc.calculate(sample_offenses)
        print(f"Tetelk: {res['copy_text']}")
        print(f"Birsag: {res['fine_min']} - {res['fine_max']} Ft")
        print(f"Borton: {res['jail_max']} perc")
        print(f"Jogositvany: {res['revoke_dl']}")
        print(f"TTS felolvasas: {res['tts_text']}")
        return

    while True:
        try:
            mondat = input("\nIrj be egy igazoltatasi mondatot (vagy 'exit'): ").strip()
            if not mondat or mondat.lower() == 'exit':
                break

            print("AI elemzes folyamatban...")
            ai_res = ai.analyze_text_direct(mondat)
            
            offenses = ai_res.get("offenses", [])
            print(f"\nFelismerve ({len(offenses)} db):")
            for o in offenses:
                print(f"  * [{o.get('code')}] {o.get('name')}")

            calc_res = calc.calculate(offenses)
            print(f"\nVagolap szoveg: {calc_res['copy_text']}")
            print(f"Birsag: {calc_res['fine_min']:,} - {calc_res['fine_max']:,} Ft".replace(",", " "))
            print(f"Borton: {calc_res['jail_min']} - {calc_res['jail_max']} perc")
            print(f"Jogositvany: {calc_res['revoke_dl']}")
            print(f"TTS bemondas: \"{calc_res['tts_text']}\"")

        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
