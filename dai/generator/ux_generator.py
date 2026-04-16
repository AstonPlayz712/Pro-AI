"""DAI.UXGenerator — generate complete UX assets for a department.

Produces:
  - UX panels (screen layouts + component layouts)
  - UX flows (interaction logic + state transitions)
  - Animations (motion rules, easing, timing, micro-interactions)
  - Transitions (screen transitions, state transitions)
  - 3D layers (elevation, parallax)
  - Liquid Glass (LG) layers (blur, refraction, material)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from dai.core import Registry


class UXGenerator:
    """Creates the full UX asset tree for a department."""

    def __init__(self, *, registry: Registry, base_dir: Path) -> None:
        self.registry = registry
        self.base = base_dir

    def generate(self, dept_name: str, **ctx: Any) -> Dict[str, Any]:
        slug = dept_name.lower()
        ux_root = self.base / "ux" / slug
        files_created: List[str] = []

        # Create all UX subdirectories
        dirs = {
            "panels": ux_root,
            "flows": ux_root / "flows",
            "animations": ux_root / "animations",
            "transitions": ux_root / "transitions",
            "3d": ux_root / "3d",
            "lg": ux_root / "lg",
        }
        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)

        # --- Panels ---
        panels = self._generate_panels(dept_name, ux_root)
        files_created.extend(panels["files"])

        # --- Flows ---
        flows = self._generate_flows(dept_name, dirs["flows"])
        files_created.extend(flows["files"])

        # --- Animations ---
        animations = self._generate_animations(dept_name, dirs["animations"])
        files_created.extend(animations["files"])

        # --- Transitions ---
        transitions = self._generate_transitions(dept_name, dirs["transitions"])
        files_created.extend(transitions["files"])

        # --- 3D Layers ---
        three_d = self._generate_3d_layers(dept_name, dirs["3d"])
        files_created.extend(three_d["files"])

        # --- Liquid Glass Layers ---
        lg = self._generate_lg_layers(dept_name, dirs["lg"])
        files_created.extend(lg["files"])

        # Register panels
        for panel_name in panels["names"]:
            self.registry.register_ux_panel(dept_name, {
                "name": panel_name,
                "type": "panel",
            })

        return {
            "panels": panels["names"],
            "flows": flows["names"],
            "animations": animations["names"],
            "transitions": transitions["names"],
            "3d_layers": three_d["names"],
            "lg_layers": lg["names"],
            "files_created": files_created,
        }

    # ---- Panel generation ---------------------------------------------------

    def _generate_panels(self, dept_name: str, ux_root: Path) -> Dict[str, Any]:
        panel_names = [
            f"{dept_name}.Dashboard",
            f"{dept_name}.CommandCenter",
            f"{dept_name}.SubAIMonitor",
        ]
        spec = {
            "department": dept_name,
            "panels": [
                {
                    "name": f"{dept_name}.Dashboard",
                    "layout": "grid-12",
                    "components": [
                        {"type": "header", "span": 12, "content": f"{dept_name} Dashboard"},
                        {"type": "status_card", "span": 4, "binding": "department.status"},
                        {"type": "subai_list", "span": 4, "binding": "department.subais"},
                        {"type": "activity_feed", "span": 4, "binding": "department.events"},
                        {"type": "command_input", "span": 12, "binding": "department.command"},
                    ],
                },
                {
                    "name": f"{dept_name}.CommandCenter",
                    "layout": "split-horizontal",
                    "components": [
                        {"type": "command_palette", "region": "left", "binding": "commands"},
                        {"type": "output_console", "region": "right", "binding": "output"},
                    ],
                },
                {
                    "name": f"{dept_name}.SubAIMonitor",
                    "layout": "flex-wrap",
                    "components": [
                        {"type": "subai_card", "repeat": "subais", "binding": "subai.*"},
                    ],
                },
            ],
        }

        path = ux_root / "panels.json"
        path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        return {"names": panel_names, "files": [str(path)]}

    # ---- Flow generation ----------------------------------------------------

    def _generate_flows(self, dept_name: str, flows_dir: Path) -> Dict[str, Any]:
        flow_names = [
            f"{dept_name}.MainFlow",
            f"{dept_name}.CommandFlow",
            f"{dept_name}.MonitorFlow",
        ]
        spec = {
            "department": dept_name,
            "flows": [
                {
                    "name": f"{dept_name}.MainFlow",
                    "entry": "Dashboard",
                    "states": {
                        "Dashboard": {"on_command": "CommandCenter", "on_monitor": "SubAIMonitor"},
                        "CommandCenter": {"on_back": "Dashboard", "on_execute": "CommandCenter"},
                        "SubAIMonitor": {"on_back": "Dashboard", "on_select": "SubAIDetail"},
                        "SubAIDetail": {"on_back": "SubAIMonitor"},
                    },
                },
                {
                    "name": f"{dept_name}.CommandFlow",
                    "entry": "Input",
                    "states": {
                        "Input": {"on_submit": "Processing"},
                        "Processing": {"on_success": "Result", "on_error": "Error"},
                        "Result": {"on_dismiss": "Input"},
                        "Error": {"on_retry": "Input", "on_dismiss": "Input"},
                    },
                },
                {
                    "name": f"{dept_name}.MonitorFlow",
                    "entry": "Overview",
                    "states": {
                        "Overview": {"on_select": "Detail", "on_refresh": "Overview"},
                        "Detail": {"on_back": "Overview"},
                    },
                },
            ],
            "interaction_logic": {
                "command_submit": {
                    "trigger": "button.click | key.enter",
                    "action": "POST /api/{dept_name.lower()}/command",
                    "on_success": "transition(Result)",
                    "on_error": "transition(Error)",
                },
                "subai_select": {
                    "trigger": "card.click",
                    "action": "navigate(SubAIDetail, {subai_id})",
                },
            },
        }

        path = flows_dir / "flows.json"
        path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        return {"names": flow_names, "files": [str(path)]}

    # ---- Animation generation -----------------------------------------------

    def _generate_animations(self, dept_name: str, anim_dir: Path) -> Dict[str, Any]:
        anim_names = [
            f"{dept_name}.FadeIn",
            f"{dept_name}.SlideUp",
            f"{dept_name}.ScaleIn",
            f"{dept_name}.PulseGlow",
        ]
        spec = {
            "department": dept_name,
            "motion_rules": {
                "default_duration_ms": 300,
                "default_easing": "cubic-bezier(0.4, 0.0, 0.2, 1.0)",
                "reduced_motion": "respect-prefers-reduced-motion",
            },
            "easing_curves": {
                "ease_in": "cubic-bezier(0.4, 0.0, 1.0, 1.0)",
                "ease_out": "cubic-bezier(0.0, 0.0, 0.2, 1.0)",
                "ease_in_out": "cubic-bezier(0.4, 0.0, 0.2, 1.0)",
                "spring": "cubic-bezier(0.34, 1.56, 0.64, 1.0)",
                "sharp": "cubic-bezier(0.4, 0.0, 0.6, 1.0)",
            },
            "timing_curves": {
                "fast": 150,
                "normal": 300,
                "slow": 500,
                "entrance": 250,
                "exit": 200,
            },
            "animations": [
                {
                    "name": f"{dept_name}.FadeIn",
                    "keyframes": {"0%": {"opacity": 0}, "100%": {"opacity": 1}},
                    "duration_ms": 250,
                    "easing": "ease_out",
                },
                {
                    "name": f"{dept_name}.SlideUp",
                    "keyframes": {
                        "0%": {"transform": "translateY(20px)", "opacity": 0},
                        "100%": {"transform": "translateY(0)", "opacity": 1},
                    },
                    "duration_ms": 300,
                    "easing": "ease_in_out",
                },
                {
                    "name": f"{dept_name}.ScaleIn",
                    "keyframes": {
                        "0%": {"transform": "scale(0.9)", "opacity": 0},
                        "100%": {"transform": "scale(1)", "opacity": 1},
                    },
                    "duration_ms": 250,
                    "easing": "spring",
                },
                {
                    "name": f"{dept_name}.PulseGlow",
                    "keyframes": {
                        "0%": {"box-shadow": "0 0 0 0 rgba(100,149,237,0.4)"},
                        "70%": {"box-shadow": "0 0 0 10px rgba(100,149,237,0)"},
                        "100%": {"box-shadow": "0 0 0 0 rgba(100,149,237,0)"},
                    },
                    "duration_ms": 1500,
                    "easing": "ease_in_out",
                    "iteration": "infinite",
                },
            ],
            "micro_interactions": [
                {"trigger": "hover", "animation": "ScaleIn", "scale": 1.02, "duration_ms": 150},
                {"trigger": "press", "animation": "ScaleIn", "scale": 0.98, "duration_ms": 100},
                {"trigger": "focus", "animation": "PulseGlow", "duration_ms": 1500},
            ],
        }

        path = anim_dir / "animations.json"
        path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        return {"names": anim_names, "files": [str(path)]}

    # ---- Transition generation ----------------------------------------------

    def _generate_transitions(self, dept_name: str, trans_dir: Path) -> Dict[str, Any]:
        trans_names = [
            f"{dept_name}.ScreenSlide",
            f"{dept_name}.CrossFade",
            f"{dept_name}.MorphTransition",
        ]
        spec = {
            "department": dept_name,
            "screen_transitions": [
                {
                    "name": f"{dept_name}.ScreenSlide",
                    "type": "slide",
                    "direction": "left",
                    "duration_ms": 350,
                    "easing": "cubic-bezier(0.4, 0.0, 0.2, 1.0)",
                },
                {
                    "name": f"{dept_name}.CrossFade",
                    "type": "fade",
                    "duration_ms": 250,
                    "easing": "cubic-bezier(0.0, 0.0, 0.2, 1.0)",
                },
                {
                    "name": f"{dept_name}.MorphTransition",
                    "type": "shared-element",
                    "duration_ms": 400,
                    "easing": "cubic-bezier(0.4, 0.0, 0.2, 1.0)",
                    "shared_elements": ["header", "status_card"],
                },
            ],
            "state_transitions": [
                {
                    "from": "idle",
                    "to": "loading",
                    "animation": "FadeIn",
                    "duration_ms": 200,
                },
                {
                    "from": "loading",
                    "to": "ready",
                    "animation": "SlideUp",
                    "duration_ms": 300,
                },
                {
                    "from": "ready",
                    "to": "error",
                    "animation": "CrossFade",
                    "duration_ms": 250,
                },
            ],
        }

        path = trans_dir / "transitions.json"
        path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        return {"names": trans_names, "files": [str(path)]}

    # ---- 3D Layer generation ------------------------------------------------

    def _generate_3d_layers(self, dept_name: str, three_d_dir: Path) -> Dict[str, Any]:
        layer_names = [
            f"{dept_name}.BaseLayer",
            f"{dept_name}.CardLayer",
            f"{dept_name}.OverlayLayer",
            f"{dept_name}.ModalLayer",
        ]
        spec = {
            "department": dept_name,
            "elevation_rules": {
                "base": {"z_index": 0, "elevation_dp": 0, "shadow": "none"},
                "card": {"z_index": 1, "elevation_dp": 2, "shadow": "0 1px 3px rgba(0,0,0,0.12)"},
                "raised": {"z_index": 2, "elevation_dp": 6, "shadow": "0 3px 6px rgba(0,0,0,0.16)"},
                "overlay": {"z_index": 10, "elevation_dp": 16, "shadow": "0 8px 24px rgba(0,0,0,0.20)"},
                "modal": {"z_index": 100, "elevation_dp": 24, "shadow": "0 12px 48px rgba(0,0,0,0.25)"},
            },
            "parallax_rules": {
                "background_rate": 0.3,
                "midground_rate": 0.6,
                "foreground_rate": 1.0,
                "perspective_origin": "50% 50%",
                "perspective_px": 1200,
            },
            "layers": [
                {
                    "name": f"{dept_name}.BaseLayer",
                    "elevation": "base",
                    "parallax_group": "background",
                    "transform_style": "preserve-3d",
                },
                {
                    "name": f"{dept_name}.CardLayer",
                    "elevation": "card",
                    "parallax_group": "midground",
                    "transform_style": "preserve-3d",
                    "hover_lift_dp": 4,
                },
                {
                    "name": f"{dept_name}.OverlayLayer",
                    "elevation": "overlay",
                    "parallax_group": "foreground",
                    "transform_style": "preserve-3d",
                },
                {
                    "name": f"{dept_name}.ModalLayer",
                    "elevation": "modal",
                    "parallax_group": "foreground",
                    "transform_style": "preserve-3d",
                    "backdrop_blur_px": 8,
                },
            ],
        }

        path = three_d_dir / "3d_layers.json"
        path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        return {"names": layer_names, "files": [str(path)]}

    # ---- Liquid Glass (LG) Layer generation ---------------------------------

    def _generate_lg_layers(self, dept_name: str, lg_dir: Path) -> Dict[str, Any]:
        layer_names = [
            f"{dept_name}.LG.Frost",
            f"{dept_name}.LG.Crystal",
            f"{dept_name}.LG.Prism",
        ]
        spec = {
            "department": dept_name,
            "lg_global": {
                "blur_base_px": 20,
                "saturation": 1.8,
                "brightness": 1.05,
                "refraction_index": 1.45,
                "chromatic_aberration": 0.5,
                "noise_opacity": 0.03,
            },
            "blur_refraction_rules": {
                "frost": {
                    "backdrop_blur_px": 24,
                    "background": "rgba(255,255,255,0.25)",
                    "refraction_offset_px": 0,
                    "border": "1px solid rgba(255,255,255,0.18)",
                },
                "crystal": {
                    "backdrop_blur_px": 40,
                    "background": "rgba(255,255,255,0.12)",
                    "refraction_offset_px": 2,
                    "border": "1px solid rgba(255,255,255,0.25)",
                    "inner_glow": "inset 0 1px 0 rgba(255,255,255,0.3)",
                },
                "prism": {
                    "backdrop_blur_px": 60,
                    "background": "linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.05))",
                    "refraction_offset_px": 4,
                    "border": "1px solid rgba(255,255,255,0.30)",
                    "chromatic_fringe": True,
                    "specular_highlight": "radial-gradient(ellipse at 30% 20%, rgba(255,255,255,0.4), transparent 60%)",
                },
            },
            "layers": [
                {
                    "name": f"{dept_name}.LG.Frost",
                    "material": "frost",
                    "use_case": "cards, panels, sidebars",
                    "backdrop_filter": "blur(24px) saturate(1.8)",
                    "background": "rgba(255,255,255,0.25)",
                },
                {
                    "name": f"{dept_name}.LG.Crystal",
                    "material": "crystal",
                    "use_case": "modals, sheets, elevated surfaces",
                    "backdrop_filter": "blur(40px) saturate(1.8) brightness(1.05)",
                    "background": "rgba(255,255,255,0.12)",
                },
                {
                    "name": f"{dept_name}.LG.Prism",
                    "material": "prism",
                    "use_case": "hero cards, feature highlights, premium surfaces",
                    "backdrop_filter": "blur(60px) saturate(2.0) brightness(1.1)",
                    "background": "linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.05))",
                },
            ],
        }

        path = lg_dir / "lg_layers.json"
        path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        return {"names": layer_names, "files": [str(path)]}
