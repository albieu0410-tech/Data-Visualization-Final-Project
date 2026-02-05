"""Engine DNA card + SVG schema generator."""

from __future__ import annotations

import html
from dataclasses import dataclass


@dataclass
class EngineDNA:
    make: str
    model: str
    trim: str
    engine_type: str
    cylinder_layout: str
    cylinders: int | float | None
    hp: float | None
    displacement_l: float | None
    accel: float | None
    fuel: float | None


def render_engine_dna(dna: EngineDNA) -> str:
    svg = svg_engine_layout(dna.cylinder_layout, dna.cylinders)
    return f"""
    <div class="engine-card">
      <div class="engine-card__header">
        <div>
          <div class="engine-card__title">{html.escape(dna.make)} {html.escape(dna.model)}</div>
          <div class="engine-card__subtitle">{html.escape(dna.trim)}</div>
        </div>
        <div class="engine-card__pill">{html.escape(dna.engine_type)}</div>
      </div>
      <div class="engine-card__body">
        <div class="engine-card__metrics">
          <div><span>HP</span><strong>{format_value(dna.hp)}</strong></div>
          <div><span>Displ</span><strong>{format_value(dna.displacement_l, 'L')}</strong></div>
          <div><span>0-100</span><strong>{format_value(dna.accel, 's')}</strong></div>
          <div><span>Fuel</span><strong>{format_value(dna.fuel, 'L/100km')}</strong></div>
        </div>
        <div class="engine-card__svg">{svg}</div>
      </div>
    </div>
    """


def format_value(value: float | None, suffix: str = "") -> str:
    if value is None or value != value:
        return "N/A"
    if suffix:
        return f"{value:.1f} {suffix}"
    return f"{value:.0f}"


def svg_engine_layout(layout: str, cylinders: int | float | None) -> str:
    layout = (layout or "inline").lower()
    count = int(cylinders) if cylinders and cylinders == cylinders else 4
    count = max(2, min(count, 12))

    if "v" in layout:
        return _svg_v_engine(count)
    if "boxer" in layout or "flat" in layout:
        return _svg_boxer_engine(count)
    return _svg_inline_engine(count)


def _svg_inline_engine(count: int) -> str:
    blocks = "".join(
        f'<rect x="{10 + i * 18}" y="20" width="14" height="24" rx="3" class="block" />'
        for i in range(count)
    )
    width = 20 + count * 18
    return f"""
    <svg viewBox="0 0 {width} 60" xmlns="http://www.w3.org/2000/svg">
      <rect x="6" y="10" width="{width - 12}" height="40" rx="10" class="block" />
      {blocks}
    </svg>
    """


def _svg_v_engine(count: int) -> str:
    half = count // 2
    left = "".join(
        f'<rect x="{12 + i * 16}" y="{18 + i * 3}" width="12" height="22" rx="3" class="block" />'
        for i in range(half)
    )
    right = "".join(
        f'<rect x="{80 - i * 16}" y="{18 + i * 3}" width="12" height="22" rx="3" class="block" />'
        for i in range(half)
    )
    return f"""
    <svg viewBox="0 0 120 60" xmlns="http://www.w3.org/2000/svg">
      <polygon points="60,8 110,52 10,52" class="block" />
      {left}
      {right}
    </svg>
    """


def _svg_boxer_engine(count: int) -> str:
    half = count // 2
    left = "".join(
        f'<rect x="{10}" y="{12 + i * 18}" width="30" height="12" rx="3" class="block" />'
        for i in range(half)
    )
    right = "".join(
        f'<rect x="{80}" y="{12 + i * 18}" width="30" height="12" rx="3" class="block" />'
        for i in range(half)
    )
    return f"""
    <svg viewBox="0 0 120 60" xmlns="http://www.w3.org/2000/svg">
      <rect x="45" y="18" width="30" height="24" rx="6" class="block" />
      {left}
      {right}
    </svg>
    """
