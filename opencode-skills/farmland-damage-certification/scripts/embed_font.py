#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从参考原件提取嵌入字体，注入目标 docx。

用法：
    python embed_font.py 目标.docx 参考原件.docx               # 默认嵌入「方正大标宋简体」
    python embed_font.py 目标.docx 参考原件.docx 仿宋 楷体      # 指定多个字体

背景：
    红头用的「方正大标宋简体」多数机器没装。原件靠 word/fonts/*.odttf
    嵌入字体保证任何机器都能正确显示；不嵌入，WPS/Word 会用替代字体渲染，
    红头字形与原件不同。

原理：
    odttf 是混淆过的字体子集，fontKey(GUID) 与文件内容绑定。
    从原件整条复制 <w:font> 节点 + odttf 文件 + rels 关系即可正确解密。
    子集只含原件用到的字符，因此仅适用于文字内容相同的文头。
"""
import os
import re
import shutil
import sys
import tempfile
import zipfile

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
ODTTF_CT = ('application/vnd.openxmlformats-officedocument.'
            'obfuscatedFont')

# CT_Settings 中排在 embedTrueTypeFonts 之前的元素（用于确定插入位置）
_BEFORE_EMBED = {
    'writeProtection', 'view', 'zoom', 'removePersonalInformation',
    'removeDateAndTime', 'doNotDisplayPageBoundaries', 'displayBackgroundShape',
    'printPostScriptOverText', 'printFractionalCharacterWidth', 'printFormsData',
}


def _font_node(font_table_xml, font_name):
    pat = re.compile(
        r'<w:font\s+w:name="%s"\s*>(.*?)</w:font>' % re.escape(font_name), re.S)
    return pat.search(font_table_xml)


def _embed_info(font_body):
    m = re.search(r'<w:embedRegular\s+r:id="(rId\d+)"\s+w:fontKey="(\{[0-9A-Fa-f-]+\})"\s*/>',
                  font_body)
    if m is None:
        m = re.search(r'<w:embedRegular\s+w:fontKey="(\{[0-9A-Fa-f-]+\})"\s+r:id="(rId\d+)"\s*/>',
                      font_body)
        if m is None:
            return None
        return m.group(2), m.group(1)
    return m.group(1), m.group(2)


def _rel_target(rels_xml, rid):
    m = re.search(r'<Relationship\s+Id="%s"[^>]*Target="([^"]+)"' % rid, rels_xml)
    if m is None:
        m = re.search(r'<Relationship[^>]*Target="([^"]+)"[^>]*Id="%s"' % rid, rels_xml)
    return m.group(1) if m else None


def _next_rid(rels_xml):
    used = [int(x) for x in re.findall(r'Id="rId(\d+)"', rels_xml)]
    return 'rId%d' % (max(used) + 1 if used else 1)


def _add_settings_flag(settings_xml):
    changed = False
    for node in ('embedTrueTypeFonts', 'saveSubsetFonts'):
        if '<w:%s/>' % node in settings_xml:
            continue
        insert_at = None
        for m in re.finditer(r'<w:(\w+)[\s/>]', settings_xml):
            if m.group(1) in _BEFORE_EMBED:
                end = settings_xml.find('>', m.start())
                if settings_xml[end - 1] == '/':
                    insert_at = end + 1
                else:
                    close = settings_xml.find('</w:%s>' % m.group(1), end)
                    insert_at = (close + len('</w:%s>' % m.group(1))
                                 if close >= 0 else end + 1)
        flag = '<w:%s/>' % node
        if insert_at is not None:
            settings_xml = settings_xml[:insert_at] + flag + settings_xml[insert_at:]
        else:
            settings_xml = settings_xml.replace('</w:settings>', flag + '</w:settings>')
        changed = True
    return settings_xml, changed


def embed(target, source, font_names):
    zt = zipfile.ZipFile(target)
    zs = zipfile.ZipFile(source)

    src_font_table = zs.read('word/fontTable.xml').decode('utf-8')
    src_rels = zs.read('word/_rels/fontTable.xml.rels').decode('utf-8')

    dst_font_table = zt.read('word/fontTable.xml').decode('utf-8')
    dst_rels_path = 'word/_rels/fontTable.xml.rels'
    if dst_rels_path in zt.namelist():
        dst_rels = zt.read(dst_rels_path).decode('utf-8')
    else:
        dst_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    '</Relationships>')

    new_files = {}
    embedded = []
    for name in font_names:
        node = _font_node(src_font_table, name)
        if node is None:
            print('  [跳过] 参考件未嵌入字体：%s' % name)
            continue
        info = _embed_info(node.group(1))
        if info is None:
            print('  [跳过] %s 无 embedRegular 条目' % name)
            continue
        src_rid, font_key = info
        target_path = _rel_target(src_rels, src_rid)
        if target_path is None:
            print('  [跳过] 找不到 %s 对应的字体文件关系' % name)
            continue
        src_part = 'word/' + target_path.replace('../', '')
        if src_part not in zs.namelist():
            print('  [跳过] 参考件缺少 %s' % src_part)
            continue

        dst_rid = _next_rid(dst_rels)
        dst_part = 'word/fonts/font%d.odttf' % (len(new_files) + 1)
        new_files[dst_part] = zs.read(src_part)
        dst_rels = dst_rels.replace(
            '</Relationships>',
            '<Relationship Id="%s" Type="%s/font" Target="fonts/font%d.odttf"/></Relationships>'
            % (dst_rid, R, len(new_files)))
        embed_tag = '<w:embedRegular r:id="%s" w:fontKey="%s"/>' % (dst_rid, font_key)

        existing = _font_node(dst_font_table, name)
        if existing is not None:
            body = existing.group(1)
            if 'embedRegular' in body:
                body = re.sub(r'<w:embedRegular[^/]*/>', '', body)
            dst_font_table = dst_font_table.replace(
                existing.group(0),
                '<w:font w:name="%s">%s%s</w:font>' % (name, body, embed_tag))
        else:
            dst_font_table = dst_font_table.replace(
                '</w:fonts>',
                '<w:font w:name="%s"><w:charset w:val="86"/>'
                '<w:family w:val="auto"/><w:pitch w:val="variable"/>%s</w:font></w:fonts>'
                % (name, embed_tag))
        embedded.append((name, dst_part, len(new_files[dst_part]), font_key))

    if not embedded:
        print('没有可嵌入的字体，未修改文件。')
        return False

    content_types = zt.read('[Content_Types].xml').decode('utf-8')
    if 'Extension="odttf"' not in content_types:
        content_types = content_types.replace(
            '</Types>',
            '<Default Extension="odttf" ContentType="%s"/></Types>' % ODTTF_CT)

    settings = zt.read('word/settings.xml').decode('utf-8')
    settings, _ = _add_settings_flag(settings)

    replace = {
        'word/fontTable.xml': dst_font_table.encode('utf-8'),
        '[Content_Types].xml': content_types.encode('utf-8'),
        'word/settings.xml': settings.encode('utf-8'),
    }

    theme_part = 'word/theme/theme1.xml'
    if theme_part in zs.namelist() and theme_part in zt.namelist():
        replace[theme_part] = zs.read(theme_part)
    if dst_rels_path in zt.namelist():
        replace[dst_rels_path] = dst_rels.encode('utf-8')
    else:
        new_files[dst_rels_path] = dst_rels.encode('utf-8')

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    tmp.close()
    with zipfile.ZipFile(tmp.name, 'w', zipfile.ZIP_DEFLATED) as out:
        for item in zt.infolist():
            data = replace.get(item.filename) or zt.read(item.filename)
            out.writestr(item.filename, data)
        for part, data in new_files.items():
            if part not in zt.namelist():
                out.writestr(part, data)

    zt.close()
    zs.close()
    shutil.move(tmp.name, target)

    for name, part, size, key in embedded:
        print('  嵌入 %s → %s (%d B, fontKey=%s)' % (name, part, size, key))
    return True


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    target, source = sys.argv[1], sys.argv[2]
    fonts = sys.argv[3:] or ['方正大标宋简体']
    if not os.path.exists(target):
        sys.exit('目标文件不存在：%s' % target)
    if not os.path.exists(source):
        sys.exit('参考文件不存在：%s' % source)
    ok = embed(target, source, fonts)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
