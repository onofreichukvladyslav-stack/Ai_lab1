from ._anvil_designer import task1Template
from anvil import *
import anvil.server


class task1(task1Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    super().__init__(**properties)

  @handle("picture_loader", "change")
  def picture_loader_change(self, file, **event_args):
    """This method is called when a new file is loaded into this FileLoader"""
    if file:
      rows = int(self.text_box_rows.text or 5)
      cols = int(self.text_box_cols.text or 4)

      result = anvil.server.call("process_task1_image", file, rows, cols)
      self.image_1.source = result["grid_image"]

      abs_formatted = "; ".join(map(str, result["abs_vector"]))
      self.text_area_abs.text = f"X = ({abs_formatted})"

      norm_formatted = "; ".join(f"{v:.4f}" for v in result["norm_vector"])
      self.text_area_norm.text = f"X^ = ({norm_formatted})"
