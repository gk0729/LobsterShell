"""
不可篡改審計鏈 - Immutable Audit Chain
========================================
核心能力：所有決策和執行留痕，支持完整性驗證

設計原則:
1. Write Once Read Many (WORM)
2. 哈希鏈確保記錄不可篡改
3. 包含完整的決策上下文
4. 支持審計追蹤和合規檢查
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class AuditLevel(Enum):
    """審計級別"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEventType(Enum):
    """審計事件類型"""
    MODE_DECISION = "mode_decision"         # 模式決策
    SECURITY_CHECK = "security_check"       # 安全檢查
    DATA_OVERWRITE = "data_overwrite"       # 數據覆寫
    EXECUTION_START = "execution_start"     # 執行開始
    EXECUTION_END = "execution_end"         # 執行結束
    USER_CONFIRMATION = "user_confirmation" # 用戶確認
    POLICY_VIOLATION = "policy_violation"   # 策略違規


@dataclass
class AuditEntry:
    """審計記錄"""
    # 基本識別（無默認值）
    entry_id: str
    timestamp: datetime
    level: AuditLevel
    event_type: AuditEventType
    session_id: str
    request_id: str
    action: str
    description: str
    
    # 可選字段（有默認值）
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    decision: Optional[str] = None
    reason: Optional[str] = None
    confidence: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None
    entry_hash: Optional[str] = None
    previous_hash: Optional[str] = None
    
    def compute_hash(self) -> str:
        """計算記錄哈希"""
        data = {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "action": self.action,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "previous_hash": self.previous_hash,
        }
        
        # 序列化並哈希
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def finalize(self, previous_hash: Optional[str] = None):
        """完成記錄，計算哈希"""
        self.previous_hash = previous_hash
        self.entry_hash = self.compute_hash()
        return self


@dataclass
class AuditChainStatus:
    """審計鏈狀態"""
    total_entries: int
    valid: bool
    broken_at: Optional[str] = None
    first_timestamp: Optional[datetime] = None
    last_timestamp: Optional[datetime] = None


class AuditChain:
    """
    不可篡改審計鏈
    
    使用哈希鏈確保審計記錄的完整性:
    Entry N 的 previous_hash = Entry N-1 的 entry_hash
    
    如果任何記錄被篡改，verify_chain() 將檢測到不一致
    """
    
    def __init__(self, chain_id: str = "default"):
        self.chain_id = chain_id
        self._entries: List[AuditEntry] = []
        self._last_hash: Optional[str] = None
        self._index_by_session: Dict[str, List[AuditEntry]] = {}
        self._index_by_user: Dict[str, List[AuditEntry]] = {}
    
    def add(self, entry: AuditEntry) -> AuditEntry:
        """
        添加審計記錄
        
        自動計算哈希並維護鏈式結構
        """
        # 完成記錄（計算哈希）
        entry.finalize(self._last_hash)
        
        # 添加到鏈
        self._entries.append(entry)
        self._last_hash = entry.entry_hash
        
        # 更新索引
        if entry.session_id:
            self._index_by_session.setdefault(entry.session_id, []).append(entry)
        if entry.user_id:
            self._index_by_user.setdefault(entry.user_id, []).append(entry)
        
        # 持久化（異步）
        self._persist_async(entry)
        
        logger.debug(f"[Audit] {entry.event_type.value}: {entry.action}")
        return entry
    
    def create_entry(
        self,
        event_type: AuditEventType,
        action: str,
        description: str,
        session_id: str,
        request_id: str,
        level: AuditLevel = AuditLevel.INFO,
        **kwargs,
    ) -> AuditEntry:
        """
        便捷方法：創建並添加審計記錄
        """
        import uuid
        
        entry = AuditEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            level=level,
            event_type=event_type,
            session_id=session_id,
            request_id=request_id,
            action=action,
            description=description,
            **kwargs,
        )
        
        return self.add(entry)
    
    def verify_chain(self) -> AuditChainStatus:
        """
        驗證審計鏈完整性
        
        逐個驗證每個記錄的哈希和鏈接關係
        """
        if not self._entries:
            return AuditChainStatus(total_entries=0, valid=True)
        
        previous_hash = None
        
        for i, entry in enumerate(self._entries):
            # 檢查 previous_hash 是否匹配
            if entry.previous_hash != previous_hash:
                return AuditChainStatus(
                    total_entries=len(self._entries),
                    valid=False,
                    broken_at=entry.entry_id,
                    first_timestamp=self._entries[0].timestamp,
                    last_timestamp=self._entries[-1].timestamp,
                )
            
            # 檢查當前哈希是否正確
            expected_hash = entry.compute_hash()
            if entry.entry_hash != expected_hash:
                return AuditChainStatus(
                    total_entries=len(self._entries),
                    valid=False,
                    broken_at=entry.entry_id,
                    first_timestamp=self._entries[0].timestamp,
                    last_timestamp=self._entries[-1].timestamp,
                )
            
            previous_hash = entry.entry_hash
        
        return AuditChainStatus(
            total_entries=len(self._entries),
            valid=True,
            first_timestamp=self._entries[0].timestamp,
            last_timestamp=self._entries[-1].timestamp,
        )
    
    def search(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[AuditLevel] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """搜索審計記錄"""
        results = []
        
        # 使用索引優化
        if user_id and user_id in self._index_by_user:
            entries_to_search = self._index_by_user[user_id]
        elif session_id and session_id in self._index_by_session:
            entries_to_search = self._index_by_session[session_id]
        else:
            entries_to_search = self._entries
        
        for entry in entries_to_search:
            if event_type and entry.event_type != event_type:
                continue
            if user_id and entry.user_id != user_id:
                continue
            if session_id and entry.session_id != session_id:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            if level and entry.level != level:
                continue
            
            results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_session_timeline(self, session_id: str) -> List[AuditEntry]:
        """獲取某個會話的完整時間線"""
        return self._index_by_session.get(session_id, [])
    
    def export(
        self,
        format: str = "json",
        include_hash: bool = True,
    ) -> str:
        """導出審計鏈"""
        if format == "json":
            data = []
            for entry in self._entries:
                entry_dict = {
                    "entry_id": entry.entry_id,
                    "timestamp": entry.timestamp.isoformat(),
                    "level": entry.level.value,
                    "event_type": entry.event_type.value,
                    "session_id": entry.session_id,
                    "request_id": entry.request_id,
                    "user_id": entry.user_id,
                    "action": entry.action,
                    "description": entry.description,
                    "success": entry.success,
                    "details": entry.details,
                }
                
                if include_hash:
                    entry_dict["entry_hash"] = entry.entry_hash
                    entry_dict["previous_hash"] = entry.previous_hash
                
                data.append(entry_dict)
            
            return json.dumps(data, indent=2, default=str)
        
        elif format == "csv":
            lines = ["timestamp,event_type,action,user_id,success,description"]
            for entry in self._entries:
                lines.append(
                    f"{entry.timestamp.isoformat()},{entry.event_type.value},"
                    f"{entry.action},{entry.user_id},{entry.success},"
                    f'"{entry.description}"'
                )
            return "\n".join(lines)
        
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def generate_report(self, session_id: Optional[str] = None) -> str:
        """生成可讀的審計報告"""
        if session_id:
            entries = self.get_session_timeline(session_id)
            title = f"會話審計報告: {session_id}"
        else:
            entries = self._entries[-50:]  # 最近 50 條
            title = "最近審計記錄"
        
        lines = [
            "=" * 60,
            f"📋 {title}",
            "=" * 60,
            f"總記錄數: {len(entries)}",
            "-" * 60,
        ]
        
        for entry in entries:
            icon = {
                AuditLevel.DEBUG: "🔍",
                AuditLevel.INFO: "ℹ️",
                AuditLevel.WARNING: "⚠️",
                AuditLevel.ERROR: "❌",
                AuditLevel.CRITICAL: "🚨",
            }.get(entry.level, "•")
            
            status = "✅" if entry.success else "❌"
            
            lines.append(
                f"{icon} [{entry.timestamp.strftime('%H:%M:%S')}] "
                f"{entry.event_type.value} | {status} {entry.action}"
            )
            lines.append(f"   {entry.description}")
            
            if entry.decision:
                lines.append(f"   決策: {entry.decision}")
            
            if entry.error_message:
                lines.append(f"   錯誤: {entry.error_message}")
            
            lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def _persist_async(self, entry: AuditEntry):
        """異步持久化（可擴展為寫入數據庫/文件等）"""
        # TODO: 實現實際的持久化邏輯
        # 例如：寫入 append-only 文件、數據庫、或區塊鏈
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        if not self._entries:
            return {"total": 0, "by_type": {}, "by_level": {}}
        
        by_type = {}
        by_level = {}
        
        for entry in self._entries:
            et = entry.event_type.value
            el = entry.level.value
            by_type[et] = by_type.get(et, 0) + 1
            by_level[el] = by_level.get(el, 0) + 1
        
        return {
            "total": len(self._entries),
            "by_type": by_type,
            "by_level": by_level,
            "sessions": len(self._index_by_session),
            "users": len(self._index_by_user),
        }
