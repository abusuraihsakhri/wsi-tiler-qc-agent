"""
QuPath GeoJSON Annotation Export for WSI Tiler QC Agent.
Convert tile QC results into QuPath-compatible GeoJSON FeatureCollections.
"""
import datetime
from typing import List, Dict, Any, Tuple


def export_qupath_annotations(tiles: List[dict], slide_dims: Tuple[int, int] = (0, 0)) -> dict:
    """Convert tile QC results to QuPath-compatible GeoJSON FeatureCollection.
    Features include classification (PASS/FAIL/BLUR/PEN_MARKED) for import into QuPath."""
    features = []
    for t in tiles:
        x = t.get("x", 0)
        y = t.get("y", 0)
        w = t.get("width", 256)
        h = t.get("height", 256)
        blur_score = t.get("blur_score", 0)
        pen_marked = t.get("pen_marked", False)

        if pen_marked:
            status = "PEN_MARKED"
        elif blur_score < 0.3:
            status = "BLUR"
        elif blur_score > 0.5 and not pen_marked:
            status = "PASS"
        else:
            status = "FAIL"

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]]],
            },
            "properties": {
                "name": f"Tile_{t.get('tile_id', 'unknown')}",
                "classification": {"name": status},
                "blur_score": blur_score,
                "pen_marked": pen_marked,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total_tiles": len(features),
            "pass_count": sum(1 for f in features if f["properties"]["classification"]["name"] == "PASS"),
            "fail_count": sum(1 for f in features if f["properties"]["classification"]["name"] == "FAIL"),
            "blur_count": sum(1 for f in features if f["properties"]["classification"]["name"] == "BLUR"),
            "pen_marked_count": sum(1 for f in features if f["properties"]["classification"]["name"] == "PEN_MARKED"),
            "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
    }


def generate_qc_summary(tiles: List[dict]) -> dict:
    """Generate aggregated QC summary per slide with worst-tile identification."""
    if not tiles:
        return {"overall_qc_status": "NO_DATA", "total_tiles": 0}

    blur_scores = [t.get("blur_score", 0) for t in tiles]
    pass_tiles = sum(1 for s in blur_scores if s > 0.5)
    worst = sorted(tiles, key=lambda t: t.get("blur_score", 0))[:10]

    return {
        "overall_qc_status": "PASS" if pass_tiles / len(tiles) > 0.9 else "REVIEW",
        "total_tiles": len(tiles),
        "pass_tiles": pass_tiles,
        "fail_tiles": len(tiles) - pass_tiles,
        "mean_blur_score": round(sum(blur_scores) / len(blur_scores), 3) if blur_scores else 0,
        "min_blur_score": round(min(blur_scores), 3) if blur_scores else 0,
        "max_blur_score": round(max(blur_scores), 3) if blur_scores else 0,
        "top_10_worst_tiles": [
            {"tile_id": t.get("tile_id"), "blur_score": t.get("blur_score")} for t in worst
        ],
    }
