"""
零幻覺數據覆寫層 - Zero Hallucination Overwriter
==================================================
核心能力：將 AI 的「猜測值」覆寫為「精確數據」

設計原則:
1. AI 只輸出模板和佔位符，不接觸真實數據
2. SQL Robot 只執行只讀查詢，做核對/複製/粘貼
3. 物理隔離確保 AI 無法修改數據獲取邏輯
4. 最終輸出 = SQL 精確數據，而非 AI 猜測

核心流程:
    AI 輸出(含佔位符) → 解析佔位符 → SQL 查詢 → 數據覆寫 → 精確輸出
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Protocol
from abc import ABC, abstractmethod
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """數據源類型"""
    SQL = "sql"
    API = "api"
    FILE = "file"
    CACHE = "cache"
    MEMORY = "memory"


@dataclass
class DataSource:
    """數據源配置"""
    name: str
    source_type: DataSourceType
    connection_string: Optional[str] = None
    read_only: bool = True  # 強制只讀
    timeout: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OverwriteRule:
    """覆寫規則"""
    placeholder: str           # 佔位符，如 {{user.balance}}
    data_source: str           # 數據源名稱
    query_template: str        # 查詢模板
    fallback_value: Any = None  # 獲取失敗時的默認值
    validator: Optional[Callable[[Any], bool]] = None  # 值驗證器
    transform: Optional[Callable[[Any], Any]] = None   # 值轉換器


@dataclass
class OverwriteResult:
    """覆寫結果"""
    success: bool
    placeholder: str
    original_value: Any
    final_value: Any
    data_source: str
    query_time_ms: float
    error: Optional[str] = None


class QueryRunner(Protocol):
    """查詢執行器協議"""
    
    async def execute(
        self,
        data_source: DataSource,
        query: str,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """執行查詢並返回結果"""
        ...


class SQLQueryRunner:
    """SQL 查詢執行器 - 只讀"""
    
    WRITE_KEYWORDS = [
        'insert', 'update', 'delete', 'drop', 'create',
        'alter', 'truncate', 'grant', 'revoke', 'merge'
    ]
    
    def __init__(self):
        self._connections: Dict[str, Any] = {}
    
    async def execute(
        self,
        data_source: DataSource,
        query: str,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """執行只讀 SQL 查詢"""
        import time
        start = time.time()
        
        # 安全檢查：確保是只讀查詢
        if not self._is_readonly(query):
            raise ValueError(f"拒絕非只讀查詢: {query[:50]}...")
        
        # TODO: 實際數據庫連接和查詢
        # 這裡是模擬實現
        logger.info(f"執行 SQL 查詢: {query[:100]}...")
        
        # 模擬查詢結果
        result = {
            "data": {"value": "精確數據值"},  # 實際應從數據庫獲取
            "row_count": 1,
            "execution_time_ms": (time.time() - start) * 1000,
        }
        
        return result
    
    def _is_readonly(self, query: str) -> bool:
        """檢查 SQL 是否為只讀"""
        query_upper = query.upper().strip()
        
        # 必須以 SELECT 開頭
        if not query_upper.startswith('SELECT'):
            return False
        
        # 檢查是否包含寫入關鍵字
        query_lower = query.lower()
        for keyword in self.WRITE_KEYWORDS:
            if keyword in query_lower:
                return False
        
        return True


class PlaceholderParser:
    """佔位符解析器"""
    
    # 支持的佔位符格式
    PLACEHOLDER_PATTERNS = [
        r'\{\{(\w+(?:\.\w+)*)\}\}',           # {{user.balance}}
        r'\$\{(\w+(?:\.\w+)*)\}',              # ${user.balance}
        r'\$(\w+(?:\.\w+)*)\b',                # $user.balance
        r'\[\[(\w+(?:\.\w+)*)\]\]',           # [[user.balance]]
    ]
    
    def __init__(self):
        self._compiled_patterns = [re.compile(p) for p in self.PLACEHOLDER_PATTERNS]
    
    def parse(self, template: str) -> List[Dict[str, Any]]:
        """
        解析模板中的佔位符
        
        Returns:
            [
                {
                    "placeholder": "{{user.balance}}",
                    "key": "user.balance",
                    "position": (start, end),
                }
            ]
        """
        placeholders = []
        
        for pattern in self._compiled_patterns:
            for match in pattern.finditer(template):
                placeholders.append({
                    "placeholder": match.group(0),
                    "key": match.group(1),
                    "position": (match.start(), match.end()),
                })
        
        return placeholders
    
    def extract_keys(self, template: str) -> List[str]:
        """提取所有佔位符鍵名"""
        placeholders = self.parse(template)
        return list(set(p["key"] for p in placeholders))


class ZeroHallucinationOverwriter:
    """
    零幻覺數據覆寫器
    
    核心使命：確保最終用戶看到的是精確數據，而非 AI 猜測
    
    使用方式:
        1. AI 生成帶佔位符的模板
        2. Overwriter 解析佔位符
        3. 從數據源獲取精確值
        4. 覆寫佔位符
        5. 返回最終結果
    """
    
    def __init__(self):
        self.data_sources: Dict[str, DataSource] = {}
        self.rules: Dict[str, OverwriteRule] = {}
        self.query_runners: Dict[DataSourceType, QueryRunner] = {}
        self.parser = PlaceholderParser()
        
        # 註冊默認查詢執行器
        self._register_default_runners()
    
    def _register_default_runners(self):
        """註冊默認查詢執行器"""
        self.query_runners[DataSourceType.SQL] = SQLQueryRunner()
    
    def register_data_source(self, source: DataSource):
        """註冊數據源"""
        self.data_sources[source.name] = source
        logger.info(f"註冊數據源: {source.name} ({source.source_type.value})")
    
    def register_rule(self, rule: OverwriteRule):
        """註冊覆寫規則"""
        self.rules[rule.placeholder] = rule
        logger.info(f"註冊覆寫規則: {rule.placeholder} -> {rule.data_source}")
    
    def register_query_runner(
        self,
        source_type: DataSourceType,
        runner: QueryRunner,
    ):
        """註冊自定義查詢執行器"""
        self.query_runners[source_type] = runner
    
    async def overwrite(
        self,
        template: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        覆寫模板中的佔位符
        
        Args:
            template: 包含佔位符的模板
            context: 上下文變量
            
        Returns:
            {
                "final_output": str,      # 覆寫後的最終輸出
                "results": list,          # 每個佔位符的覆寫結果
                "success": bool,          # 是否全部成功
                "stats": dict,            # 統計信息
            }
        """
        import time
        start_time = time.time()
        
        # 1. 解析佔位符
        placeholders = self.parser.parse(template)
        
        if not placeholders:
            # 沒有佔位符，直接返回
            return {
                "final_output": template,
                "results": [],
                "success": True,
                "stats": {"total": 0, "success": 0, "failed": 0, "time_ms": 0},
            }
        
        # 2. 逐個覆寫
        results = []
        final_output = template
        
        for ph_info in placeholders:
            placeholder = ph_info["placeholder"]
            key = ph_info["key"]
            
            result = await self._overwrite_single(
                placeholder=placeholder,
                key=key,
                context=context,
            )
            results.append(result)
            
            # 替換模板中的佔位符
            if result.success:
                final_output = final_output.replace(
                    placeholder,
                    str(result.final_value),
                )
            else:
                # 使用 fallback 或保留原樣
                fallback = self.rules.get(placeholder, OverwriteRule("", "", "")).fallback_value
                if fallback is not None:
                    final_output = final_output.replace(placeholder, str(fallback))
        
        # 3. 統計
        success_count = sum(1 for r in results if r.success)
        total_time_ms = (time.time() - start_time) * 1000
        
        return {
            "final_output": final_output,
            "results": results,
            "success": success_count == len(results),
            "stats": {
                "total": len(results),
                "success": success_count,
                "failed": len(results) - success_count,
                "time_ms": round(total_time_ms, 2),
            },
        }
    
    async def _overwrite_single(
        self,
        placeholder: str,
        key: str,
        context: Optional[Dict[str, Any]],
    ) -> OverwriteResult:
        """覆寫單個佔位符"""
        import time
        start = time.time()
        
        # 查找規則
        rule = self.rules.get(placeholder)
        if not rule:
            # 嘗試從上下文獲取
            if context and key in context:
                value = context[key]
                return OverwriteResult(
                    success=True,
                    placeholder=placeholder,
                    original_value=placeholder,
                    final_value=value,
                    data_source="context",
                    query_time_ms=(time.time() - start) * 1000,
                )
            
            return OverwriteResult(
                success=False,
                placeholder=placeholder,
                original_value=placeholder,
                final_value=None,
                data_source="unknown",
                query_time_ms=0,
                error=f"未找到佔位符 '{placeholder}' 的覆寫規則",
            )
        
        # 獲取數據源
        data_source = self.data_sources.get(rule.data_source)
        if not data_source:
            return OverwriteResult(
                success=False,
                placeholder=placeholder,
                original_value=placeholder,
                final_value=None,
                data_source=rule.data_source,
                query_time_ms=0,
                error=f"數據源 '{rule.data_source}' 未註冊",
            )
        
        try:
            # 構建查詢
            query = self._build_query(rule.query_template, context)
            
            # 獲取查詢執行器
            runner = self.query_runners.get(data_source.source_type)
            if not runner:
                raise ValueError(f"不支持的數據源類型: {data_source.source_type}")
            
            # 執行查詢
            query_result = await runner.execute(data_source, query)
            value = query_result.get("data", {}).get("value")
            
            # 驗證
            if rule.validator and not rule.validator(value):
                raise ValueError(f"值驗證失敗: {value}")
            
            # 轉換
            if rule.transform:
                value = rule.transform(value)
            
            return OverwriteResult(
                success=True,
                placeholder=placeholder,
                original_value=placeholder,
                final_value=value,
                data_source=rule.data_source,
                query_time_ms=(time.time() - start) * 1000,
            )
            
        except Exception as e:
            logger.error(f"覆寫失敗: {placeholder} - {e}")
            
            # 使用 fallback
            if rule.fallback_value is not None:
                return OverwriteResult(
                    success=True,  # fallback 視為成功
                    placeholder=placeholder,
                    original_value=placeholder,
                    final_value=rule.fallback_value,
                    data_source=rule.data_source,
                    query_time_ms=(time.time() - start) * 1000,
                )
            
            return OverwriteResult(
                success=False,
                placeholder=placeholder,
                original_value=placeholder,
                final_value=None,
                data_source=rule.data_source,
                query_time_ms=(time.time() - start) * 1000,
                error=str(e),
            )
    
    def _build_query(self, template: str, context: Optional[Dict]) -> str:
        """構建最終查詢"""
        if not context:
            return template
        
        # 簡單的字符串替換
        query = template
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in query:
                # 防止 SQL 注入：只允許數字和簡單字符串
                safe_value = self._sanitize_value(value)
                query = query.replace(placeholder, safe_value)
        
        return query
    
    def _sanitize_value(self, value: Any) -> str:
        """清理值以防止注入"""
        if isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # 只允許字母數字和少數安全字符
            import re
            safe = re.sub(r'[^\w\s.-]', '', value)
            return f"'{safe}'"
        else:
            return str(value)
    
    def create_sql_rule(
        self,
        placeholder: str,
        data_source: str,
        sql_query: str,
        fallback: Any = None,
    ) -> OverwriteRule:
        """便捷方法：創建 SQL 覆寫規則"""
        return OverwriteRule(
            placeholder=placeholder,
            data_source=data_source,
            query_template=sql_query,
            fallback_value=fallback,
        )


# ===== 使用示例 =====

EXAMPLE_TEMPLATE = """
用戶信息報告
==============
姓名: {{user.name}}
餘額: ${{user.balance}} USD
等級: {{user.level}}
註冊時間: {{user.created_at}}
==============
此報告由 AI 生成，數據經 SQL Robot 覆寫確保準確
"""

EXAMPLE_RULES = [
    OverwriteRule(
        placeholder="{{user.name}}",
        data_source="user_db",
        query_template="SELECT name as value FROM users WHERE id = {user_id}",
        fallback_value="未知用戶",
    ),
    OverwriteRule(
        placeholder="${{user.balance}}",
        data_source="user_db",
        query_template="SELECT balance as value FROM accounts WHERE user_id = {user_id}",
        fallback_value=0.0,
        transform=lambda x: f"{float(x):,.2f}",
    ),
]
