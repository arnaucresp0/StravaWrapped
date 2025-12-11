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
    #TODO: DEFINE THE TEXT POSITIONS...
    "random_data_cat": {
        "file": "assets/wrapped_cat/input/random_data_cat.png",
        "fields": {
            "photo_count":  {"pos": (200, 620), "size": 80, "color": "white"},
            "kudos_count":    {"pos": (200, 740), "size": 80, "color": "white"},
            "comment_count":       {"pos": (200, 880), "size": 80, "color": "white"},
            "social_ratio":   {"pos": (200, 1030), "size": 80, "color": "white"},
            "train_time":    {"pos": (200, 1170), "size": 80, "color": "white"},
        }
    },
    #TODO: DEFINE THE TEXT POSITIONS...
    "total_elevation_cat": {
        "file": "assets/wrapped_cat/input/total_elevation_cat.png",
        "fields": {
            "total_elevation":  {"pos": (200, 620), "size": 80, "color": "white"},
            "everest_count":    {"pos": (200, 740), "size": 80, "color": "white"},
        }
    },
    #TODO: DEFINE THE TEXT POSITIONS...
    "total_km_cat": {
        "file": "assets/wrapped_cat/input/total_elevation_cat.png",
        "fields": {
            "total_distance":  {"pos": (200, 620), "size": 80, "color": "white"},
            "distance_comp":    {"pos": (200, 740), "size": 80, "color": "white"},
        }
    },
    #TODO: DEFINE THE TEXT POSITIONS...
    "total_time_cat": {
        "file": "assets/wrapped_cat/input/total_time_cat.png",
        "fields": {
            "total_time_minutes":  {"pos": (200, 620), "size": 80, "color": "white"},
            "total_time_days":    {"pos": (200, 740), "size": 80, "color": "white"},
        }
    },
    #TODO: DEFINE THE TEXT POSITIONS...
    "total_pr_cat": {
        "file": "assets/wrapped_cat/input/total_pr_cat.png",
        "fields": {
            "total_pr":  {"pos": (200, 620), "size": 80, "color": "white"},
        }
    },
    #TODO: DEFINE THE TEXT POSITIONS...
    "total_watts_cat": {
        "file": "assets/wrapped_cat/input/total_watts_cat.png",
        "fields": {
            "total_kWh":  {"pos": (200, 620), "size": 80, "color": "white"},
            "total_house_power":    {"pos": (200, 740), "size": 80, "color": "white"},
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
