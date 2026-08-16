import asyncio
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.tools.files import _resolve_path, open_file, create_folder, list_drives, _get_user_folder
from app.agent.complexity import ComplexityDetector
from app.agent.evaluator import TaskEvaluator
from app.agent.models import TaskStep, EvaluationVerdict

class MockAI:
    async def generate_structured(self, messages, schema, model=None):
        return {"verdict": "SUCCESS", "reasoning": "Step succeeded"}
    async def generate_with_tools(self, messages, tools, model=None):
        return {}
    async def chat(self, messages, model=None):
        return "Done."

async def test_file_resolution_and_opening():
    print("=== 1. Testing Path & Category Resolution ===")
    user_home = os.path.expanduser("~")
    downloads_dir = _get_user_folder("Downloads")
    
    # Test folder aliases
    dl_path = _resolve_path("downloads")
    print("Downloads resolved:", dl_path)
    assert os.path.exists(dl_path)
    
    dt_path = _resolve_path("desktop")
    print("Desktop resolved:", dt_path)
    assert os.path.exists(dt_path)

    # Test drive resolution
    c_drive = _resolve_path("C:")
    print("C: Drive resolved:", c_drive)
    assert c_drive.upper() == "C:\\"

    # Test non-existing folder in Downloads (e.g. Downloads/pen fight)
    non_existing_dl = _resolve_path("Downloads/pen fight")
    print("Non-existing 'Downloads/pen fight' resolved to:", non_existing_dl)
    assert non_existing_dl == os.path.normpath(os.path.join(downloads_dir, "pen fight"))
    assert "JARVIS\\backend" not in non_existing_dl

    # Test natural creation queries
    natural_dl = _resolve_path("create a folder in Downloads folder called pen fight")
    print("Natural creation 'in Downloads' resolved to:", natural_dl)
    assert natural_dl == os.path.normpath(os.path.join(downloads_dir, "pen fight"))

    # Test category resolution in Downloads (e.g. image in download folder)
    resolved_img = _resolve_path("image in download folder")
    print("Resolved 'image in download folder':", resolved_img)
    assert os.path.exists(resolved_img)
    assert resolved_img.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))

    # Test natural phrasing for opening
    resolved_natural = _resolve_path("there is a image file in download folder can you open it")
    print("Resolved natural phrasing:", resolved_natural)
    assert os.path.exists(resolved_natural)

    # Test video in downloads
    resolved_video = _resolve_path("video in downloads")
    print("Resolved 'video in downloads':", resolved_video)
    assert os.path.exists(resolved_video)
    assert resolved_video.lower().endswith(('.mp4', '.mkv', '.mov', '.avi'))

    # Test direct filename
    resolved_direct = _resolve_path("Screenshot_20260813-043107.png")
    print("Resolved direct filename:", resolved_direct)
    assert os.path.exists(resolved_direct)
    assert "Screenshot_20260813-043107.png" in resolved_direct

    # Test relative path with folder prefix
    resolved_rel = _resolve_path("Downloads/Screenshot_20260813-043107.png")
    print("Resolved relative path:", resolved_rel)
    assert os.path.exists(resolved_rel)

    print("\n=== 2. Testing create_folder & open_file Logic ===")
    # Clean up misplaced backend/Downloads
    misplaced_backend_dl = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Downloads")
    if os.path.exists(misplaced_backend_dl):
        shutil.rmtree(misplaced_backend_dl, ignore_errors=True)

    # Test create_folder in real Downloads
    create_res = await create_folder("Downloads/pen fight")
    print("create_folder result:", create_res)
    real_created_dir = os.path.join(downloads_dir, "pen fight")
    assert os.path.exists(real_created_dir)
    assert "Successfully created folder 'pen fight'" in create_res

    # Test open_file on directory
    folder_res = await open_file("Downloads")
    print("open_file('Downloads') result:", folder_res)
    assert "Opened folder 'Downloads' in File Explorer." in folder_res

    # Test open_file on resolved image
    target_img = _resolve_path("image in download folder")
    assert os.path.exists(target_img)
    print(f"Target image verified on disk: {target_img}")

    print("\n=== 3. Testing Complexity Detection ===")
    ai = MockAI()
    detector = ComplexityDetector(ai)

    res1 = await detector.detect("there is a image file in download folder can you open it")
    print("Detection for 'there is a image file in download folder can you open it':", res1)
    assert res1 is False

    res2 = await detector.detect("create a folder in Downloads folder called pen fight")
    print("Detection for folder creation:", res2)
    assert res2 is False

    res3 = await detector.detect("Open Chrome")
    print("Detection for 'Open Chrome':", res3)
    assert res3 is False

    res4 = await detector.detect("Clean up my Downloads folder and group files by type, and then create a summary report.")
    print("Detection for complex multi-step:", res4)
    assert res4 is True

    print("\n=== 4. Testing Evaluator Deterministic Success ===")
    evaluator = TaskEvaluator(ai)
    step = TaskStep(id="step_1", description="Open image in downloads")
    eval_res = await evaluator.evaluate(step, "Opened 'Screenshot_20260813-043107.png' in default application.")
    print("Evaluator verdict:", eval_res.verdict, "-", eval_res.reasoning)
    assert eval_res.verdict == EvaluationVerdict.SUCCESS

    print("\n ALL FILE RESOLUTION AND OPENING TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_file_resolution_and_opening())
