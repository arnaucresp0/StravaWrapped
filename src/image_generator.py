from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import time
import base64
import io


TEMPLATE_DIR = "assets/wrapped_cat/input"
STORAGE_ROOT = Path("storage")

SCALE = 1  # Trying this to improve text quality
FONT_PATH = os.path.join(
    "assets", "fonts", "Montserrat_Arabic_Regular", "Montserrat_Arabic_Regular.ttf"
)
TEXT_SIZE = 48
TEXT_COLOR = "black"

TEMPLATES = {
    # Done!
    "year_overall_cat": {
        "file": "assets/wrapped_cat/input/year_overall_cat.png",
        "fields": {
            "activities_last_year":  {"pos": (720, 860), "size": TEXT_SIZE, "color": TEXT_COLOR},
            "total_elevation_m":    {"pos": (800, 1045), "size": TEXT_SIZE, "color": TEXT_COLOR},
            "dominant_sport":       {"pos": (825, 1230), "size": TEXT_SIZE, "color": TEXT_COLOR},
            "total_time_minutes":   {"pos": (720, 1410), "size": TEXT_SIZE, "color": TEXT_COLOR},
            "total_distance_km":    {"pos": (515, 1600), "size": TEXT_SIZE, "color": TEXT_COLOR},
        }
    }, 
    # Done! (pending to review activity name pos)
    "liked_activity": {
        "file": "assets/wrapped_cat/input/liked_activity_cat.png",
        "fields": {
            "activity_name":  {"pos": (150, 1280), "size": 35, "color": TEXT_COLOR},
            "activity_kudos": {"pos": (515, 1390), "size": 85, "color": TEXT_COLOR},
        }
    },
    # Done!
    "random_data_cat": {
        "file": "assets/wrapped_cat/input/random_data_cat.png",
        "fields": {
            "photo_count":  {"pos": (730, 882), "size": 44, "color": TEXT_COLOR},
            "kudos_count":    {"pos": (680, 1035), "size": 44, "color": TEXT_COLOR},
            "comment_count":       {"pos": (810, 1180), "size": 44, "color": TEXT_COLOR},
            "train_time":    {"pos": (600, 1333), "size": 44, "color": TEXT_COLOR},
            "total_mates":      {"pos": (735, 1485), "size": 44, "color": TEXT_COLOR},
            "social_ratio":   {"pos": (440, 1637), "size": 44, "color": TEXT_COLOR},
        }
    },
    # Done!
    "total_elevation_cat": {
        "file": "assets/wrapped_cat/input/total_elevation_cat.png",
        "fields": {
            "total_elevation_m":  {"pos": (460, 1225), "size": 60, "color": TEXT_COLOR},
            "everest_count":    {"pos": (510, 1625), "size": 60, "color": TEXT_COLOR},
        }
    },
    # Done!
    "total_km_cat": {
        "file": "assets/wrapped_cat/input/total_km_cat.png",
        "fields": {
            "total_distance_km":  {"pos": (430, 1065), "size": 60, "color": TEXT_COLOR},
            "distance_comp":    {"pos": (250, 1540), "size": 60, "color": TEXT_COLOR},
        }
    },
    # Done!
    "total_time_cat": {
        "file": "assets/wrapped_cat/input/total_time_cat.png",
        "fields": {
            "total_time_minutes":  {"pos": (440, 1270), "size": 60, "color": TEXT_COLOR},
            "total_time_days":    {"pos": (465, 1580), "size": 60, "color": TEXT_COLOR},
        }
    },
    # Done!
    "total_pr_cat": {
        "file": "assets/wrapped_cat/input/total_pr_cat.png",
        "fields": {
            "total_pr":  {"pos": (485, 1040), "size": 80, "color": TEXT_COLOR},
        }
    },
    # Done!
    "total_watts_cat": {
        "file": "assets/wrapped_cat/input/total_watts_cat.png",
        "fields": {
            "total_kWh":  {"pos": (440, 920), "size": 60, "color": TEXT_COLOR},
            "total_house_power":    {"pos": (450, 1350), "size": 60, "color": TEXT_COLOR},
        }
    },
    # Done!
    "multi_sport_cat": {
        "file": "assets/wrapped_cat/input/multi_sport_cat.png",
        "fields": {
            "total_sports":  {"pos": (535, 850), "size": 80, "color": TEXT_COLOR},
            "main_sport":    {"pos": (350, 1260), "size": 60, "color": TEXT_COLOR},
            "secondary_sport": {"pos": (350, 1360), "size": 60, "color": TEXT_COLOR},
            "third_sport":  {"pos": (350, 1460), "size": 60, "color": TEXT_COLOR},
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
    "train_time":           lambda s: str(s["train_time"]),
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
        return ImageFont.truetype(FONT_PATH, size)
    except IOError as e:
        print(f"[FONT ERROR] {e}")
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


def generate_wrapped_images_to_disk(stats: dict, athlete_id: int):  # Nom canviat
    output_dir = get_user_output_dir(athlete_id)
    outputs = []
    for template_name in TEMPLATES:
        output_path = output_dir / f"{template_name}.png"
        render_template(template_name, stats, str(output_path))
        outputs.append(str(output_path))
    return outputs


def get_user_output_dir(athlete_id: int) -> Path:
    base = STORAGE_ROOT / "generated" / str(athlete_id) / "wrapped"
    base.mkdir(parents=True, exist_ok=True)
    return base

def generate_wrapped_images_in_memory(stats: dict, athlete_id: int):
    """Genera les imatges del Wrapped i les retorna com a llista d'objectes PIL.Image."""
    images_pil = []
    
    for template_name in TEMPLATES:
        template = TEMPLATES[template_name]
        # Obrir la plantilla (imatge de fons)
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
            scaled_pos = (cfg["pos"][0] * SCALE, cfg["pos"][1] * SCALE)
            draw.text(scaled_pos, text, fill=cfg["color"], font=font)

        # Afegir l'objecte d'imatge a la llista (NO guardar a disc)
        images_pil.append(img)
    
    return images_pil

def generate_wrapped_images_base64(stats: dict, athlete_id: int):
    """
    Genera les imatges del Wrapped i les retorna com a llista de cadenes Base64 (JPEG).
    """
    start_total = time.time()
    images_base64 = []
    
    print(f"🖼️  [IMAGE_GEN] Iniciant generació per athlete {athlete_id}")
    
    for i, template_name in enumerate(TEMPLATES.keys()):
        img_start = time.time()
        template = TEMPLATES[template_name]
        
        # 1. Obrir plantilla i renderitzar text
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
            scaled_pos = (cfg["pos"][0] * SCALE, cfg["pos"][1] * SCALE)
            draw.text(scaled_pos, text, fill=cfg["color"], font=font)
        
        # 2. Convertir a JPEG (més eficient que PNG)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Si té transparència, posar fons blanc
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                bg.paste(img, mask=img.split()[-1])
            else:
                bg.paste(img)
            img = bg
        
        # Guardar com JPEG
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=75, optimize=True)
        img_byte_arr.seek(0)
        
        # 3. Convertir a Base64
        file_bytes = img_byte_arr.read()
        file_size_kb = len(file_bytes) // 1024
        
        encoded_string = base64.b64encode(file_bytes).decode('utf-8')
        images_base64.append(encoded_string)
        
        # 4. Alliberar memòria
        img.close()
        
        img_elapsed = time.time() - img_start
        print(f"   🖼️  [IMAGE_GEN] {template_name}: {file_size_kb}KB en {img_elapsed:.1f}s")
    
    total_time = time.time() - start_total
    print(f"✅ [IMAGE_GEN] {len(images_base64)} imatges generades en {total_time:.1f}s")
    
    return images_base64