from ._anvil_designer import task3Template
from anvil import *
import anvil.server


class task3(task3Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    super().__init__(**properties)

    # Any code you write here will run before the form opens.
    self.drop_down_method.items = [
      ("1) Геометричні центри кластерів", "centers"),
      ("2) Ортогональні області (Мін-Макс)", "orthogonal"),
    ]

 
  def run_classification(self):
    file = self.file_loader_unknown.file
    if not file:
      return

    selected_method = self.drop_down_method.selected_value
    if not selected_method:
      selected_method = "centers"

    res = anvil.server.call("classify_unknown_image", file, selected_method)

    if res.get("status") == "success":
      lines = [
        f"РЕЗУЛЬТАТ КЛАСИФІКАЦІЇ: Клас -> {res['predicted_class']}",
        f"Обраний метод: {selected_method.upper()}",
        "---",
        f"Нормований вектор ознак: {res['norm_vector']}",
        "---",
        f"Показники для класів: {res['metrics']}",
      ]
      self.text_area_results.text = "\n".join(lines)
    else:
      alert(res.get("message", "Помилка класифікації."))

  @handle("file_loader_unknown", "change")
  def file_loader_unknown_change(self, file, **event_args):
    if file:
      self.image_unknown.source = file
      self.run_classification()

  @handle("drop_down_method", "change")
  def drop_down_method_change(self, **event_args):
    self.run_classification()
  