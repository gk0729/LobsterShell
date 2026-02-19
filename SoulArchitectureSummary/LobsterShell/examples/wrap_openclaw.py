"""
示例: 包裝 OpenClaw

展示如何用 LobsterShell 安全地包裝 OpenClaw Agent
"""

import asyncio
from lobstershell import LobsterShell, ModeConfig


async def main():
    # 1. 初始化 LobsterShell
    shell = LobsterShell(
        mode=ModeConfig.HYBRID_SHIELD,  # 混合模式
        local_model="qwen2.5:7b",       # 本地審核模型
        local_db="postgresql://localhost/mydb",
        strict_mode=True,
    )

    print("🦞 LobsterShell 已初始化")
    print(f"   模式: {shell.mode.value}")
    print(f"   本地模型: {shell.local_model}")

    # 2. 模擬 OpenClaw Agent
    class MockOpenClawAgent:
        """模擬的 OpenClaw Agent"""

        async def run(self, request: str):
            # 模擬雲端 AI 處理
            return f"雲端處理結果: {request}"

    agent = MockOpenClawAgent()

    # 3. 包裝 Agent
    wrapped_agent = shell.wrap(agent)
    print("\n✅ OpenClaw Agent 已包裝")

    # 4. 測試不同請求

    # 4.1 普通查詢 (低敏感度)
    print("\n--- 測試 1: 普通查詢 ---")
    response1 = await wrapped_agent.run("今天天氣怎麼樣？")
    print(f"響應: {response1.final_output}")

    # 4.2 敏感數據查詢 (需確認)
    print("\n--- 測試 2: 敏感數據查詢 ---")
    response2 = await wrapped_agent.run(
        "查詢手機號 13812345678 的用戶餘額"
    )
    print(f"響應: {response2.final_output}")
    print(f"脫敏後: {response2.local_review.get('masked', False)}")

    # 4.3 危險操作 (被拒絕)
    print("\n--- 測試 3: 危險操作 ---")
    response3 = await wrapped_agent.run(
        "DELETE FROM users WHERE id=123"
    )
    print(f"響應: {response3.final_output}")
    print(f"被拒絕: {not response3.local_review.get('allowed', True)}")

    # 5. 查看審計日誌
    print("\n--- 審計日誌 ---")
    logs = shell.get_audit_logs()
    for log in logs[:3]:  # 只顯示前 3 條
        print(f"  [{log.level.value}] {log.action}")

    # 6. 驗證審計鏈
    is_valid = shell.verify_audit_chain()
    print(f"\n🔐 審計鏈完整性: {'✅ 有效' if is_valid else '❌ 已被篡改'}")


if __name__ == "__main__":
    asyncio.run(main())
