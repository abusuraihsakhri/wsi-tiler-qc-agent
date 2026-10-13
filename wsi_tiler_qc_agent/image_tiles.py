"""Local raster-image tiling and exploratory quality metrics.

Supports Pillow-readable raster files, not proprietary whole-slide formats
that require OpenSlide or a vendor SDK. Thresholds are experimental.
"""
import argparse
import csv
import json
from pathlib import Path


def _otsu(gray):
    """Otsu threshold for an 8-bit grayscale thumbnail."""
    import numpy as np

    hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    total = hist.sum()
    if not total:
        return 0
    weighted_sum = np.dot(np.arange(256), hist)
    left_weight = 0.0
    left_sum = 0.0
    best = -1.0
    threshold = 0
    for level in range(256):
        left_weight += hist[level]
        left_sum += level * hist[level]
        right_weight = total - left_weight
        if left_weight <= 0 or right_weight <= 0:
            continue
        difference = left_sum / left_weight - (weighted_sum - left_sum) / right_weight
        variance = left_weight * right_weight * difference * difference
        if variance > best:
            best = variance
            threshold = level
    return min(threshold, 235)


def qc_metrics(tile, tissue_threshold):
    """Return tissue fraction, Laplacian variance and saturated color fraction."""
    import numpy as np

    rgb = np.asarray(tile.convert("RGB"), dtype=np.float32)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = .299 * r + .587 * g + .114 * b
    tissue = float(np.mean(gray <= tissue_threshold) * 100)
    color = ((b > 1.45 * r) & (b > 1.15 * g) |
             (g > 1.55 * r) & (g > 1.08 * b)) & (
                 np.maximum.reduce([r, g, b]) - np.minimum.reduce([r, g, b]) > 65
             )
    color_percentage = float(np.mean(color) * 100)
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        focus = 0.0
    else:
        laplacian = (
            4 * gray[1:-1, 1:-1] - gray[1:-1, :-2] -
            gray[1:-1, 2:] - gray[:-2, 1:-1] - gray[2:, 1:-1]
        )
        focus = float(np.var(laplacian[::2, ::2]))
    return tissue, max(0.0, focus), color_percentage


def process_image(input_path, output_dir, tile_size=256, tissue_cutoff=5.0,
                  focus_cutoff=30.0, color_cutoff=12.0, max_pixels=100_000_000):
    """Tile a local image, save accepted PNG patches and QC manifests.

    Output coordinates refer to level-0 pixels; edge patches are cropped.
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Install the image extras: pip install '.[images]'") from exc

    if isinstance(tile_size, bool) or not 64 <= tile_size <= 4096:
        raise ValueError("tile_size must be in [64, 4096]")
    if any(not 0 <= x <= 100 for x in (tissue_cutoff, color_cutoff)):
        raise ValueError("Percentage thresholds must be between 0 and 100")
    if focus_cutoff < 0 or not np.isfinite(focus_cutoff):
        raise ValueError("focus_cutoff must be finite and non-negative")
    if max_pixels <= 0:
        raise ValueError("max_pixels must be positive")

    source = Path(input_path).expanduser().resolve(strict=True)
    if not source.is_file():
        raise ValueError("Input must be an image file")
    destination = Path(output_dir).expanduser().resolve()
    if destination == source or source in destination.parents:
        raise ValueError("Output directory must not be the input image")
    destination.mkdir(parents=True, exist_ok=True)
    patches = destination / "accepted"
    patches.mkdir(exist_ok=True)

    with Image.open(source) as slide:
        width, height = slide.size
        if width * height > max_pixels:
            raise ValueError(f"Image exceeds {max_pixels} pixels")
        thumbnail = slide.convert("RGB")
        thumbnail.thumbnail((512, 512))
        arr = np.asarray(thumbnail, dtype=np.float32)
        gray = np.asarray(.299 * arr[:, :, 0] + .587 * arr[:, :, 1] +
                          .114 * arr[:, :, 2], dtype=np.uint8)
        threshold = _otsu(gray)
        records = []
        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                w, h = min(tile_size, width - x), min(tile_size, height - y)
                region = slide.crop((x, y, x+w, y+h)).convert("RGB")
                tissue, focus, color = qc_metrics(region, threshold)
                status = ("BACKGROUND" if tissue < tissue_cutoff else
                          "LOW_FOCUS" if focus < focus_cutoff else
                          "COLOR_REVIEW" if color > color_cutoff else "ACCEPTED")
                tile_id = f"tile_{x}_{y}"
                if status == "ACCEPTED":
                    region.save(patches / f"{tile_id}.png")
                records.append({
                    "tile_id": tile_id, "x": x, "y": y, "width": w, "height": h,
                    "tissue_percentage": round(tissue, 2),
                    "focus_laplacian_variance": round(focus, 2),
                    "suspected_color_percentage": round(color, 2),
                    "status": status,
                })

    from .qupath_export import export_qupath_annotations
    with (destination / "tile_qc.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    geojson = export_qupath_annotations(records, (width, height))
    (destination / "tile_qc.geojson").write_text(
        json.dumps(geojson, indent=2), encoding="utf-8")
    counts = {name: sum(row["status"] == name for row in records) for name in
              ("ACCEPTED", "LOW_FOCUS", "COLOR_REVIEW", "BACKGROUND")}
    summary = {"source": source.name, "width": width, "height": height,
               "tile_size": tile_size, "otsu_threshold": threshold,
               "tiles": len(records), "counts": counts}
    (destination / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local raster tiling and exploratory patch QC")
    parser.add_argument("image", help="Pillow-readable PNG, JPEG, TIFF or other raster")
    parser.add_argument("-o", "--output", required=True, help="Destination directory")
    parser.add_argument("--tile-size", type=int, default=256)
    parser.add_argument("--tissue-cutoff", type=float, default=5.0)
    parser.add_argument("--focus-cutoff", type=float, default=30.0)
    parser.add_argument("--color-cutoff", type=float, default=12.0)
    args = parser.parse_args(argv)
    result = process_image(args.image, args.output, args.tile_size,
                           args.tissue_cutoff, args.focus_cutoff, args.color_cutoff)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
