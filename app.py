import ast
import json
import os
import operator
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
NOTES_FILE = DATA_DIR / "notes.json"

app = FastAPI(title="NEURAL AGENT", version="1.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
client = OpenAI(api_key=API_KEY) if API_KEY else None

SYSTEM_PROMPT = """
Bạn là NEURAL AGENT, trợ lý AI tiếng Việt thân thiện, có năng lực lập kế hoạch.
- Trả lời rõ ràng, hữu ích, trung thực; nói rõ khi chưa chắc chắn.
- Với nhiệm vụ nhiều bước, hãy chia thành các bước ngắn và kiểm tra kết quả.
- Bạn có thể dùng công cụ tính toán, lưu ghi chú và tìm kiếm web khi cần.
- Không tuyên bố đã thực hiện hành động nếu công cụ chưa xác nhận thành công.
- Không yêu cầu người dùng gửi khóa API, mật khẩu hoặc dữ liệu bí mật vào cuộc trò chuyện.
- Khi dùng thông tin từ web, hãy nêu nguồn nếu kết quả tìm kiếm cung cấp nguồn.
"""

TOOLS = [
    {"type": "web_search"},
    {
        "type": "function",
        "name": "calculate",
        "description": "Tính biểu thức số học cơ bản. Chỉ dùng số và phép toán + - * / // % ** cùng ngoặc.",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "save_note",
        "description": "Lưu một ghi chú văn bản vào bộ nhớ cục bộ của ứng dụng.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["title", "content"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    history: list[dict[str, str]] = Field(default_factory=list, max_length=30)

class ChatResponse(BaseModel):
    reply: str
    model: str

def safe_calculate(expression: str) -> str:
    allowed_ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
        ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos,
    }
    def evaluate(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in allowed_ops:
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("Số mũ quá lớn.")
            result = allowed_ops[type(node.op)](left, right)
            if isinstance(result, (int, float)) and abs(result) > 1e100:
                raise ValueError("Kết quả vượt giới hạn.")
            return result
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_ops:
            return allowed_ops[type(node.op)](evaluate(node.operand))
        raise ValueError("Biểu thức chứa cú pháp không được hỗ trợ.")
    try:
        tree = ast.parse(expression, mode="eval")
        return str(evaluate(tree))
    except Exception as exc:
        return f"Không thể tính biểu thức: {exc}"

def save_note(title: str, content: str) -> str:
    try:
        notes = json.loads(NOTES_FILE.read_text(encoding="utf-8")) if NOTES_FILE.exists() else []
        note = {"title": title[:160], "content": content[:5000]}
        notes.append(note)
        NOTES_FILE.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
        return f"Đã lưu ghi chú '{note['title']}'."
    except Exception as exc:
        return f"Lưu ghi chú thất bại: {exc}"

def execute_tool(name: str, arguments: dict[str, Any]) -> str:
    if name == "calculate":
        return safe_calculate(arguments["expression"])
    if name == "save_note":
        return save_note(arguments["title"], arguments["content"])
    return "Công cụ không được hỗ trợ."

@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/api/health")
def health():
    return {"ok": True, "api_configured": bool(API_KEY), "model": MODEL}

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Chưa cấu hình OPENAI_API_KEY. Hãy tạo file .env từ .env.example và thêm API key."
        )
    history = []
    for item in req.history[-20:]:
        role = item.get("role")
        content = item.get("content", "")
        if role in ("user", "assistant") and isinstance(content, str):
            history.append({"role": role, "content": content[:8000]})
    history.append({"role": "user", "content": req.message})

    try:
        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            input=history,
            tools=TOOLS,
            max_output_tokens=1800,
        )
        # Agent tool loop: the model can request tools, the backend runs them,
        # and tool results are sent back for a final response.
        for _ in range(5):
            calls = [item for item in response.output if getattr(item, "type", "") == "function_call"]
            if not calls:
                break
            outputs = []
            for call in calls:
                try:
                    args = json.loads(call.arguments)
                    result = execute_tool(call.name, args)
                except Exception as exc:
                    result = f"Công cụ gặp lỗi: {exc}"
                outputs.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": str(result),
                })
            response = client.responses.create(
                model=MODEL,
                instructions=SYSTEM_PROMPT,
                previous_response_id=response.id,
                input=outputs,
                tools=TOOLS,
                max_output_tokens=1800,
            )
        reply = (response.output_text or "").strip()
        if not reply:
            reply = "Tôi chưa tạo được câu trả lời. Bạn hãy thử diễn đạt yêu cầu theo cách khác."
        return ChatResponse(reply=reply, model=MODEL)
    except Exception as exc:
        # Keep raw provider details out of the UI; detailed logs can be added later.
        print(f"OpenAI request failed: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Không thể kết nối AI lúc này. Hãy kiểm tra API key, tên model, kết nối mạng và hạn mức API."
        )
