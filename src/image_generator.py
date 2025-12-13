from PIL import Image, ImageDraw, ImageFont
import os

TEMPLATE_DIR = "assets/wrapped_cat/input"
OUTPUT_DIR = "assets/wrapped_cat/output"

SCALE = 2  # Trying this to improve text quality

TEMPLATES = {
    # Done!
    "year_overall_cat": {
        "file": "assets/wrapped_cat/input/year_overall_cat.png",
        "fields": {
            "activities_last_year":  {"pos": (740, 905), "size": 44, "color": "white"},
            "total_elevation_m":    {"pos": (800, 1105), "size": 44, "color": "white"},
            "dominant_sport":       {"pos": (825, 1285), "size": 44, "color": "white"},
            "total_time_minutes":   {"pos": (720, 1465), "size": 44, "color": "white"},
            "total_distance_km":    {"pos": (515, 1655), "size": 44, "color": "white"},
        }
    }, 
    # Done!
    "liked_activity": {
        "file": "assets/wrapped_cat/input/liked_activity_cat.png",
        "fields": {
            "activity_name":  {"pos": (540, 1280), "size": 44, "color": "white"},
            "activity_kudos": {"pos": (540, 1390), "size": 44, "color": "white"},
        }
    },
    # Done!
    "random_data_cat": {
        "file": "assets/wrapped_cat/input/random_data_cat.png",
        "fields": {
            "photo_count":  {"pos": (730, 930), "size": 38, "color": "white"},
            "kudos_count":    {"pos": (680, 1085), "size": 38, "color": "white"},
            "comment_count":       {"pos": (810, 1230), "size": 38, "color": "white"},
            "train_time":    {"pos": (600, 1385), "size": 38, "color": "white"},
            "total_mates":      {"pos": (735, 1535), "size": 38, "color": "white"},
            "social_ratio":   {"pos": (440, 1685), "size": 38, "color": "white"},
        }
    },
    # Done!
    "total_elevation_cat": {
        "file": "assets/wrapped_cat/input/total_elevation_cat.png",
        "fields": {
            "total_elevation_m":  {"pos": (540, 1225), "size": 44, "color": "white"},
            "everest_count":    {"pos": (540, 1625), "size": 44, "color": "white"},
        }
    },
    # Done!
    "total_km_cat": {
        "file": "assets/wrapped_cat/input/total_km_cat.png",
        "fields": {
            "total_distance_km":  {"pos": (540, 1065), "size": 44, "color": "white"},
            "distance_comp":    {"pos": (540, 1540), "size": 44, "color": "white"},
        }
    },
    # Done!
    "total_time_cat": {
        "file": "assets/wrapped_cat/input/total_time_cat.png",
        "fields": {
            "total_time_minutes":  {"pos": (540, 1300), "size": 44, "color": "white"},
            "total_time_days":    {"pos": (540, 1600), "size": 44, "color": "white"},
        }
    },
    # Done!
    "total_pr_cat": {
        "file": "assets/wrapped_cat/input/total_pr_cat.png",
        "fields": {
            "total_pr":  {"pos": (540, 1060), "size": 44, "color": "white"},
        }
    },
    # Done!
    "total_watts_cat": {
        "file": "assets/wrapped_cat/input/total_watts_cat.png",
        "fields": {
            "total_kWh":  {"pos": (540, 925), "size": 44, "color": "white"},
            "total_house_power":    {"pos": (540, 1350), "size": 44, "color": "white"},
        }
    },
    # Done!
    "multi_sport_cat": {
        "file": "assets/wrapped_cat/input/multi_sport_cat.png",
        "fields": {
            "total_sports":  {"pos": (540, 850), "size": 44, "color": "white"},
            "main_sport":    {"pos": (350, 1260), "size": 44, "color": "white"},
            "secondary_sport": {"pos": (350, 1360), "size": 44, "color": "white"},
            "third_sport":  {"pos": (350, 1460), "size": 44, "color": "white"},
        }
    }
}

FIELD_MAPPING = {
    # --- BASIC ---
    "activities_last_year": lambda s: str(s["activities_last_year"]),
    "total_distance_km":    lambda s: str(s["total_distance_km"]),
    "total_time_minutes":   lambda s: str(s["total_time_minutes"]),
    "total_time_days":      lambda s: str(s["total_time_days"]),
    "total_elevation_m":      lambda s: str(s["total_elevation_m"]),
    "dominant_sport":       lambda s: str(s["dominant_sport"]),

    # --- COMPARATIVE ---
    "distance_comp":        lambda s: str(s["distance_comparasion"]),
    "everest_count":        lambda s: str(s["everest_equivalent"]),

    # --- ENERGY ---
    "total_kWh":            lambda s: str(s["total_energy_kwh"]),
    "total_house_power":    lambda s: str(s["house_power_days"]),

    # --- ACTIVITY HIGHLIGHT ---
    "activity_name":         lambda s: s["most_kudos_activity"]["name"] or "",
    "activity_kudos":       lambda s: str(s["most_kudos_activity"]["kudos"]),

    # --- SOCIAL ---
    "photo_count":          lambda s: str(s["total_photos"]),
    "kudos_count":          lambda s: str(s["total_kudos"]),
    "comment_count":        lambda s: str(s["total_comments"]),
    "social_ratio":         lambda s: str(s["social_ratio"]),
    "train_time":           lambda s: str(s["total_time_days"]),
    "total_mates":          lambda s: str(s["sports_practiced"]),

    # --- PRs ---
    "total_pr":             lambda s: str(s["total_prs"]),

    # --- MULTI SPORT ---
    "total_sports":         lambda s: str(s["sports_practiced"]),
    "main_sport":           lambda s: _format_podium(s, "first"),
    "secondary_sport":      lambda s: _format_podium(s, "second"),
    "third_sport":          lambda s: _format_podium(s, "third"),
}

def _format_podium(stats, position):
    data = stats["sport_podium"].get(position)
    if not data or not data["sport"]:
        return ""
    return f'{data["sport"]} ({data["count"]})'


def resolve_field(field_name: str, stats: dict) -> str:
    resolver = FIELD_MAPPING.get(field_name)
    if not resolver:
        raise ValueError(f"Field '{field_name}' not defined in FIELD_MAPPING")
    return resolver(stats)

def load_font(size):
    try:
        return ImageFont.truetype("assets\fonts\Montserrat_Arabic_Regular\E:\PROJECTES\StravaWrapped\assets\fonts\Montserrat_Arabic_Regular\Montserrat_Arabic_Regular.ttf", size)
    except IOError:
        return ImageFont.load_default()

def render_template(template_name: str, stats: dict, output_path: str):
    template = TEMPLATES[template_name]

    img = Image.open(template["file"]).convert("RGBA")

    if SCALE != 1:
        img = img.resize(
            (img.width * SCALE, img.height * SCALE),
            Image.Resampling.LANCZOS
        )

    draw = ImageDraw.Draw(img)

    for field, cfg in template["fields"].items():
        text = resolve_field(field, stats)
        if not text:
            continue

        font = load_font(cfg["size"] * SCALE)

        scaled_pos = (
            cfg["pos"][0] * SCALE,
            cfg["pos"][1] * SCALE
        )

        draw.text(
            scaled_pos,
            text,
            fill=cfg["color"],
            font=font
        )

    img.save(output_path)


def generate_wrapped_images(stats):
    outputs = []
    for template_name in TEMPLATES:
        output = f"assets/wrapped_cat/output/{template_name}.png"
        render_template(template_name, stats, output)
        outputs.append(output)
    return outputs
