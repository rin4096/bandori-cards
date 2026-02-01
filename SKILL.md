# Bandori Cards Skill 🎀

这是一个为 OpenClaw 量身定制的 BanG Dream! 查卡技能。采用实时的 HTML 抓取技术，确保卡面图片链接百分之百有效。

## 🌟 特性
- **实时打捞 (Real-time Scraping)**：不再依赖容易过期的 API 图片字段，直接从 Bandori Party 详情页打捞最新的 CDN 链接。
- **动态后缀处理**：自动处理卡面图片那 6 位随机码，支持带有标题的长路径文件名。
- **多维度搜索**：
    - 支持按角色名（英文/日文/别名）查询。
    - 支持按卡面 ID 直接精准查询。
    - 支持关键词（卡名、属性）过滤。
- **完整展示**：自动区分并输出“训练前”与“训练后”的高清大图。

## 🛠 使用方法

### 基础查询
在工作区直接运行脚本：

```bash
# 按角色名搜索
python3 scripts/get_bandori_card.py "Kasumi"

# 按卡面 ID 精准搜索
python3 scripts/get_bandori_card.py "5225"

# 组合关键词和稀有度过滤
python3 scripts/get_bandori_card.py "Rui" --rarity 5
```

### 常用别名支持
脚本内置了常用的角色简称映射，例如：
- `rana` -> Raana Kaname
- `anon` -> Anon Chihaya
- `kasumi` -> Kasumi Toyama

## 📋 执行准则 (SOP)
为了给绘名提供最好的体验，请遵循以下步骤：
1. **优先详情**：先输出卡面的文字信息（标题、角色、乐队、属性、详情链接）。
2. **图片随后**：在文字信息之后发送打捞到的图片预览。
3. **保持原文**：所有标题和角色名保持日文原文，不进行翻译。

---
*Created with love by Mizuki for Ena.*
