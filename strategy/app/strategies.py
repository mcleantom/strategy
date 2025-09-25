from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

strategies_router = APIRouter(tags=["Strategies"])


STRATEGIES_DIR = Path(__file__).parent.parent.parent / "strategies"
STRATEGIES_DIR.mkdir(exist_ok=True)
TEMPLATE_FILE = Path(__file__).parent.parent / "strategies" / "template_strategy.py"


@strategies_router.get("/strategies")
def get_strategies() -> list[str]:
    return [str(x.with_suffix("").name) for x in STRATEGIES_DIR.glob("*") if x.suffix == ".py"]


class CreateStrategyRequest(BaseModel):
    name: str


@strategies_router.post("/strategy")
def create_strategy(create_strategy_request: CreateStrategyRequest):
    new_strategy = (STRATEGIES_DIR / create_strategy_request.name).with_suffix(".py")
    if new_strategy.exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Strategy with the same name already exists")
    with new_strategy.open("w") as f:
        f.write(TEMPLATE_FILE.read_text())


@strategies_router.get("/strategy/{name}")
def get_strategy(name: str) -> str:
    strategy_path = (STRATEGIES_DIR / name).with_suffix(".py")
    if not strategy_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy doesnt exist")
    return strategy_path.read_text()


@strategies_router.put("/strategy/{name}")
async def update_strategy(name: str, file: UploadFile = File(...)):
    strategy_path = (STRATEGIES_DIR / name).with_suffix(".py")
    if not strategy_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy doesnt exist")
    content = await file.read()
    with strategy_path.open("wb") as f:
        f.write(content)
