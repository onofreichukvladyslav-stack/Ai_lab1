import io
import json
from datetime import datetime
import math
import anvil.media
import anvil.server
from PIL import Image, ImageDraw, ImageOps
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TASK1_DIR = BASE_DIR / "task1"
TASK2_DIR = BASE_DIR / "task2"
TASK3_DIR = BASE_DIR / "task3"

anvil.server.connect("server_W3KM6HL2BXISEBRLW7QTRGBN-CRMD5XCQMGANZSO6")

def extract_vector(img_bytes, rows=10, cols=10):
    rows = int(rows)
    cols = int(cols)
    orig_img = Image.open(io.BytesIO(img_bytes))
    img_gray = orig_img.convert("L")

    inverted = ImageOps.invert(img_gray)
    bbox = inverted.getbbox()
    if bbox:
        img_gray = img_gray.crop(bbox)

    w, h = img_gray.size
    max_dim = max(w, h)
    square_img = Image.new("L", (max_dim, max_dim), 255)
    square_img.paste(img_gray, ((max_dim - w) // 2, (max_dim - h) // 2))

    standard_img = square_img.resize((64, 64)) 
    pixels = standard_img.load()

    
    w, h = standard_img.size
    cell_w = w / cols
    cell_h = h / rows

    abs_vector = []
    for r in range(rows):
        for c in range(cols):
            x_start, x_end = int(c * cell_w), int((c + 1) * cell_w)
            y_start, y_end = int(r * cell_h), int((r + 1) * cell_h)
            
            dark_count = sum(
                1
                for y in range(y_start, y_end)
                for x in range(x_start, x_end)
                if pixels[x, y] < 128
            )
            abs_vector.append(dark_count)

    total = sum(abs_vector)
    norm_vector = (
        [val / total for val in abs_vector]
        if total > 0
        else [0.0] * len(abs_vector)
    )

    return {
        "orig_img": orig_img,
        "width": w,
        "height": h,
        "cell_w": cell_w,
        "cell_h": cell_h,
        "abs_vector": abs_vector,
        "norm_vector": norm_vector,
        "total_dark_pixels": total,
    }

@anvil.server.callable
def process_task1_image(file, rows=5, cols=4):
    img_bytes = file.get_bytes()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = file.name if file.name else "uploaded.bmp"

    saved_orig_filename = f"{timestamp}_{clean_name}"
    orig_file_path = TASK1_DIR / saved_orig_filename
    with open(orig_file_path, "wb") as f:
        f.write(img_bytes)

    data = extract_vector(img_bytes, rows, cols)
    abs_vector = data["abs_vector"]
    norm_vector = data["norm_vector"]

    grid_img = data["orig_img"].convert("RGB")
    draw = ImageDraw.Draw(grid_img)

    w, h = grid_img.size
    cell_w = w / cols
    cell_h = h / rows

    
    for c in range(1, cols):
        x = int(c * cell_w)
        draw.line([(x, 0), (x, h)], fill="red", width=2)

    for r in range(1, rows):
        y = int(r * cell_h)
        draw.line([(0, y), (w, y)], fill="red", width=2)


    grid_filename = f"grid_{saved_orig_filename}.png"
    grid_file_path = TASK1_DIR / grid_filename
    grid_img.save(grid_file_path, format="PNG")

    json_filename = f"result_{timestamp}.json"
    json_file_path = TASK1_DIR / json_filename

    result_data = {
        "timestamp": timestamp,       
        "abs_vector": abs_vector,
        "norm_vector": norm_vector,
    }

    with open(json_file_path, "w", encoding="utf-8") as jf:
        json.dump(result_data, jf, ensure_ascii=False, indent=4)

    out_buffer = io.BytesIO()
    grid_img.save(out_buffer, format="PNG")
    grid_media = anvil.BlobMedia("image/png", out_buffer.getvalue(), name=f"grid_{clean_name}.png")

    print("[Завдання №1] Обробка завершена для ", clean_name)
    print("Збережено картинку: ", orig_file_path.name)
    print("Збережено сітку: ", grid_file_path.name)
    print("Збережено вектори: ", json_file_path.name)

    return {
        "grid_image": grid_media,
        "abs_vector": abs_vector,
        "norm_vector": norm_vector,
    }

@anvil.server.callable
def get_available_templates():
    json_files = list(TASK2_DIR.glob("template_*.json"))
    classes = []
    for f in json_files:
        with open(f, "r", encoding="utf-8") as jf:
            data = json.load(jf)
            classes.append(data["class_name"])
    return sorted(classes)


@anvil.server.callable
def save_task2_template(file, class_name, selected_metric="euclidean", rows=10, cols=10):
    if not class_name or not class_name.strip():
        return {"status": "error", "message": "Задайте назву класу!"}

    class_name = class_name.strip()
    img_bytes = file.get_bytes()

    data = extract_vector(img_bytes, rows, cols)

    with open(TASK2_DIR / f"template_{class_name}.png", "wb") as f:
        f.write(img_bytes)

    json_data ={
        "class_name": class_name,
        "grid_size": {"rows": int(rows), "cols": int(cols)},
        "norm_vector": data["norm_vector"],
    }

    with open(TASK2_DIR / f"template_{class_name}.json", "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, ensure_ascii=False, indent=4)

    return {
        "status": "success",
        "message": f"Еталон '{class_name}' успішно збережено!",
    }

@anvil.server.callable
def classify_by_name(target_class_name, selected_metric="euclidean", rows=10, cols=10):
    if not target_class_name:
        return {"status": "error", "message": "Оберіть цифру зі списку!"}

  
    target_json_path = TASK2_DIR / f"template_{target_class_name}.json"
    if not target_json_path.exists():
        return {
            "status": "error",
            "message": f"Файл еталону {target_class_name}.json не знайдено!",
        }

    with open(target_json_path, "r", encoding="utf-8") as jf:
        target_data = json.load(jf)

    test_vec = target_data["norm_vector"]

  
    template_files = list(TASK2_DIR.glob("template_*.json"))
    distances = []

    for t_path in template_files:
        with open(t_path, "r", encoding="utf-8") as jf:
            t_data = json.load(jf)

        curr_class = t_data["class_name"]
        tmpl_vec = t_data["norm_vector"]

    
        if selected_metric == "euclidean":
            dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(test_vec, tmpl_vec)))
        elif selected_metric == "chebyshev":
            dist = max(abs(x - y) for x, y in zip(test_vec, tmpl_vec))
        elif selected_metric == "manhattan":
            dist = sum(abs(x - y) for x, y in zip(test_vec, tmpl_vec))
        else:
            dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(test_vec, tmpl_vec)))

        distances.append({"class_name": curr_class, "distance": round(dist, 5)})

  
    distances.sort(key=lambda item: item["distance"])

  
    predicted_class = distances[0]["class_name"]
    min_distance = distances[0]["distance"]

    return {
        "status": "success",
        "predicted_class": predicted_class,
        "min_distance": min_distance,
        "all_distances": distances,
    }

@anvil.server.callable
def get_template_image(target_class_name):
    if not target_class_name:
        return

    img_path = TASK2_DIR / f"{target_class_name}.bmp"
    if not img_path.exists():
        return None

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    return anvil.BlobMedia("image/png", img_bytes, name=f"{target_class_name}.png")

@anvil.server.callable
def train_and_classify_task3():
    if not TASK3_DIR.exists():
        return {"status": "error", "message": "Папка task3 не знайдена!"}
    
    classes = [d.name for d in TASK3_DIR.iterdir() if d.is_dir()]
    if not classes:
        return {
            "status": "error", 
            "message": (
                "У папці task3 немає підпапок з класами"
            )
        }
    
    clusters_stats = {}
    all_training_samples = []

    for class_name in classes:
        class_dir = TASK3_DIR / class_name
        img_files = list(class_dir.glob("*.bmp")) + list(class_dir.glob("*.jpg"))

        class_abs_vectors = []
        class_norm_vectors = []
        sample_details = []

        for img_path in img_files:
            with open(img_path, "rb") as f:
                img_bytes = f.read()

            features = extract_vector(img_bytes, rows=8, cols=8)

            class_abs_vectors.append(features["abs_vector"])
            class_norm_vectors.append(features["norm_vector"])

            sample_details.append({
                "filename": img_path.name,
                "abs_vector": features["abs_vector"],
                "norm_vector": [round(v, 4) for v in features["norm_vector"]]
            })

        if not class_norm_vectors:
            continue

        num_features = len(class_norm_vectors[0])
        mean_vector = [
            sum(vector[i] for vector in class_norm_vectors)
            / len(class_norm_vectors)
            for i in range(num_features)
        ]   

        min_vector = [
            min(vector[i] for vector in class_norm_vectors)
            for i in range(num_features)
        ]

        max_vector = [
            max(vector[i] for vector in class_norm_vectors)
            for i in range(num_features)
        ]

        clusters_stats[class_name] = {
            "samples_count": len(class_norm_vectors),
            "samples": sample_details,
            "mean_vector": [round(v, 4) for v in mean_vector],
            "min_vector": [round(v, 4) for v in min_vector],
            "max_vector": [round(v, 4) for v in max_vector]
        }

    return {"status": "success", "stats": clusters_stats}

@anvil.server.callable
def classify_unknown_image(file_obj, selected_method):
    if not file_obj:
        return {"status": "error", "message": "Не завантажено невідоме зображення!"}
    
    img_bytes = file_obj.get_bytes()
    test_features = extract_vector(img_bytes, rows=8, cols=8)
    test_norm = test_features["norm_vector"]

    train_data = train_and_classify_task3()
    if train_data.get("status") != "success":
        return train_data

    stats = train_data["stats"]
    best_class = None
    distances_or_scores = {}

    if selected_method == "centers":
        min_dist = float("inf")
        for class_name, data in stats.items():
            center = data["mean_vector"]
            dist = math.sqrt(sum((t - c) ** 2 for t, c in zip(test_norm, center)))
            distances_or_scores[class_name] = round(dist, 5)
            if dist < min_dist:
                min_dist = dist
                best_class = class_name

    elif selected_method == "orthogonal":
        matching_classes = []
        for class_name, data in stats.items():
            min_v = data["min_vector"]
            max_v = data["max_vector"]

            inside = all(min_v[i] <= test_norm[i] <= max_v[i] for i in range(len(test_norm)))
            if inside:
                matching_classes.append(class_name)

        if len(matching_classes) == 1:
            best_class = matching_classes[0]
            distances_or_scores = {
                c: "Увійшов в область" for c in matching_classes
            }
        else:
            min_dist = float("inf")
            for class_name, data in stats.items():
                min_v = data["min_vector"]
                max_v = data["max_vector"]
                mid_v = [(a + b) / 2 for a, b in zip(min_v, max_v)]
                dist = math.sqrt(sum((t - m) ** 2 for t, m in zip(test_norm, mid_v)))
                distances_or_scores[class_name] = round(dist, 5)
                if dist < min_dist:
                    min_dist = dist
                    best_class = class_name

    return {
        "status": "success",
        "predicted_class": best_class,
        "abs_vector": test_features["abs_vector"],
        "norm_vector": [round(v, 4) for v in test_norm],
        "metrics": distances_or_scores
    }


def scan_and_register_bmp_templates(rows=10, cols=10):
    bmp_files = list(TASK2_DIR.glob("*.bmp"))

    for bmp_path in bmp_files:
        class_name = bmp_path.stem.replace("template_", "")
        json_file_path = TASK2_DIR / f"template_{class_name}.json"

        if not json_file_path.exists():
            with open(bmp_path, "rb") as f:
                img_bytes = f.read()
            
            data = extract_vector(img_bytes, rows, cols)

            json_data = {
                "class_name": class_name,
                "grid_size": {"rows": int(rows), "cols": int(cols)},
                "norm_vector": data["norm_vector"]
            }

            with open(json_file_path, "w", encoding="utf-8") as jf:
                json.dump(json_data, jf, ensure_ascii=False, indent=4)

            print(f"[Завдання 2] Автоматично згенеровано еталон для: {bmp_path.name}")


if __name__ == "__main__":
    scan_and_register_bmp_templates(rows=10, cols=10)
    print("Сервер запущено.")
    anvil.server.wait_forever()