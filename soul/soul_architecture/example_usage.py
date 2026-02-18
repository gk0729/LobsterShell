"""
🦞 Soul Architecture 使用示例
================================
演示如何使用抽取出的 LobsterShell 核心靈魂
"""

import asyncio
from soul_architecture import (
    SoulCore,
    ExecutionContext,
    ExecutionMode,
    ModeDecision,
    DataSource,
    DataSourceType,
    OverwriteRule,
)


# ===== 示例 1: 基本使用 =====

async def example_basic():
    """基礎使用示例"""
    print("\n" + "=" * 60)
    print("示例 1: 基本使用")
    print("=" * 60)
    
    # 1. 初始化核心
    core = SoulCore(
        local_threshold=0.8,
        cloud_threshold=0.3,
        enable_audit=True,
    )
    
    # 2. 註冊執行器（根據模式不同）
    async def local_executor(context, decision):
        """本地執行器"""
        return f"[本地執行] 處理: {context.input_content}"
    
    async def hybrid_executor(context, decision):
        """混合模式執行器"""
        return f"[混合執行] AI規劃 + 本地執行: {context.input_content}"
    
    async def cloud_executor(context, decision):
        """雲端執行器"""
        return f"[雲端執行] 已脫敏處理: {context.input_content}"
    
    core.register_executor(ExecutionMode.LOCAL_ONLY, local_executor)
    core.register_executor(ExecutionMode.HYBRID, hybrid_executor)
    core.register_executor(ExecutionMode.CLOUD_SANDBOX, cloud_executor)
    
    # 3. 創建執行上下文
    context = ExecutionContext(
        request_id="req-001",
        session_id="sess-001",
        user_id="user-001",
        tenant_id="tenant-001",
        input_content="查詢用戶餘額",
        granted_permissions=["ai:use", "database:read"],
    )
    
    # 4. 執行
    result = await core.execute(context)
    
    print(f"\n✅ 執行結果:")
    print(f"   成功: {result.success}")
    print(f"   模式: {result.mode.value}")
    print(f"   輸出: {result.output}")
    print(f"   決策原因: {result.mode_decision.reason}")
    print(f"   敏感度: {result.mode_decision.sensitivity_score:.2f}")
    print(f"   總耗時: {result.total_time_ms:.2f}ms")
    
    return core, result


# ===== 示例 2: 敏感度驅動的模式切換 =====

async def example_sensitivity_modes(core: SoulCore):
    """演示不同敏感度內容的模式選擇"""
    print("\n" + "=" * 60)
    print("示例 2: 敏感度驅動的模式切換")
    print("=" * 60)
    
    test_cases = [
        ("今天天氣如何？", "低敏感度 - 日常問題"),
        ("分析這個 CSV 文件", "中敏感度 - 文件處理"),
        ("我的銀行密碼是 123456", "高敏感度 - 密碼洩漏"),
        ("信用卡號 4111-1111-1111-1111", "高敏感度 - 金融信息"),
        ("刪除所有用戶數據", "高敏感度 - 危險操作"),
    ]
    
    for content, description in test_cases:
        context = ExecutionContext(
            request_id=f"req-{hash(content) % 10000}",
            session_id="sess-002",
            user_id="user-001",
            input_content=content,
            granted_permissions=["ai:use"],
        )
        
        result = await core.execute(context)
        
        print(f"\n📋 {description}")
        print(f"   輸入: {content[:40]}...")
        print(f"   選擇模式: {result.mode.value:20} (敏感度: {result.mode_decision.sensitivity_score:.2f})")
        print(f"   需確認: {'是' if result.mode_decision.requires_confirmation else '否'}")


# ===== 示例 3: 零幻覺數據覆寫 =====

async def example_zero_hallucination(core: SoulCore):
    """演示零幻覺數據覆寫"""
    print("\n" + "=" * 60)
    print("示例 3: 零幻覺數據覆寫")
    print("=" * 60)
    
    # 1. 註冊數據源
    core.register_data_source(DataSource(
        name="user_db",
        source_type=DataSourceType.SQL,
        connection_string="postgresql://localhost/mydb",
        read_only=True,
    ))
    
    # 2. 註冊覆寫規則
    core.register_overwrite_rule(OverwriteRule(
        placeholder="{{user.balance}}",
        data_source="user_db",
        query_template="SELECT balance FROM accounts WHERE user_id = {user_id}",
        fallback_value="0.00",
        transform=lambda x: f"{float(x):,.2f}",
    ))
    
    core.register_overwrite_rule(OverwriteRule(
        placeholder="{{user.name}}",
        data_source="user_db",
        query_template="SELECT name FROM users WHERE id = {user_id}",
        fallback_value="未知用戶",
    ))
    
    # 3. AI 生成的模板（含佔位符）
    ai_template = """
尊敬的 {{user.name}}，

您的當前賬戶餘額為: ${{user.balance}} USD

如有疑問請聯繫客服。
"""
    
    # 4. 執行（帶覆寫）
    context = ExecutionContext(
        request_id="req-003",
        session_id="sess-003",
        user_id="user-123",
        input_content="查詢餘額",
        granted_permissions=["ai:use", "database:read"],
    )
    
    # 模擬執行器返回模板
    async def template_executor(ctx, decision):
        return ai_template
    
    core.register_executor(ExecutionMode.HYBRID, template_executor)
    
    result = await core.execute(context)
    
    print("\n📝 AI 原始輸出（模板）:")
    print(ai_template)
    
    print("\n✅ 覆寫後的最終輸出:")
    print(result.output)
    
    print(f"\n📊 覆寫統計:")
    print(f"   總佔位符: {result.overwrite_stats.get('total', 0)}")
    print(f"   成功覆寫: {result.overwrite_stats.get('success', 0)}")
    print(f"   覆寫耗時: {result.overwrite_stats.get('time_ms', 0):.2f}ms")


# ===== 示例 4: 完整執行流程展示 =====

async def example_full_flow():
    """展示完整的執行流程"""
    print("\n" + "=" * 60)
    print("示例 4: 完整執行流程")
    print("=" * 60)
    
    core = SoulCore(enable_audit=True)
    
    # 註冊執行器
    async def mock_ai_executor(context, decision):
        # 模擬 AI 生成帶佔位符的輸出
        return f"""
查詢結果:
- 用戶: {{user.name}}
- 餘額: ${{user.balance}}
- 狀態: {{user.status}}
- AI 分析: 這是基於輸入 '{context.input_content}' 的分析結果
"""
    
    core.register_executor(ExecutionMode.HYBRID, mock_ai_executor)
    
    # 註冊數據源和規則
    core.register_data_source(DataSource(
        name="main_db",
        source_type=DataSourceType.SQL,
        read_only=True,
    ))
    
    for placeholder, query in [
        ("{{user.name}}", "SELECT '張三' as value"),
        ("{{user.balance}}", "SELECT 15000.50 as value"),
        ("{{user.status}}", "SELECT '活躍' as value"),
    ]:
        core.register_overwrite_rule(OverwriteRule(
            placeholder=placeholder,
            data_source="main_db",
            query_template=query,
        ))
    
    # 執行
    context = ExecutionContext(
        request_id="req-full-001",
        session_id="sess-full-001",
        user_id="user-001",
        input_content="查詢我的賬戶信息和餘額",
        granted_permissions=["ai:use", "database:read"],
    )
    
    result = await core.execute(context)
    
    print("\n📊 執行流程統計:")
    for stage, timing in result.stage_timings.items():
        print(f"   {stage:15}: {timing:8.2f}ms")
    print(f"   {'total':15}: {result.total_time_ms:8.2f}ms")
    
    print(f"\n🎯 模式決策:")
    print(f"   選擇模式: {result.mode.value}")
    print(f"   置信度: {result.mode_decision.confidence:.0%}")
    print(f"   決策原因: {result.mode_decision.reason}")
    
    if result.security_report:
        print(f"\n🔒 安全檢查:")
        print(f"   整體狀態: {'通過' if result.security_report.overall_passed else '未通過'}")
        print(f"   風險等級: {result.security_report.risk_level}")
    
    print(f"\n📝 最終輸出:")
    print(result.output)
    
    # 審計報告
    print(f"\n📋 審計記錄:")
    print(core.get_audit_report(context.session_id))
    
    # 驗證審計鏈
    is_valid = core.verify_audit_chain()
    print(f"\n🔐 審計鏈完整性: {'✅ 有效' if is_valid else '❌ 無效'}")


# ===== 主入口 =====

async def main():
    """主函數"""
    print("\n" + "=" * 60)
    print("🦞 LobsterShell Soul Architecture 演示")
    print("=" * 60)
    
    # 示例 1: 基本使用
    core, _ = await example_basic()
    
    # 示例 2: 敏感度模式切換
    await example_sensitivity_modes(core)
    
    # 示例 3: 零幻覺覆寫
    await example_zero_hallucination(core)
    
    # 示例 4: 完整流程
    await example_full_flow()
    
    # 最終統計
    print("\n" + "=" * 60)
    print("📊 最終統計")
    print("=" * 60)
    stats = core.get_stats()
    print(f"總執行次數: {stats['total_executions']}")
    print(f"成功: {stats['successful']}")
    print(f"失敗: {stats['failed']}")
    if 'success_rate' in stats:
        print(f"成功率: {stats['success_rate']:.1%}")


if __name__ == "__main__":
    asyncio.run(main())
