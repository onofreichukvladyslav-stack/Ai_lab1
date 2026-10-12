from anvil import *
import anvil.server

from ..task1 import task1
from ..task2 import task2
from ..task3 import task3
from ._anvil_designer import Form1Template

class Form1(Form1Template):
  def __init__(self, **properties):
    super().__init__(**properties)

  @handle("btn_task1", "click")
  def btn_task1_click(self, **event_args):
    self.show_task1()

  @handle("btn_task2", "click")
  def btn_task2_click(self, **event_args):
    self.show_task2()

  @handle("btn_task3", "click")
  def btn_task3_click(self, **event_args):
    self.show_task3()

  def show_task1(self):
    self.content_panel.clear()
    self.content_panel.add_component(task1())

  def show_task2(self):
    self.content_panel.clear()
    self.content_panel.add_component(task2())

  def show_task3(self):
    self.content_panel.clear()
    self.content_panel.add_component(task3())

  
