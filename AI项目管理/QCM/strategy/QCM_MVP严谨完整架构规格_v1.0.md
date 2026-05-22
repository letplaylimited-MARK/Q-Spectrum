# QCM MVP 严谨完整架构规格
## 融入幽灵通道协议的完整实现

**版本**: v1.0-StrictSpec  
**日期**: 2026-04-07  
**核心理念**: 幽灵通道是核心，不是可选组件  

---

## 一、完整架构（幽灵通道驱动）

```
┌─────────────────────────────────────────────────────────────────────┐
│                          用户界面层                                   │
│              (聊天室 / 项目助手 / 协作空间 / 知识库)                   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────┐
│                          QCM核心引擎层                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   角色系统   │  │  知识共鸣   │  │  工作流引擎 │  │   飞轮系统  │  │
│  │  RoleEngine │  │ ResonanceEng│  │ WorkflowEng │  │  Flywheel  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
│          │                │                │                │          │
│          └────────────────┴────────────────┴────────────────┘          │
│                                 │                                      │
│                          幽灵通道协议层（核心）                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                        协议管理器                                 │ │
│  │                   GhostChannelManager                            │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐       │
│  │ Delta同步    │ 因果排序     │ 加密传输     │ 审计追踪     │       │
│  │ DeltaSyncer  │ VectorClock  │ CryptoEngine │ AuditLogger  │       │
│  ├──────────────┼──────────────┼──────────────┼──────────────┤       │
│  │ 增量计算     │ 事件偏序     │ AES-256-GCM  │ 事务记录     │       │
│  │ 压缩优化    │ 冲突检测     │ HMAC验证     │ Merkle验证   │       │
│  │ 差分载荷    │ 因果一致性   │ 密钥派生     │ 完整性验证   │       │
│  └──────────────┴──────────────┴──────────────┴──────────────┘       │
│                                  │                                      │
│                          数据存储层                                    │
│           (状态快照 / 向量时钟 / 审计日志 / 差分历史)                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────┐
│                          AI模型接入层                                 │
│              (OpenAI / Claude / Gemini / 国产模型)                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、幽灵通道原子能力在MVP中的实现

### 2.1 原子能力A：Delta增量同步

```python
class DeltaSyncer:
    """Delta增量同步器"""
    
    def compute_delta(self, old_state: dict, new_state: dict) -> DeltaPayload:
        """
        计算两个状态之间的差异
        
        Returns:
            DeltaPayload: 包含 added, modified, removed, list_appends, changed_fields
        """
        delta = {
            "added": {},
            "modified": {},
            "removed": [],
            "list_appends": {},
            "changed_fields": {}
        }
        
        # 比较逻辑...
        
        return DeltaPayload(**delta)
    
    def apply_delta(self, state: dict, delta: DeltaPayload) -> dict:
        """将Delta应用到状态"""
        # 应用逻辑...
        return new_state
```

### 2.2 原子能力B：因果排序

```python
class VectorClock:
    """向量时钟 - 因果排序"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.clock = defaultdict(int)
    
    def increment(self):
        """增加本地时钟"""
        self.clock[self.node_id] += 1
    
    def merge(self, other_clock: dict):
        """合并外部时钟"""
        for node, time in other_clock.items():
            self.clock[node] = max(self.clock[node], time)
    
    def happens_before(self, other: 'VectorClock') -> str:
        """
        判断因果关系
        
        Returns:
            "BEFORE"  - self 先于 other
            "AFTER"   - self 后于 other  
            "CONCURRENT" - 并发
        """
        # 实现逻辑...
        pass
    
    def to_dict(self) -> dict:
        return dict(self.clock)
```

### 2.3 原子能力C：加密传输

```python
class CryptoEngine:
    """加密引擎 - AES-256-GCM"""
    
    def __init__(self, key: bytes = None):
        if key is None:
            key = os.urandom(32)  # 256位密钥
        self.key = key
    
    def encrypt(self, data: bytes, aad: bytes = None) -> tuple[bytes, bytes, bytes]:
        """
        加密数据
        
        Returns:
            (ciphertext, nonce, auth_tag)
        """
        cipher = AESGCM(self.key)
        nonce = os.urandom(12)  # 96位nonce
        ciphertext = cipher.encrypt(nonce, data, aad)
        return ciphertext, nonce
    
    def decrypt(self, ciphertext: bytes, nonce: bytes, tag: bytes, aad: bytes = None) -> bytes:
        """解密数据"""
        cipher = AESGCM(self.key)
        return cipher.decrypt(nonce, ciphertext + tag, aad)
    
    def sign(self, data: bytes) -> str:
        """HMAC-SHA256签名"""
        return hmac.new(self.key, data, hashlib.sha256).hexdigest()
    
    def verify(self, data: bytes, signature: str) -> bool:
        """验证签名"""
        expected = hmac.new(self.key, data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
```

### 2.4 原子能力D：完整性验证

```python
class MerkleTree:
    """Merkle树 - 完整性验证"""
    
    def __init__(self):
        self.leaves = []
        self.tree = []
    
    def build(self, data: list[bytes]) -> str:
        """构建Merkle树，返回根哈希"""
        self.leaves = [hashlib.sha256(d).digest() for d in self.tree]
        
        # 构建树...
        
        return self.tree[0] if self.tree else None
    
    def verify(self, root: str, proof: list, leaf: bytes) -> bool:
        """验证完整性"""
        # 验证逻辑...
        pass
    
    def get_root(self) -> str:
        return self.tree[0] if self.tree else None
```

### 2.5 原子能力E：审计追踪

```python
@dataclass
class AuditEntry:
    """审计条目"""
    transaction_id: str
    timestamp: float
    source_role: str
    destination_role: str
    message_type: str
    delta_hash: str
    merkle_root_before: str
    merkle_root_after: str
    bandwidth_saved_bytes: int
    transmission_duration_ms: float
    signature_verified: bool
    tamper_detected: bool

class AuditLogger:
    """审计日志器"""
    
    def __init__(self, storage_path: str):
        self.storage = storage_path
    
    def log(self, entry: AuditEntry):
        """记录审计条目"""
        # 写入持久化存储
        pass
    
    def query(self, filters: dict) -> list[AuditEntry]:
        """查询审计日志"""
        pass
    
    def verify_chain(self, from_txn: str, to_txn: str) -> bool:
        """验证审计链完整性"""
        pass
```

### 2.6 原子能力F：自愈恢复

```python
@dataclass
class SnapshotRecord:
    """快照记录"""
    snapshot_id: str
    state: dict
    vector_clock: dict
    merkle_root: str
    timestamp: float

class SelfHealer:
    """自愈恢复器"""
    
    def __init__(self):
        self.snapshots: list[SnapshotRecord] = []
    
    def create_snapshot(self, state: dict, vc: VectorClock, merkle_root: str) -> SnapshotRecord:
        """创建快照"""
        snapshot = SnapshotRecord(
            snapshot_id=str(uuid4()),
            state=copy.deepcopy(state),
            vector_clock=vc.to_dict(),
            merkle_root=merkle_root,
            timestamp=time.time()
        )
        self.snapshots.append(snapshot)
        return snapshot
    
    def recover(self, snapshot_id: str) -> dict:
        """从快照恢复"""
        for snap in self.snapshots:
            if snap.snapshot_id == snapshot_id:
                return copy.deepcopy(snap.state)
        raise ValueError(f"Snapshot {snapshot_id} not found")
    
    def find_latest_valid_snapshot(self) -> SnapshotRecord:
        """找到最新的有效快照"""
        valid = [s for s in self.snapshots if not self._is_corrupted(s)]
        return valid[-1] if valid else None
```

---

## 三、幽灵通道管理器（核心）

```python
class GhostChannelManager:
    """幽灵通道管理器 - 统一协调所有原子能力"""
    
    def __init__(self, config: GhostChannelConfig):
        # 核心组件
        self.delta_syncer = DeltaSyncer()
        self.vector_clock = VectorClock(config.node_id)
        self.crypto = CryptoEngine(config.encryption_key)
        self.merkle = MerkleTree()
        self.audit_logger = AuditLogger(config.audit_path)
        self.self_healer = SelfHealer()
        
        # 存储
        self.state_store = {}  # 当前状态
        self.history = []  # 同步历史
        
        # 配置
        self.config = config
    
    async def sync_state(self, new_state: dict, target: str) -> SyncResult:
        """
        核心同步方法 - 完整流程
        
        1. Delta计算
        2. 压缩
        3. 加密
        4. 发送
        5. 验证
        6. 审计
        """
        start_time = time.time()
        
        # 1. 获取旧状态
        old_state = self.state_store.get(target, {})
        
        # 2. Delta计算
        delta = self.delta_syncer.compute_delta(old_state, new_state)
        
        # 3. 压缩
        compressed = self._compress(delta)
        
        # 4. 向量时钟
        self.vector_clock.increment()
        
        # 5. 加密
        encrypted, nonce, tag = self.crypto.encrypt(
            json.dumps(compressed).encode()
        )
        
        # 6. Merkle根
        self.merkle.build([encrypted])
        merkle_root = self.merkle.get_root()
        
        # 7. 计算带宽节省
        old_size = len(json.dumps(old_state))
        new_size = len(encrypted)
        bandwidth_saved = max(0, old_size - new_size)
        
        # 8. 发送（这里简化，实际会走网络）
        success = await self._send(target, encrypted, nonce, tag)
        
        if success:
            # 9. 更新状态
            self.state_store[target] = new_state
            
            # 10. 创建快照
            self.self_healer.create_snapshot(new_state, self.vector_clock, merkle_root)
            
            # 11. 记录审计
            audit_entry = AuditEntry(
                transaction_id=str(uuid4()),
                timestamp=time.time(),
                source_role=self.config.node_id,
                destination_role=target,
                message_type="STATE_SYNC",
                delta_hash=hashlib.sha256(json.dumps(delta).encode()).hexdigest(),
                merkle_root_before="",  # 简化
                merkle_root_after=merkle_root,
                bandwidth_saved_bytes=bandwidth_saved,
                transmission_duration_ms=(time.time() - start_time) * 1000,
                signature_verified=True,
                tamper_detected=False
            )
            self.audit_logger.log(audit_entry)
        
        return SyncResult(
            success=success,
            bandwidth_reduction=bandwidth_saved / old_size if old_size > 0 else 0,
            latency_ms=(time.time() - start_time) * 1000
        )
    
    async def recover_from_failure(self) -> dict:
        """从失败中恢复"""
        snapshot = self.self_healer.find_latest_valid_snapshot()
        if snapshot:
            return self.self_healer.recover(snapshot.snapshot_id)
        return {}
```

---

## 四、完整项目结构

```
qcm-mvp/
│
├── core/                          # 核心引擎
│   ├── __init__.py
│   ├── engine.py                  # QCM主引擎
│   ├── role_engine.py             # 角色引擎
│   ├── context.py                # 上下文管理
│   └── exceptions.py              # 异常定义
│
├── ghost_channel/                 # ★ 幽灵通道协议层（核心）
│   ├── __init__.py
│   ├── manager.py                 # 通道管理器
│   ├── delta_syncer.py            # A: Delta增量同步
│   ├── vector_clock.py            # B: 因果排序
│   ├── crypto_engine.py           # C: 加密传输
│   ├── merkle_tree.py             # D: 完整性验证
│   ├── audit_logger.py            # E: 审计追踪
│   ├── self_healer.py             # F: 自愈恢复
│   ├── semantic_matcher.py        # G: 语义匹配（可选MVP）
│   └── types.py                   # 类型定义
│
├── roles/                         # 角色系统
│   ├── __init__.py
│   ├── base.py                   # 角色基类
│   ├── secretary.py              # 秘书长
│   ├── researcher.py             # 研究员
│   ├── architect.py              # 架构师
│   └── manager.py                # 角色管理器
│
├── models/                        # AI模型接入
│   ├── __init__.py
│   ├── interface.py              # 模型接口
│   ├── openai_adapter.py         # OpenAI适配器
│   └── registry.py               # 模型注册
│
├── storage/                       # 存储层
│   ├── __init__.py
│   ├── state_store.py            # 状态存储
│   ├── snapshot_store.py         # 快照存储
│   └── audit_store.py            # 审计存储
│
├── api/                           # 对外API
│   ├── __init__.py
│   ├── routes.py                 # Flask路由
│   └── schemas.py                # 请求/响应模式
│
├── web/                           # 前端
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── config/                        # 配置
│   ├── __init__.py
│   ├── config.py                 # 配置类
│   └── defaults.yaml             # 默认配置
│
├── tests/                         # 测试
│   ├── __init__.py
│   ├── test_delta.py
│   ├── test_vector_clock.py
│   ├── test_crypto.py
│   ├── test_merkle.py
│   ├── test_audit.py
│   └── test_integration.py
│
├── requirements.txt
├── main.py                        # 入口
└── README.md
```

---

## 五、MVP功能矩阵

| 功能 | 实现 | 幽灵通道能力 |
|------|------|-------------|
| 与AI对话 | ✅ 基础实现 | - |
| 角色切换 | ✅ 基础实现 | - |
| 记住对话 | ✅ 基础实现 | Delta同步 + 审计 |
| 只传变化 | ✅ MVP实现 | Delta增量同步 |
| 因果顺序 | ✅ MVP实现 | VectorClock因果排序 |
| 数据加密 | ✅ MVP实现 | AES-256-GCM加密 |
| 完整性验证 | ✅ MVP实现 | Merkle Tree |
| 审计记录 | ✅ MVP实现 | AuditLogger |
| 失败恢复 | ✅ MVP实现 | SelfHealer快照 |

---

## 六、核心接口规格

### 6.1 GhostChannelManager接口

```python
class GhostChannelManager(ABC):
    """幽灵通道管理器接口"""
    
    async def sync_state(self, new_state: dict, target: str) -> SyncResult:
        """同步状态"""
        pass
    
    async def receive_state(self, source: str) -> dict:
        """接收状态"""
        pass
    
    async def recover_from_failure(self) -> dict:
        """从失败恢复"""
        pass
    
    def get_audit_log(self, filters: dict) -> list[AuditEntry]:
        """获取审计日志"""
        pass
    
    def get_current_state(self, node: str) -> dict:
        """获取当前状态"""
        pass
    
    def verify_integrity(self, node: str) -> bool:
        """验证完整性"""
        pass
```

### 6.2 SyncResult返回结果

```python
@dataclass
class SyncResult:
    success: bool
    bandwidth_reduction: float      # 带宽降低比例 (0.0-1.0)
    latency_ms: float               # 延迟 (毫秒)
    consistency_verified: bool      # 一致性验证
    changes_applied: int           # 应用的变更数
    errors: list[str]              # 错误列表
    transaction_id: str            # 事务ID
    merkle_root: str               # Merkle根
    audit_entry: AuditEntry        # 审计条目
```

---

## 七、部署配置

```yaml
# config.yaml
ghost_channel:
  node_id: "qcm_primary"
  
  # Delta同步配置
  delta:
    enabled: true
    compression: true
    compression_level: 9
  
  # 因果排序配置
  vector_clock:
    enabled: true
    max_clock_drift: 1000
  
  # 加密配置
  crypto:
    enabled: true
    algorithm: "AES-256-GCM"
    key_derivation: "PBKDF2-SHA256"
    iterations: 100000
  
  # Merkle树配置
  merkle:
    enabled: true
    hash_algorithm: "SHA-256"
  
  # 审计配置
  audit:
    enabled: true
    storage: "./data/audit.log"
    retention_days: 90
  
  # 自愈配置
  self_heal:
    enabled: true
    max_snapshots: 10
    snapshot_interval: 300  # 秒

roles:
  - secretary
  - researcher
  - architect

models:
  default: "openai"
  openai:
    api_key: ${OPENAI_API_KEY}
    model: "gpt-4"
```

---

## 八、验证标准

### MVP必须满足：

```
[ ] Delta同步工作正常
[ ] 向量时钟正确追踪因果
[ ] 数据加密/解密正确
[ ] Merkle根正确计算
[ ] 审计日志正确记录
[ ] 快照创建和恢复正常
[ ] 角色切换正常
[ ] AI对话正常
[ ] 整体系统可运行
```

---

## 九、下一步

**确认后，我将开始编写代码**：
1. 创建项目结构
2. 实现幽灵通道协议层（核心）
3. 实现角色系统
4. 实现AI模型接入
5. 实现前端界面

**请确认：
1. 这个严谨的架构设计是否满足需求？**
2. **是否现在开始编写代码？**
