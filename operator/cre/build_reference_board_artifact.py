#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from reference_board import build_generic_reference_board


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a generic art reference board artifact set.")
    parser.add_argument("--request", required=True, help="Full drawing request.")
    parser.add_argument("--primary-subject", required=True, help="Primary subject to ground.")
    parser.add_argument("--anatomy-anchor", help="Real-world anatomy/form anchor.")
    parser.add_argument("--identity-anchor", help="Identity/brand/franchise anchor.")
    parser.add_argument("--style-anchor", help="Clothing/style-family anchor.")
    parser.add_argument("--must-have", action="append", default=[], help="Repeatable must-have part.")
    parser.add_argument("--must-avoid", action="append", default=[], help="Repeatable must-avoid drift.")
    parser.add_argument("--style-note", action="append", default=[], help="Repeatable style note.")
    parser.add_argument("--pose", default="readable full-subject pose")
    parser.add_argument("--camera-angle", default="straight-on to slight three-quarter view")
    parser.add_argument("--stem", required=True, help="Artifact filename stem.")
    parser.add_argument("--out-dir", default="operator/cre", help="Output directory for artifacts.")
    args = parser.parse_args()

    board = build_generic_reference_board(
        request=args.request,
        primary_subject=args.primary_subject,
        anatomy_anchor=args.anatomy_anchor,
        identity_anchor=args.identity_anchor,
        style_anchor=args.style_anchor,
        must_have_parts=args.must_have or None,
        must_avoid=args.must_avoid or None,
        style_notes=args.style_note or None,
        pose=args.pose,
        camera_angle=args.camera_angle,
    )
    written = board.save_split_artifacts(Path(args.out_dir), args.stem)
    for key, path in written.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
