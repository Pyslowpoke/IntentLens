"""On-demand exports run separately from publishing a usable chart preview."""
import os
import sys
import tempfile
from pathlib import Path
from services.api import store
from services.api.contracts import ChartSpec
from services.api.render import render, resolve, configure_export_browser


def export(id, format):
    revision = store.get("revision", id)
    if format not in revision.get("available_exports", []):
        raise ValueError("Format unavailable")
    destination = store.root() / "artifacts" / id
    with tempfile.TemporaryDirectory(dir=destination) as temporary:
        temporary = Path(temporary)
        spec = ChartSpec.model_validate(revision["spec"])
        if resolve(spec) == "plotly":
            configure_export_browser()
            import plotly.io as pio
            figure = pio.read_json(destination / revision["artifacts"]["plotly"])
            figure.write_image(temporary / f"chart.{format}", format=format, width=spec.width, height=spec.height)
        else:
            render(revision["result"], spec, temporary)
        source = temporary / f"chart.{format}"
        if not source.is_file() or source.stat().st_size == 0:
            raise ValueError("Export produced no file")
        os.replace(source, destination / source.name)


if __name__ == "__main__":
    export(sys.argv[1], sys.argv[2])
