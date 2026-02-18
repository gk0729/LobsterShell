# 貢獻指南

感謝你對 LobsterShell 的興趣！

---

## 如何貢獻

### 1. 報告問題

如果你發現 bug 或有功能建議：
1. 在 GitHub Issues 中搜索是否已有相關問題
2. 如果沒有，創建新 Issue
3. 提供詳細的描述和重現步驟

### 2. 提交代碼

1. Fork 本倉庫
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 創建 Pull Request

### 3. 改進文檔

文檔改進是最容易的貢獻方式：
- 修正拼寫錯誤
- 添加示例
- 改進解釋
- 翻譯成其他語言

---

## 開發環境

### Soul（蝦魂）

```bash
cd soul/soul_architecture
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # 目前無依賴
python3 test_core.py
```

### Shell（蝦殼）

```bash
cd shell
python3 -m venv venv
source venv/bin/activate
pip install -e .
python3 -m pytest
```

---

## 代碼風格

- Python: PEP 8
- 使用有意義的變量名
- 添加適當的註釋
- 編寫測試

---

## 行為準則

- 尊重所有貢獻者
- 保持友好和專業
- 接受建設性批評
- 關注對社區最有利的事情

---

感謝你的貢獻！🦞
