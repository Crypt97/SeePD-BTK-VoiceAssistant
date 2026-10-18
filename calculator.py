"""
SeeRPG BTK Calculator
Calculates aggregated fines, jail times, document revocations and command templates.
Uses the official SeePD formula with safe handling for null database values.
"""
from typing import List, Dict, Any, Optional

def format_huf(val: int) -> str:
    return f"{val:,}".replace(",", " ")

def s_val(v):
    return v if v is not None else 0

def c_val(base, pbp):
    n = pbp if pbp is not None else -1
    return s_val(base) if n < 0 else n

class BTKCalculator:
    def __init__(self, btk_service):
        self.btk_service = btk_service

    def calculate(self, offenses: List[Dict[str, Any]], ease_percent: int = 0) -> Dict[str, Any]:
        """
        offenses: list of dicts: {"code": "GYH", "count": 1, "accomplice": False} or {"id": 1, ...}
        ease_percent: 0-100 (enyhítés mértéke)
        """
        resolved_items = []
        fine_min = 0
        fine_max = 0
        jail_min = 0
        jail_max = 0
        
        has_jail = False
        any_no_bail = False
        max_revoke_dl = 0  # 0: nem, 1: bevonható, 2: kötelező
        max_revoke_gl = 0

        codes = []

        for item in offenses:
            code = item.get("code", "").strip().upper()
            point_id = item.get("id")
            count = max(1, item.get("count", 1))
            accomplice = item.get("accomplice", False)

            point = None
            if code and code in self.btk_service.points_by_code:
                point = self.btk_service.points_by_code[code]
            elif point_id and point_id in self.btk_service.points_by_id:
                point = self.btk_service.points_by_id[point_id]

            if not point:
                continue

            multiplier = 2 if accomplice else 1
            c_diff = max(0, count - 1)

            # Hivatalos SeePD képlet
            p_f_min = point.get("fineMin")
            p_f_max = point.get("fineMax")
            p_pbp_f_min = point.get("pbpFineMin")
            p_pbp_f_max = point.get("pbpFineMax")

            l_f = c_val(p_f_min, p_pbp_f_min)
            u_f = c_val(p_f_max, p_pbp_f_max)
            item_f_min = int((s_val(p_f_min) + c_diff * l_f) / multiplier)
            item_f_max = int((s_val(p_f_max) + c_diff * u_f) / multiplier)

            p_j_min = point.get("jailMin")
            p_j_max = point.get("jailMax")
            p_pbp_j_min = point.get("pbpJailMin")
            p_pbp_j_max = point.get("pbpJailMax")

            l_j = c_val(p_j_min, p_pbp_j_min)
            u_j = c_val(p_j_max, p_pbp_j_max)
            item_j_min = int((s_val(p_j_min) + c_diff * l_j) / multiplier)
            item_j_max = int((s_val(p_j_max) + c_diff * u_j) / multiplier)

            fine_min += item_f_min
            fine_max += item_f_max
            jail_min += item_j_min
            jail_max += item_j_max

            if item_j_max > 0:
                has_jail = True
                if not point.get("bail", False):
                    any_no_bail = True

            max_revoke_dl = max(max_revoke_dl, point.get("revokeDl") or 0)
            max_revoke_gl = max(max_revoke_gl, point.get("revokeGl") or 0)

            p_code = point.get("pNumber", "").strip()
            codes.append(p_code if count == 1 else f"{p_code} (x{count})")

            resolved_items.append({
                "point": point,
                "count": count,
                "accomplice": accomplice,
                "fine_min": item_f_min,
                "fine_max": item_f_max,
                "jail_min": item_j_min,
                "jail_max": item_j_max,
            })

        # Enyhítés alkalmazása
        if ease_percent > 0:
            factor = (100 - ease_percent) / 100.0
            eased_f_min = int(fine_min * factor)
            eased_f_max = int(fine_max * factor)
            eased_j_min = int(jail_min * factor)
            eased_j_max = int(jail_max * factor)
        else:
            eased_f_min, eased_f_max = fine_min, fine_max
            eased_j_min, eased_j_max = jail_min, jail_max

        # Óvadék
        if not has_jail:
            bail_status = "Nincs (nincs börtön)"
        elif any_no_bail:
            bail_status = "Nem adható"
        else:
            bail_status = "Jár"

        # Iratok
        dl_map = {0: "Nem", 1: "Bevonható", 2: "Kötelező bevonni"}
        gl_map = {0: "Nem", 1: "Bevonható", 2: "Kötelező bevonni"}
        revoke_dl_str = dl_map.get(max_revoke_dl, "Nem")
        revoke_gl_str = gl_map.get(max_revoke_gl, "Nem")

        copy_text = ", ".join(codes)

        # TTS szöveg előkészítése
        names = [it["point"].get("name", "") for it in resolved_items]
        if not resolved_items:
            tts_text = "Nem sikerült azonosítani szabálysértést."
        else:
            names_str = ", ".join(names[:3])
            fine_target = eased_f_max if eased_f_max > 0 else eased_f_min
            fine_spoken = f"{format_huf(fine_target)} forint bírság" if fine_target > 0 else "nincs bírság"
            jail_spoken = f"{eased_j_max} perc börtön" if eased_j_max > 0 else ""
            
            parts = [f"Felismerve: {names_str}."]
            if jail_spoken:
                parts.append(f"{fine_spoken} és {jail_spoken}.")
            else:
                parts.append(f"{fine_spoken}.")

            if max_revoke_dl == 2:
                parts.append("A jogosítvány bevonása kötelező!")
            elif max_revoke_dl == 1:
                parts.append("A jogosítvány bevonható.")

            if max_revoke_gl == 2:
                parts.append("A fegyverengedély bevonása kötelező!")
            elif max_revoke_gl == 1:
                parts.append("A fegyverengedély bevonható.")

            tts_text = " ".join(parts)

        return {
            "items": resolved_items,
            "fine_min": eased_f_min,
            "fine_max": eased_f_max,
            "jail_min": eased_j_min,
            "jail_max": eased_j_max,
            "original_fine": (fine_min, fine_max),
            "original_jail": (jail_min, jail_max),
            "has_jail": has_jail,
            "bail_status": bail_status,
            "revoke_dl": revoke_dl_str,
            "revoke_gl": revoke_gl_str,
            "copy_text": copy_text,
            "tts_text": tts_text
        }
