from ._anvil_designer import task2Template
from anvil import *
import anvil.server


class task2(task2Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    super().__init__(**properties)

    self.drop_down_metric.items = [
      ("1) Евклідова відстань (d1)", "euclidean"),
      ("2) Норма Чебишева (d3)", "chebyshev"),
      ("3) Манхетенська відстань(d2)", "manhattan")
    ]

    self.refresh_templates_list()

  def refresh_templates_list(self):
    try:
      templates = anvil.server.call("get_available_templates")
      if templates:
        self.drop_down_template.items = [(f"Цифра: {t}", t) for t in templates]
      else:
        self.drop_down_template.items = [("Немає збережених еталонів", None)]
    except Exception as e:
      print("Помилка еталонів: ", e)

  @handle("drop_down_template", "change")
  def drop_down_template_change(self, **event_args):
    self.run_classification()

  @handle("drop_down_metric", "change")
  def drop_down_metric_change(self, **event_args):
    self.run_classification()
  
  def run_classification(self):
    selected_template = self.drop_down_template.selected_value
    selected_formula = self.drop_down_metric.selected_value

    if not selected_template:
      return

    template_media = anvil.server.call("get_template_image", selected_template)

    if template_media:
      self.image_template.source = (template_media)

    rows = int(5)
    cols = int(4)

    res = anvil.server.call("classify_by_name", selected_template, selected_formula, rows, cols)

    if res.get("status") == "success":
      self.lbl_result.text = (f"РЕЗУЛЬТАТ КЛАСИФІКАЦІЇ: {res['predicted_class']}")

      lines = [f"Обрана цифра: {selected_template} | Формула: {selected_formula.upper()}", "---"]
      for item in res["all_distances"]:
        marker = (
          " <-- Обрана цифра"
          if item["class_name"] == selected_template
          else ""
        )
        lines.append(f"Клас '{item['class_name']}': d = {item['distance']:.5f}{marker}")

      self.text_area_details.text = "\n".join(lines)
    else:
      alert(res.get("message", "Помилка розпізнавання"))