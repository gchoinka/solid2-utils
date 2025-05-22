from pathlib import Path

from solid2_utils.render import RenderTask
from solid2 import cube

def test_render_task():
    rt:RenderTask = RenderTask(scad_object=cube(1,1,1), position=(0,0,0), filename=Path("./out.stl"))