"""
Main Agent — Lab 14: AI Evaluation & Benchmarking
===================================================
RAG Agent mô phỏng hệ thống hỗ trợ khách hàng.
Hỗ trợ 2 phiên bản (V1 Base & V2 Optimized) để test Regression.

Agent sử dụng Knowledge Base giống với synthetic_gen.py để mô phỏng
quy trình Retrieval → Generation thực tế.
"""

import asyncio
import random
import hashlib
from typing import List, Dict


# Knowledge Base (giống data/synthetic_gen.py)
KNOWLEDGE_BASE = {
    "doc_001": "Chính sách bảo hành: Sản phẩm được bảo hành 12 tháng kể từ ngày mua. Khách hàng cần giữ hóa đơn để được bảo hành. Các trường hợp không được bảo hành: rơi vỡ, ngấm nước, tự ý tháo lắp.",
    "doc_002": "Hướng dẫn đổi mật khẩu: Bước 1: Đăng nhập vào tài khoản. Bước 2: Vào Cài đặt > Bảo mật. Bước 3: Nhấn 'Đổi mật khẩu'. Bước 4: Nhập mật khẩu cũ và mật khẩu mới (tối thiểu 8 ký tự, bao gồm chữ hoa, chữ thường, số). Bước 5: Nhấn 'Lưu'.",
    "doc_003": "Chính sách hoàn tiền: Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày kể từ ngày mua nếu sản phẩm bị lỗi kỹ thuật từ nhà sản xuất. Thời gian xử lý hoàn tiền: 5-7 ngày làm việc. Phí xử lý: 0 đồng.",
    "doc_004": "Bảng giá dịch vụ 2024: Gói Basic: 99.000đ/tháng (5GB storage, 100 API calls/ngày). Gói Pro: 299.000đ/tháng (50GB storage, 1000 API calls/ngày, hỗ trợ 24/7). Gói Enterprise: Liên hệ (unlimited storage, unlimited API calls, SLA 99.9%).",
    "doc_005": "Quy trình khiếu nại: Bước 1: Gửi email đến support@company.com hoặc gọi hotline 1900-xxxx. Bước 2: Cung cấp mã đơn hàng và mô tả vấn đề. Bước 3: Đội ngũ sẽ phản hồi trong 24h. Bước 4: Xử lý trong 3-5 ngày làm việc.",
    "doc_006": "Chính sách bảo mật dữ liệu: Dữ liệu khách hàng được mã hóa AES-256. Không chia sẻ dữ liệu với bên thứ ba mà không có sự đồng ý. Tuân thủ GDPR và PDPA.",
    "doc_007": "Hướng dẫn tích hợp API: Endpoint chính: https://api.company.com/v2. Authentication: Bearer Token. Rate limit: 100 requests/phút cho gói Basic, 1000 requests/phút cho gói Pro.",
    "doc_008": "Chính sách nhân sự: Nhân viên chính thức được nghỉ phép 12 ngày/năm. Nghỉ ốm có lương: 30 ngày/năm. Thời gian làm việc: 8:00 - 17:00, Thứ 2 - Thứ 6. Làm thêm giờ được trả 150% lương cơ bản.",
    "doc_009": "Hướng dẫn cài đặt phần mềm: Yêu cầu hệ thống: Windows 10/11 hoặc macOS 12+, RAM tối thiểu 8GB, ổ cứng trống 2GB.",
    "doc_010": "FAQ: Q: Tôi quên mật khẩu thì làm sao? A: Vào trang đăng nhập, nhấn 'Quên mật khẩu'. Q: Làm sao để nâng cấp gói? A: Vào Cài đặt > Gói dịch vụ > Nâng cấp.",
    "doc_011": "Chính sách đối tác: Đối tác được hưởng chiết khấu 15-30% tùy cấp bậc. Silver: >= 50 triệu/tháng. Gold: >= 200 triệu/tháng. Platinum: >= 500 triệu/tháng.",
    "doc_012": "Hướng dẫn sử dụng Dashboard: Tab Overview, Tab Analytics, Tab Settings.",
}

DOC_IDS = list(KNOWLEDGE_BASE.keys())


class MainAgent:
    """
    RAG Agent mô phỏng với 2 phiên bản:
    - V1 (Base): Retrieval đơn giản, đôi khi trả về sai context
    - V2 (Optimized): Retrieval cải tiến, ít sai hơn, phản hồi chính xác hơn
    """

    def __init__(self, version: str = "v1"):
        self.version = version
        self.name = f"SupportAgent-{version}"
        self.total_tokens = 0
        self.total_cost = 0.0

    def _simple_retrieval(self, question: str) -> List[str]:
        """
        Mô phỏng Retrieval stage.
        V1: accuracy ~70% (30% chance trả sai doc)
        V2: accuracy ~90%
        """
        seed = int(hashlib.md5(question.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        # Keyword matching đơn giản
        keyword_map = {
            "bảo hành": ["doc_001"],
            "mật khẩu": ["doc_002", "doc_010"],
            "hoàn tiền": ["doc_003"],
            "giá": ["doc_004"],
            "gói": ["doc_004", "doc_010"],
            "khiếu nại": ["doc_005"],
            "bảo mật": ["doc_006"],
            "api": ["doc_007"],
            "nhân sự": ["doc_008"],
            "nghỉ phép": ["doc_008"],
            "lương": ["doc_008"],
            "cài đặt": ["doc_009"],
            "phần mềm": ["doc_009"],
            "đối tác": ["doc_011"],
            "chiết khấu": ["doc_011"],
            "dashboard": ["doc_012"],
        }

        matched = []
        q_lower = question.lower()
        for keyword, doc_ids in keyword_map.items():
            if keyword in q_lower:
                matched.extend(doc_ids)

        # Loại bỏ trùng lặp
        matched = list(dict.fromkeys(matched))

        if not matched:
            # Không match → trả random docs
            matched = rng.sample(DOC_IDS, min(3, len(DOC_IDS)))

        # V1: 30% chance thêm noise (sai doc)
        # V2: 10% chance thêm noise
        noise_rate = 0.30 if self.version == "v1" else 0.10
        if rng.random() < noise_rate:
            noise_doc = rng.choice(DOC_IDS)
            matched.insert(0, noise_doc)  # Đặt sai doc lên đầu

        # Thêm padding docs
        remaining = [d for d in DOC_IDS if d not in matched]
        rng.shuffle(remaining)
        matched.extend(remaining[:5 - len(matched)])

        return matched[:5]

    async def query(self, question: str) -> Dict:
        """
        Mô phỏng quy trình RAG:
        1. Retrieval: Tìm kiếm context liên quan
        2. Generation: Sinh câu trả lời
        """
        # Giả lập latency
        latency = random.uniform(0.05, 0.15) if self.version == "v2" else random.uniform(0.1, 0.3)
        await asyncio.sleep(latency)

        # 1. Retrieval
        retrieved_ids = self._simple_retrieval(question)
        contexts = [KNOWLEDGE_BASE[did] for did in retrieved_ids if did in KNOWLEDGE_BASE]

        # 2. Generation
        tokens = random.randint(100, 300) if self.version == "v1" else random.randint(80, 200)
        self.total_tokens += tokens
        cost_per_1k = 0.005  # $0.005 per 1K tokens
        cost = (tokens / 1000) * cost_per_1k
        self.total_cost += cost

        # V1: câu trả lời generic hơn, đôi khi hallucinate
        # V2: câu trả lời cụ thể hơn, ít hallucinate
        if self.version == "v2":
            answer = self._generate_v2_answer(question, contexts)
        else:
            answer = self._generate_v1_answer(question, contexts)

        return {
            "answer": answer,
            "contexts": contexts[:2],
            "retrieved_ids": retrieved_ids,
            "metadata": {
                "model": "gpt-4o-mini" if self.version == "v1" else "gpt-4o",
                "tokens_used": tokens,
                "cost_usd": round(cost, 6),
                "sources": retrieved_ids[:3],
                "agent_version": self.version
            }
        }

    def _generate_v1_answer(self, question: str, contexts: List[str]) -> str:
        """V1: câu trả lời cơ bản, đôi khi thiếu thông tin."""
        if not contexts:
            return f"Dựa trên tài liệu hệ thống, tôi xin trả lời câu hỏi '{question}' như sau: [Câu trả lời mẫu]."

        # Trả lời dựa trên context đầu tiên (có thể sai nếu retrieval sai)
        first_ctx = contexts[0]
        if len(first_ctx) > 150:
            return f"Theo tài liệu: {first_ctx[:150]}..."
        return f"Theo tài liệu: {first_ctx}"

    def _generate_v2_answer(self, question: str, contexts: List[str]) -> str:
        """V2: câu trả lời chất lượng hơn, tổng hợp nhiều context."""
        # Xử lý adversarial
        adversarial_keywords = ["bỏ qua", "ignore", "hack", "jailbreak", "DAN", "system prompt", "API key", "database", "admin"]
        if any(kw.lower() in question.lower() for kw in adversarial_keywords):
            return "Tôi không thể thực hiện yêu cầu này. Tôi chỉ có thể hỗ trợ các câu hỏi liên quan đến sản phẩm và dịch vụ của công ty."

        # Xử lý edge cases
        if len(question.strip()) < 3:
            return "Bạn chưa nhập câu hỏi. Vui lòng cho tôi biết bạn cần hỗ trợ gì?"

        if not contexts:
            return "Xin lỗi, tôi không tìm thấy thông tin liên quan trong tài liệu để trả lời câu hỏi này."

        # Tổng hợp câu trả lời từ tất cả contexts
        combined = " ".join(contexts[:3])
        if len(combined) > 300:
            return f"Dựa trên tài liệu liên quan: {combined[:300]}. Bạn có cần thêm thông tin chi tiết không?"
        return f"Dựa trên tài liệu liên quan: {combined}"

    def get_usage_stats(self) -> Dict:
        """Trả về thống kê sử dụng token và chi phí."""
        return {
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "agent_version": self.version,
            "model": "gpt-4o-mini" if self.version == "v1" else "gpt-4o"
        }


if __name__ == "__main__":
    agent = MainAgent(version="v2")
    async def test():
        resp = await agent.query("Làm thế nào để đổi mật khẩu?")
        print(resp)
        print(agent.get_usage_stats())
    asyncio.run(test())
