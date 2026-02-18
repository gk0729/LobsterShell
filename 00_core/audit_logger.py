"""
審計日誌 - LobsterShell 不可篡改審計系統

所有操作都留痕，支持 WORM (Write Once Read Many) 存儲
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
from enum import Enum
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


class AuditLevel(Enum):
    """審計級別"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """審計記錄"""
    timestamp: datetime
    level: AuditLevel
    action: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tenant_id: Optional[str] = None
    
    # 請求/響應
    request: Optional[str] = None
    masked_request: Optional[str] = None
    response: Optional[str] = None
    final_output: Optional[str] = None
    
    # 模式和策略
    mode: Optional[str] = None
    policy_decision: Optional[dict] = None
    
    # 數據操作
    sql_queries: list[str] = field(default_factory=list)
    api_calls: list[str] = field(default_factory=list)
    
    # 審核結果
    local_review_result: Optional[dict] = None
    cloud_review_result: Optional[dict] = None
    
    # 用戶交互
    approval_required: bool = False
    user_confirmed: Optional[bool] = None
    confirmation_method: Optional[str] = None
    
    # 完整性
    entry_hash: Optional[str] = None
    previous_hash: Optional[str] = None

    def compute_hash(self) -> str:
        """計算記錄哈希"""
        data = json.dumps({
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "action": self.action,
            "request": self.request,
            "response": self.response,
            "previous_hash": self.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()


class AuditLogger:
    """
    審計日誌器

    實現不可篡改的審計鏈
    """

    def __init__(self, storage_path: str = "./audit_logs"):
        self.storage_path = storage_path
        self._last_hash: Optional[str] = None
        self._entries: list[AuditEntry] = []

    def log(
        self,
        action: str,
        level: AuditLevel = AuditLevel.INFO,
        **kwargs,
    ) -> AuditEntry:
        """
        記錄審計日誌

        Args:
            action: 操作名稱
            level: 審計級別
            **kwargs: 其他字段

        Returns:
            AuditEntry: 審計記錄
        """
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            level=level,
            action=action,
            previous_hash=self._last_hash,
            **kwargs,
        )

        # 計算哈希
        entry.entry_hash = entry.compute_hash()
        self._last_hash = entry.entry_hash

        # 存儲
        self._entries.append(entry)
        self._persist(entry)

        logger.info(f"Audit: {action} [{level.value}]")
        return entry

    def _persist(self, entry: AuditEntry):
        """持久化審計記錄"""
        # TODO: 實現 WORM 存儲
        # 可以用 append-only 文件、區塊鏈、或專用 WORM 存儲
        pass

    def verify_chain(self) -> bool:
        """
        驗證審計鏈完整性

        Returns:
            bool: 鏈是否完整
        """
        if not self._entries:
            return True

        previous_hash = None
        for entry in self._entries:
            if entry.previous_hash != previous_hash:
                return False
            if entry.compute_hash() != entry.entry_hash:
                return False
            previous_hash = entry.entry_hash

        return True

    def search(
        self,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[AuditLevel] = None,
    ) -> list[AuditEntry]:
        """搜索審計記錄"""
        results = []
        for entry in self._entries:
            if action and entry.action != action:
                continue
            if user_id and entry.user_id != user_id:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            if level and entry.level != level:
                continue
            results.append(entry)
        return results

    def export(self, format: str = "json") -> str:
        """導出審計日誌"""
        if format == "json":
            return json.dumps([
                {
                    "timestamp": e.timestamp.isoformat(),
                    "level": e.level.value,
                    "action": e.action,
                    "request": e.request,
                    "response": e.response,
                    "mode": e.mode,
                    "entry_hash": e.entry_hash,
                }
                for e in self._entries
            ], indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
