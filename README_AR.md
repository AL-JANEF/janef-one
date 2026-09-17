<p align="center">
  <img src="./assets/al-janef-logo.png" alt="AL-JANEF" width="430">
</p>

<h1 align="center">JANEF ONE</h1>
<p align="center"><strong>نواة واحدة. لكل وكيل.</strong></p>
<p align="center">
  مهارة Agent Skill محمولة مع Runtime مقسّى بلغة Python لتوجيه المهام، وإدارة الحالة، وWorkGraph، وفحص المهارات، والتفويض، والأدلة، والتحقق القابل لإعادة الإنتاج.
</p>

<p align="center"><a href="./README.md">English README</a></p>

## ما هو JANEF ONE؟

JANEF ONE هو **طبقة أوركسترا رئيسية** للعمل بالوكلاء. بدل تحميل عشرات المهارات العامة المتداخلة في السياق، يحافظ على Kernel صغير يتحكم في التوجيه وترتيب الصلاحيات والتحقق، ثم يحمّل المهارة المتخصصة فقط عندما تضيف معرفة أو قدرة فريدة.

```text
افهم → احسم التعليمات → وجّه → اجمع → نفّذ → تحقّق → أبلغ
```

لا يتجاوز JANEF ONE تعليمات النظام الفعلية أو سياسات السلامة أو الصلاحيات أو الأدوات المتاحة في بيئة التشغيل.

## قدرات الإصدار 1.0

- Instruction Resolver لحسم الأولوية والتعارض بصورة حتمية.
- Capability Registry لاكتشاف القدرات المتاحة فعليًا.
- Context Governor لضبط الميزانية وإزالة التكرار.
- Persistent State بكتابة ذرية وسجل أحداث tamper-evident.
- WorkGraph لتنفيذ DAG مع dependencies وretries وverification gates.
- Recovery Manager لنقاط الاستعادة والفشل الجزئي.
- Multi-Agent Scheduler لتفويض مضبوط مبني على التبعيات.
- Skill Firewall لفحص المهارات قبل تحميلها.
- Skill Rating لتقييم القيمة والتداخل والمخاطر.
- Authorization Gate للعمليات ذات الأثر الخارجي أو غير القابلة للعكس.
- Evidence Ledger لمنع ادعاءات الإنجاز بلا دليل.
- Benchmark Harness وبوابات Regression قابلة لإعادة التنفيذ.

## البدء السريع

```bash
git clone https://github.com/AL-JANEF/janef-one.git
cd janef-one
python3 -m pip install -e '.[dev]'
python3 scripts/quality_gate.py
janef-one --version
```

## معيار الإصدار

مصطلح `10/10` في هذا المستودع يعني أن **جميع بوابات الإصدار المعرفة داخل المشروع نجحت**: الاختبارات، التغطية، benchmark الحتمي، self-firewall، clean install، CLI smoke، recovery، reproducible packaging، وسلامة الإصدار. وهو ليس ادعاءً بأن المشروع لا يمكن التفوق عليه في كل مهمة مستقبلية.

## الأمان

تُعامل المهارات الخارجية ومصادر prompt snapshots كمدخلات غير موثوقة. لا تُضمّن corpora خارجية في الإصدارات العامة. راجع `SECURITY.md` و`NOTICE`.

## الترخيص

Apache License 2.0.

<p align="center"><strong>AL-JANEF · CODE • CREATE • BUILD</strong></p>
