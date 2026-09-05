"""
Multi-Resolution Focus Quality Heatmap for WSI Tiler QC Agent.
Generate per-tile focus heatmaps as QuPath-compatible annotation overlays.
"""
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class TileFocusData:
    """Focus quality data for a single tile."""
    tile_id: str
    x: int
    y: int
    width: int = 256
    height: int = 256
    blur_score: float = 0.0
    laplacian_variance: float = 0.0
    focus_quality: str = "unknown"  # "sharp", "acceptable", "blurry", "out_of_focus"


class FocusHeatmapGenerator:
    """Generate focus quality heatmaps from tile QC data."""

    FOCUS_THRESHOLDS = {
        "sharp": 100.0,
        "acceptable": 50.0,
        "blurry": 20.0,
    }

    def __init__(self):
        self.tile_data: Dict[str, List[TileFocusData]] = {}

    def register_tiles(self, case_id: str, tiles: List[TileFocusData]):
        self.tile_data[case_id] = tiles

    def classify_focus(self, blur_score: float) -> str:
        if blur_score >= self.FOCUS_THRESHOLDS["sharp"]:
            return "sharp"
        elif blur_score >= self.FOCUS_THRESHOLDS["acceptable"]:
            return "acceptable"
        elif blur_score >= self.FOCUS_THRESHOLDS["blurry"]:
            return "blurry"
        return "out_of_focus"

    def generate_focus_heatmap(self, case_id: str) -> dict:
        tiles = self.tile_data.get(case_id, [])
        if not tiles:
            return {"error": "No tile data found", "tile_count": 0}

        classified_tiles = []
        for t in tiles:
            quality = self.classify_focus(t.blur_score)
            classified_tiles.append({
                "tile_id": t.tile_id,
                "x": t.x,
                "y": t.y,
                "width": t.width,
                "height": t.height,
                "blur_score": t.blur_score,
                "focus_quality": quality,
            })

        quality_counts = {}
        for t in classified_tiles:
            q = t["focus_quality"]
            quality_counts[q] = quality_counts.get(q, 0) + 1

        total = len(classified_tiles)
        sharp_pct = quality_counts.get("sharp", 0) / total * 100 if total else 0

        return {
            "case_id": case_id,
            "tile_count": total,
            "quality_distribution": quality_counts,
            "sharp_percentage": round(sharp_pct, 1),
            "overall_focus_grade": "PASS" if sharp_pct > 80 else "REVIEW" if sharp_pct > 50 else "FAIL",
            "tiles": classified_tiles,
        }

    def get_worst_tiles(self, case_id: str, n: int = 10) -> List[dict]:
        tiles = self.tile_data.get(case_id, [])
        sorted_tiles = sorted(tiles, key=lambda t: t.blur_score)[:n]
        return [
            {"tile_id": t.tile_id, "x": t.x, "y": t.y, "blur_score": t.blur_score,
             "focus_quality": self.classify_focus(t.blur_score)}
            for t in sorted_tiles
        ]
