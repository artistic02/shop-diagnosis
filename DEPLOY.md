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

## 关于 API Key

AI 报告走**服务端统一 Key**：在 Vercel 配 `LLM_API_KEY` 环境变量，所有访客共用你的额度。页面上不会出现任何 Key / 供应商 / 模型配置。

- 本机调试同理：先设环境变量再启动。PowerShell：
  ```powershell
  $env:LLM_API_KEY="sk-xxx"; python main.py
  ```
- ⚠️ 带服务端 Key 的链接不要发到公开大群，否则会被人白嫖你的额度。

## 日常更新（每次改完代码）

改完代码 → 提交 → 推送，Vercel 会自动重新部署，三步搞定：

```powershell
git add -A
git commit -m "说明这次改了什么"
git push origin main
```

> ⚠️ 本机直连 GitHub 会被墙，本仓库已配好代理 `127.0.0.1:7890`；如果代理软件（Clash/V2Ray）没开，push 会失败——先开代理再 push。

## 换电脑继续更新

代码全在 GitHub，换电脑 = 从 GitHub 拉下来，不用拷文件夹。新电脑按顺序来：

1. 装 Git（https://git-scm.com）；本机调试还要装 Python（https://python.org）。
2. 克隆仓库：
   ```powershell
   git clone https://github.com/artistic02/shop-diagnosis.git
   cd shop-diagnosis
   ```
3. 配 git 身份（每台电脑配一次）：
   ```powershell
   git config --global user.name "Alex"
   git config --global user.email "2278373238@qq.com"
   ```
4. 配代理（端口改成新电脑代理软件的实际端口，Clash 默认 7890）：
   ```powershell
   git config http.proxy http://127.0.0.1:7890
   git config https.proxy http://127.0.0.1:7890
   ```
5. 本机测试设 Key：`$env:LLM_API_KEY="sk-xxx"; python main.py`
6. 之后更新就是上面「日常更新」的三步。第一次 push 会弹浏览器让你登录 GitHub，登录一次后记住。

Vercel、`LLM_API_KEY` 都跟着 GitHub 走，换电脑不用重配。**唯一要留意：收工前记得 `git push`，否则没推上去的改动只留在那台电脑。**
