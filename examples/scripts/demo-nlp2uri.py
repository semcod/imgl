#!/usr/bin/env python3
"""Demo: NL → URI → resolve dla kilku przykładowych komend."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from imgl import ImglConfig, analyze  # noqa: E402
from imgl.catalog import build_interactive_catalog  # noqa: E402
from imgl.interact import InteractSession, resolve_imgl_uri  # noqa: E402
from imgl.nlp2uri import prompt_to_imgl_uri  # noqa: E402
from imgl.window_scope import apply_discovered_windows  # noqa: E402


def main() -> int:
    image = sys.argv[1] if len(sys.argv) > 1 else "screen.png"
    window_id = sys.argv[2] if len(sys.argv) > 2 else "region-top"
    vql_file = "layout.vql.json"

    print(f"=== nlp2uri demo: {image} window={window_id} ===\n")

    scene = analyze(image, lang="eng+pol", config=ImglConfig())
    scene = apply_discovered_windows(scene)
    catalog = build_interactive_catalog(
        scene,
        image_path=image,
        vql_file=vql_file,
        lang="eng+pol",
        window_id=window_id,
        use_llm=False,
    )
    session = InteractSession(
        image_path=str(Path(image).resolve()),
        vql_file=str(Path(vql_file).resolve()),
        lang="eng+pol",
        scene=scene,
        catalog=catalog,
        selected_window_id=window_id,
    )

    prompts = [
        "3",
        "kliknij Projects",
        "kliknij Follow",
        "wpisz hello w Type to search",
        "mapa",
    ]

    for prompt in prompts:
        resolved = prompt_to_imgl_uri(
            prompt,
            image=session.image_path,
            file=session.vql_file,
            lang=session.lang,
            catalog=session.catalog,
        )
        if resolved is None:
            print(f"  {prompt!r} → (brak dopasowania)")
            continue
        result = resolve_imgl_uri(resolved.uri, session)
        status = "OK" if result.get("ok") else f"ERR: {result.get('error')}"
        action = result.get("action", resolved.match_reason)
        coords = ""
        if result.get("x") is not None:
            coords = f" @ ({result['x']},{result['y']})"
        print(f"  {prompt!r}")
        print(f"    → {resolved.match_reason} [{status}] {action}{coords}")

    print("\nUruchom interaktywnie:")
    print(f"  imgl interact {image} --llm --window {window_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
