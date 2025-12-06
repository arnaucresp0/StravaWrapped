from PIL import Image, ImageDraw, ImageFont
import os

TEMPLATE_DIR = "assets/templates"
OUTPUT_DIR = "assets/output"

def generate_wrapped_image(stats, template_name="wrapped_base.png"):
    """
    stats: dict amb totes les dades calculades
    template_name: la imatge base sobre la qual dibuixarem
    """

    # Carreguem plantilla
    template_path = os.path.join(TEMPLATE_DIR, template_name)
    img = Image.open(template_path).convert("RGBA")

    draw = ImageDraw.Draw(img)

    # Carreguem el tipus de lletra — en pots posar el que vulguis
    font_path = "assets/fonts/Inter-Bold.ttf"
    font_big = ImageFont.truetype(font_path, 64)
    font_small = ImageFont.truetype(font_path, 40)

    # EXEMPLE POSICIONS (les canviarem segons necessitis)
    positions = {
        "total_distance": (120, 300),
        "total_elevation": (120, 420),
        "dominant_sport": (120, 540),
        "total_time": (120, 660),
        "total_energy": (120, 780),
        "total_activities": (120, 900)
    }

    # Escritura de dades
    draw.text(
        positions["total_distance"],
        f"{stats['total_distance_km']} km",
        font=font_big,
        fill="white",
    )

    draw.text(
        positions["total_elevation"],
        f"{stats['total_elevation_m']} m",
        font=font_big,
        fill="white",
    )

    draw.text(
        positions["dominant_sport"],
        stats["dominant_sport"],
        font=font_big,
        fill="white",
    )

    draw.text(
        positions["total_time"],
        f"{stats['total_time_days']} dies",
        font=font_big,
        fill="white",
    )

    draw.text(
        positions["total_energy"],
        f"{stats['total_energy_kwh']} kWh",
        font=font_big,
        fill="white",
    )

    draw.text(
        positions["total_activities"],
        f"{stats['activities_last_year']} activitats",
        font=font_big,
        fill="white",
    )

    # Guardem resultat
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "wrapped_output.png")
    img.save(output_path)

    return output_path
