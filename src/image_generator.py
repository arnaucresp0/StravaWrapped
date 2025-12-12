from PIL import Image, ImageDraw, ImageFont
import os

TEMPLATE_DIR = "assets/wrapped_cat/input"
OUTPUT_DIR = "assets/wrapped_cat/output"

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
            "activty_name":  {"pos": (540, 1280), "size": 44, "color": "white"},
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
            "total_elevation":  {"pos": (540, 1225), "size": 44, "color": "white"},
            "everest_count":    {"pos": (540, 1625), "size": 44, "color": "white"},
        }
    },
    # Done!
    "total_km_cat": {
        "file": "assets/wrapped_cat/input/total_elevation_cat.png",
        "fields": {
            "total_distance":  {"pos": (540, 1065), "size": 44, "color": "white"},
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
    #TODO: DEFINE THE TEXT POSITIONS...
    "multi_sport_cat": {
        "file": "assets/wrapped_cat/input/multi_sport_cat.png",
        "fields": {
            "total_sports":  {"pos": (200, 620), "size": 44, "color": "white"},
            "main_sport":    {"pos": (200, 740), "size": 44, "color": "white"},
            "secondary_sport": {"pos": (200, 740), "size": 44, "color": "white"},
            "third_sport":  {"pos": (200, 740), "size": 44, "color": "white"},
        }
    }
}

def render_template(template_key, stats, output_path):
    cfg = TEMPLATES[template_key]

    img = Image.open(cfg["file"]).convert("RGBA")
    draw = ImageDraw.Draw(img)

    for field, meta in cfg["fields"].items():
        value = stats.get(field, "")
        x, y = meta["pos"]
        size = meta["size"]
        color = meta.get("color", "white")

        font = ImageFont.truetype("assetes/fonts\Montserrat-Arabic Regular/Montserrat-Arabic Regular.ttf", size)

        draw.text((x, y), str(value), font=font, fill=color)

    img.save(output_path)
    return output_path

def generate_wrapped_images(stats):
    outputs = {}
    for key in TEMPLATES:
        out = f"output/{key}.png"
        render_template(key, stats, out)
        outputs[key] = out
    return outputs
