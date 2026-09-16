// Vercel 无服务器函数：POST /api/report
// 职责：接收诊断结果，代理调用 DeepSeek / 通义千问，返回 AI 诊断报告。
// API Key 优先用请求里传来的；没有则回退到服务端环境变量 LLM_API_KEY（部署后配置）。
const PROVIDERS = {
  deepseek: { url: 'https://api.deepseek.com/chat/completions', model: 'deepseek-chat' },
  qwen: { url: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', model: 'qwen-plus' },
};

const SYSTEM_PROMPT = '你是外卖代运营的资深运营顾问，擅长把数据问题翻译成加盟商听得懂的诊断报告。输出使用 Markdown，语气专业但不吓人。不要使用表格（不要出现竖线 | 分隔符），用标题、列表和加粗即可。';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, error: '仅支持 POST' });
  }

  const body = req.body || {};
  const provider = PROVIDERS[body.provider] ? body.provider : 'deepseek';
  const apiKey = (body.apiKey || '').trim() || (process.env.LLM_API_KEY || '').trim();
  const model = body.model || process.env.LLM_MODEL || PROVIDERS[provider].model;
  const prompt = body.prompt || '';

  if (!apiKey) {
    return res.status(400).json({ ok: false, error: '服务端未配置 LLM_API_KEY 环境变量' });
  }
  if (!prompt) {
    return res.status(400).json({ ok: false, error: '缺少诊断内容（请先点击「开始诊断」）' });
  }

  try {
    const upstream = await fetch(PROVIDERS[provider].url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + apiKey },
      body: JSON.stringify({
        model,
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: prompt },
        ],
        temperature: 0.7,
        stream: false,
      }),
    });

    const text = await upstream.text();
    let data;
    try { data = JSON.parse(text); } catch (e) {
      return res.status(502).json({ ok: false, error: '上游返回非 JSON：' + text.slice(0, 200) });
    }

    if (!upstream.ok) {
      return res.status(upstream.status).json({ ok: false, error: 'LLM 接口返回 ' + upstream.status + '：' + JSON.stringify(data).slice(0, 300) });
    }

    const content = data && data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content;
    if (!content) {
      return res.status(502).json({ ok: false, error: '响应格式异常：' + text.slice(0, 300) });
    }

    return res.status(200).json({ ok: true, report: content });
  } catch (e) {
    return res.status(500).json({ ok: false, error: '请求失败：' + (e && e.message ? e.message : e) });
  }
}
