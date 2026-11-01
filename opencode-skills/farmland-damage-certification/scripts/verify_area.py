#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
耕地破坏文书面积校验器
从 config.json 与已生成的 docx 做六层面积校验，全部 PASS 才算可交付。

用法：
    python verify_area.py config.json                  # 按配置推断两份 docx 路径
    python verify_area.py config.json a.docx b.docx    # 显式指定要校验的 docx

校验层：
  L1 地块级：每地块分项之和 = 地块面积
  L2 汇总：  各地类分项之和 = 总面积
  L3 平方米：调查报告分项㎡之和 = 总㎡；总㎡÷10000 ≈ 汇总公顷
  L4 亩数：  每项 = 公顷×15 四舍五入 2 位；分项亩之和 = 合计亩
  L5 破坏面：damage_ha ≤ 耕地面积
  L6 文书：  逐对验算文中每一处"X公顷（合Y亩）"，并核对总面积声明
"""
import os
import re
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx import Document  # noqa: E402

from gen_docs import (  # noqa: E402
    D, LAND_TYPES, aggregate, ha2mu, q4, load_config,
)

PAIR_RE = re.compile(r'([0-9]+\.[0-9]{4})公顷（合([0-9]+\.[0-9]{2})亩）')
TOTAL_RE = re.compile(r'总面积([0-9]+\.[0-9]{4})公顷（合([0-9]+\.[0-9]{2})亩）')

results = []


def chk(name, actual, expect, tol=D('0.00005'), quiet=False):
    ok = abs(D(str(actual)) - D(str(expect))) <= tol
    results.append((ok, name, str(actual), str(expect)))
    if not quiet:
        print('  %s %-54s 实际=%-12s 期望=%s'
              % ('OK  ' if ok else 'FAIL', name, actual, expect))
    return ok


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    cfg = load_config(sys.argv[1])
    plots = cfg['plots']
    agg = aggregate(plots)

    print('=' * 80)
    print('L1 地块级校验')
    print('=' * 80)
    for p in plots:
        pid = p.get('id', '?')
        nong = (D(str(p.get('gengdi', 0))) + D(str(p.get('guoyuan', 0)))
                + D(str(p.get('qiaomu_lindi', 0))) + D(str(p.get('qita_lindi', 0)))
                + D(str(p.get('nongdao', 0))))
        chk('%s 农用地分项之和 = 总面积 - 建设用地'
            % pid, nong + D(str(p.get('jianshe', 0))), p['area'])

    print('=' * 80)
    print('L2 汇总校验（公顷）')
    print('=' * 80)
    chk('各地类分项之和 = 总面积',
        sum(agg[k] for k, _ in LAND_TYPES), agg['area'])
    declared = cfg['case'].get('total_area_ha')
    if declared is not None:
        chk('配置声明总面积 = 地类汇总', declared, agg['area'])
    for k, name in LAND_TYPES:
        print('  %-6s %10s 公顷' % (name, q4(agg[k])))

    print('=' * 80)
    print('L3 平方米校验（对照执法局调查报告）')
    print('=' * 80)
    survey = cfg.get('survey_m2') or {}
    if survey:
        m2_total = D(str(survey.get('total', 0)))
        parts = {k: v for k, v in survey.items() if k != 'total'}
        if parts:
            chk('调查报告分项㎡之和 = 总㎡',
                sum(D(str(v)) for v in parts.values()), m2_total, tol=D('0.01'))
        if m2_total:
            chk('总㎡ ÷ 10000 ≈ 地类汇总公顷',
                m2_total / D('10000'), agg['area'], tol=D('0.0001'))
    else:
        print('  （配置未提供 survey_m2，跳过）')

    print('=' * 80)
    print('L4 公顷→亩换算校验（×15 四舍五入 2 位，禁截断）')
    print('=' * 80)
    mu_sum = D('0')
    for k, name in LAND_TYPES:
        mu = ha2mu(agg[k])
        mu_sum += mu
        print('  %-6s %8s × 15 = %-9s → %s 亩'
              % (name, q4(agg[k]), D(str(agg[k])) * D('15'), mu))
    print('  %-6s %8s × 15 = %-9s → %s 亩'
          % ('合计', q4(agg['area']), D(str(agg['area'])) * D('15'), ha2mu(agg['area'])))
    chk('分项亩数之和 = 合计亩数', mu_sum, ha2mu(agg['area']))

    print('=' * 80)
    print('L5 破坏面积合理性')
    print('=' * 80)
    dmg = D(str(cfg['case']['damage_ha']))
    ok = dmg <= agg['gengdi'] + D('0.00005')
    results.append((ok, '破坏面积 ≤ 耕地总面积', str(dmg), str(q4(agg['gengdi']))))
    print('  %s 破坏面积 %s ≤ 耕地 %s'
          % ('OK  ' if ok else 'FAIL', dmg, q4(agg['gengdi'])))

    print('=' * 80)
    print('L6 文书文本校验（逐对验算"X公顷（合Y亩）"）')
    print('=' * 80)
    if len(sys.argv) > 2:
        files = sys.argv[2:]
    else:
        names = cfg['case'].get('filenames', {})
        out = cfg['meta']['out_dir']
        files = [
            os.path.join(out, names.get('lunzheng',
                         '%s耕地破坏论证意见.docx' % cfg['case']['subject'])),
            os.path.join(out, names.get('rending',
                         '%s破坏耕地认定意见.docx' % cfg['case']['subject'])),
        ]

    for fp in files:
        short = os.path.basename(fp)
        if not os.path.exists(fp):
            results.append((False, '%s 文件存在' % short, '未找到', '存在'))
            print('  FAIL %s 不存在' % short)
            continue
        text = '\n'.join(p.text for p in Document(fp).paragraphs)
        pairs = PAIR_RE.findall(text)
        print('\n-- %s（%d 处面积对）' % (short, len(pairs)))
        for ha, mu in pairs:
            expect = ha2mu(ha)
            ok = (expect == D(mu))
            results.append((ok, '%s %s公顷→%s亩' % (short, ha, mu), expect, mu))
            print('  %s %s 公顷 → 应 %s 亩，文书 %s 亩'
                  % ('OK  ' if ok else 'FAIL', ha, expect, mu))
        m = TOTAL_RE.search(text)
        if m:
            chk('%s 总面积公顷' % short, m.group(1), agg['area'])
            chk('%s 总面积亩' % short, m.group(2), ha2mu(agg['area']))
        else:
            results.append((False, '%s 缺少"总面积...公顷（合...亩）"声明' % short, '-', '-'))

    print('=' * 80)
    fails = [r for r in results if not r[0]]
    print('校验项 %d，通过 %d，失败 %d'
          % (len(results), len(results) - len(fails), len(fails)))
    if fails:
        print('\n失败明细：')
        for ok, name, a, b in fails:
            print('  FAIL %-56s 实际=%s 期望=%s' % (name, a, b))
        sys.exit(1)
    print('全部通过：地块级 → 汇总 → 平方米 → 亩数 → 破坏面积 → 文书文本 六层闭合。')


if __name__ == '__main__':
    main()
