# 部署说明（Vercel）

把「外卖门店诊断」部署到云端，别人打开网址就能用，你不再需要 `python main.py`。

## 架构

| 文件 | 作用 | 跑在哪 |
|---|---|---|
| index.html | 前端：表单 + 规则引擎 + 批量诊断 | 静态，所有环境通用 |
| api/report.js | AI 报告接口（调 DeepSeek / 通义） | Vercel（Node 函数） |
| main.py | AI 报告接口（本机调试用） | 你本机（Python） |

规则引擎在前端 `index.html` 里，改它线上和本机都会生效。

## 一次性部署步骤（约 15 分钟）

1. **提交到 git**（文件已暂存，只需设身份并提交）：
   ```bash
   cd d:\shop_diagnosis
   git config --global user.name "你的名字"
   git config --global user.email "你的邮箱"
   git commit -m "第一版：外卖门店诊断"
   ```

2. **推到 GitHub**：
   - 浏览器打开 github.com → New repository → 名字 `shop-diagnosis` → **不要**勾选 README / gitignore → Create
   - 回到终端（把 `<你的用户名>` 换成你自己的）：
   ```bash
   git remote add origin https://github.com/<你的用户名>/shop-diagnosis.git
   git branch -M main
   git push -u origin main
   ```

3. **连 Vercel**：
   - vercel.com 用 GitHub 账号登录 → Add New Project → 选 `shop-diagnosis` → 直接 Deploy
   - 等 1 分钟，得到网址 `https://xxx.vercel.app`

4. **配置服务端 Key（让别人不用填）**：
   - Vercel 项目 → Settings → Environment Variables → 添加
     - `LLM_API_KEY` = 你的 DeepSeek Key（`sk-...`）
     - （可选）`LLM_PROVIDER` = `deepseek`
   - Save → Deployments → 对最新部署点 Redeploy
   - 之后别人打开网址，点「生成 AI 报告」无需填 Key

5. **把网址发给别人**，完事。

## 关于 API Key 的两种模式

- **服务端统一 Key**（推荐给小范围熟人试用）：配置 `LLM_API_KEY`，别人不用填，但费用都算你的。
- **各自填自己的 Key**：不配 `LLM_API_KEY`，页面里的 Key 输入框留给大家自己填。

⚠️ 带服务端 Key 的链接不要发到公开大群，否则会被人白嫖你的额度。
