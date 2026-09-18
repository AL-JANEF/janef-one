<p align="center">
  <img src="./assets/social-preview.png" alt="JANEF ONE" width="100%">
</p>

<h1 align="center">JANEF ONE</h1>
<p align="center"><strong>طبقة تحكم واحدة لوكلاء الذكاء الاصطناعي.</strong></p>
<p align="center">Claude Code · Codex · Gemini CLI · Cursor · OpenCode</p>

JANEF ONE نواة Orchestration محمولة لتنظيم التوجيه، السياق، WorkGraphs، الوكلاء المتعددين، صلاحيات العمليات الحساسة، فحص المهارات، الأدلة والتحقق من الإنجاز.

[English](./README.md) · [Demo](./docs/DEMO.md) · [Architecture](./references/ARCHITECTURE.md) · [Security](./SECURITY.md)

## ابدأ سريعًا

```bash
git clone https://github.com/AL-JANEF/janef-one.git
cd janef-one
python3 scripts/validate.py
PYTHONPATH=runtime python3 -m janef_one route "Review this repository for release readiness"
```

أو شغّل العرض السريع:

```bash
bash examples/quick-demo.sh
```

## الدليل التقني للإصدار v1.0.1

- **113/113** اختبارات Unit/Integration ناجحة.
- **1,970/1,970** فحوص Benchmark حتمية ناجحة.
- **90.31%** Runtime coverage.
- **100/100** Self-firewall مع قرار `allow`.
- CI ناجح على Python 3.11 و3.12 و3.13.
- CodeQL مفعل.
- بناء Release قابل لإعادة الإنتاج بنفس SHA-256.

هذه الأرقام تخص بوابات المشروع الحتمية، ولا تعني ادعاء التفوق على كل إطار Agent في كل مهمة.

## لماذا JANEF ONE؟

بدل تكديس مهارات عامة متداخلة داخل الـcontext، يحتفظ JANEF ONE بنواة تحكم صغيرة ويحمّل القدرات المتخصصة فقط عندما تضيف قيمة فريدة. كما يفصل التنفيذ عن التحقق، ويعامل المهارات الخارجية والمدخلات المسترجعة كمصادر غير موثوقة حتى تجتاز البوابات المطلوبة.

## أهم القدرات

- Instruction Resolver
- Capability Registry
- Context Governor
- Persistent State + Recovery
- WorkGraph
- Multi-Agent Scheduler
- Skill Firewall
- Skill Rating
- Authorization Gate
- Evidence Ledger
- Benchmark / Regression Harness

## المجتمع

إذا استفدت من JANEF ONE، ضع **Star** للمستودع وشارك تجربتك عبر Showcase issue. هذا يساعد المشروع على الوصول لمطورين آخرين.

Apache-2.0 · Built by **AL-JANEF**
