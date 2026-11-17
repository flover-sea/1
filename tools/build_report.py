#!/usr/bin/env python3
"""Build the Chinese homework report from its editable Markdown and MATLAB files.

Requires python-docx, matplotlib and Pillow. Run: python3 tools/build_report.py
"""
from __future__ import annotations

from pathlib import Path
import os
import re
import tempfile
import zipfile

# Keep runtime caches outside the checkout and writable in managed environments.
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "ocean-report-mpl"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "ocean-report-cache"))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '海洋技术作业_完整解答.docx'
FONT_CJK = 'Noto Sans CJK SC'


def set_font(run, size=11, bold=None, mono=False):
    run.font.name = 'Consolas' if mono else 'Calibri'
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), FONT_CJK)


def set_section(section, landscape=False):
    section.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    section.page_width = Cm(29.7 if landscape else 21)
    section.page_height = Cm(21 if landscape else 29.7)
    section.top_margin = Cm(1.2 if landscape else 1.8)
    section.bottom_margin = Cm(1.2 if landscape else 1.8)
    section.left_margin = section.right_margin = Cm(1.5 if landscape else 1.8)
    section.header_distance = section.footer_distance = Cm(0.6)


def inline(paragraph, text, size=11):
    """Preserve emphasis and code; expose reference URLs for print readers."""
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: f'{m[1]}（{m[2]}）', text)
    for token in re.split(r'(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)', text):
        if not token:
            continue
        if token.startswith('**') and token.endswith('**'):
            run = paragraph.add_run(token[2:-2]); set_font(run, size, bold=True)
        elif token.startswith('`') and token.endswith('`'):
            run = paragraph.add_run(token[1:-1]); set_font(run, size-1, mono=True)
        elif token.startswith('*') and token.endswith('*'):
            run = paragraph.add_run(token[1:-1]); set_font(run, size); run.italic = True
        else:
            run = paragraph.add_run(token); set_font(run, size)


def add_code(doc, source, size=8):
    for line in source.splitlines():
        p = doc.add_paragraph(style='Source Code')
        set_font(p.add_run(line or ' '), size, mono=True)


def add_formula(doc, latex, directory, number):
    latex = latex.replace(r'\le ', r'\leq ').replace(r'\le30', r'\leq 30')
    if latex.startswith('c(T,S,z)='):
        lines = [r'c(T,S,z)=1449.2+4.6T-0.055T^2+0.00029T^3',
                 r'\qquad +(1.34-0.01T)(S-35)+0.016z.']
    else:
        lines = [latex]
    fig = plt.figure(figsize=(10, 0.55 * len(lines)), dpi=220)
    for index, line in enumerate(lines):
        fig.text(0.01, 1-(index+0.65)/len(lines), '$'+line+'$', fontsize=16, va='center')
    image_path = directory / f'equation_{number:02d}.png'
    fig.savefig(image_path, transparent=True, bbox_inches='tight', pad_inches=0.08)
    plt.close(fig)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = False
    width, _ = Image.open(image_path).size
    p.add_run().add_picture(str(image_path), width=Inches(min(6.7, width/220)))


def add_table(doc, rows):
    table = doc.add_table(rows=1, cols=len(rows[0]))
    table.style = 'Table Grid'
    for c, value in zip(table.rows[0].cells, rows[0]):
        inline(c.paragraphs[0], value.replace('\\', '/'), 9.5)
        for run in c.paragraphs[0].runs:
            run.bold = True
        shading = OxmlElement('w:shd'); shading.set(qn('w:fill'), 'E8EFF6')
        c._tc.get_or_add_tcPr().append(shading)
    for data in rows[1:]:
        for cell, value in zip(table.add_row().cells, data):
            inline(cell.paragraphs[0], value, 9.5)
    repeat = OxmlElement('w:tblHeader'); repeat.set(qn('w:val'), 'true')
    table.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in table.rows:
        # Keep each logical table row on one page, with the header repeated.
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.space_before = Pt(3)
                p.paragraph_format.line_spacing = 1.1


def add_diagram(doc, caption, path):
    section = doc.add_section(WD_SECTION_START.NEW_PAGE)
    set_section(section, landscape=True)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    inline(p, caption, 12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    width, height = Image.open(path).size
    target_width = min(10.2, 6.05 * width / height)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(str(path), width=Inches(target_width))


def add_markdown(doc, source, equation_dir):
    lines = source.splitlines()
    i = 0
    equation_number = 0
    landscape = False
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1; continue
        image_match = re.fullmatch(r'!\[([^\]]+)\]\(([^)]+)\)', line)
        if image_match:
            add_diagram(doc, image_match[1], ROOT / image_match[2])
            landscape = True
            i += 1; continue
        if landscape:
            set_section(doc.add_section(WD_SECTION_START.NEW_PAGE))
            landscape = False
        if line == r'\[':
            i += 1; formula = []
            while i < len(lines) and lines[i].strip() != r'\]':
                formula.append(lines[i].strip()); i += 1
            equation_number += 1
            add_formula(doc, ' '.join(formula), equation_dir, equation_number)
            i += 1; continue
        if line.startswith('```'):
            i += 1; source_lines = []
            while i < len(lines) and not lines[i].startswith('```'):
                source_lines.append(lines[i]); i += 1
            add_code(doc, '\n'.join(source_lines), 9)
            i += 1; continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith('|'):
                values = [v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', v) for v in values):
                    rows.append(values)
                i += 1
            add_table(doc, rows); continue
        match = re.match(r'^(#{1,3}) (.*)$', line)
        if match:
            doc.add_heading(match[2], level=len(match[1]))
            i += 1; continue
        if line.startswith('> '):
            p = doc.add_paragraph()
            inline(p, line[2:], 9.5)
            for run in p.runs:
                run.font.color.rgb = RGBColor.from_string('555555')
            i += 1; continue
        if line.startswith('- '):
            inline(doc.add_paragraph(style='List Bullet'), line[2:])
            i += 1; continue
        # Each Markdown paragraph may span multiple source lines.
        paragraph = [line]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|\||!\[|```|\\\[|- |>)', lines[i].strip()):
            paragraph.append(lines[i].strip()); i += 1
        inline(doc.add_paragraph(), ' '.join(paragraph))
    if landscape:
        set_section(doc.add_section(WD_SECTION_START.NEW_PAGE))


def main():
    doc = Document()
    set_section(doc.sections[0])
    normal = doc.styles['Normal']
    normal.font.name = 'Calibri'; normal.font.size = Pt(11)
    normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), FONT_CJK)
    normal.paragraph_format.line_spacing = 1.25
    normal.paragraph_format.space_after = Pt(7)
    code_style = doc.styles.add_style('Source Code', 1)
    code_style.font.name = 'Consolas'; code_style.font.size = Pt(8)
    code_style.paragraph_format.space_after = Pt(0)
    code_style.paragraph_format.line_spacing = 1
    for name in ['Heading 1', 'Heading 2', 'Heading 3']:
        style = doc.styles[name]
        style.font.color.rgb = RGBColor.from_string('17365D')
        style.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), FONT_CJK)
    header = doc.sections[0].header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_font(header.add_run('海洋技术作业 · MH370 搜寻与海水声速分析'), 8)
    footer = doc.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE')
    footer._p.append(field)
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(title.add_run('海洋技术作业：两题完整解答'), 20, bold=True)
    title.paragraph_format.space_after = Pt(16)
    with tempfile.TemporaryDirectory(prefix='ocean-report-') as directory:
        equation_dir = Path(directory)
        for index, path in enumerate([ROOT/'第一题_MH370海洋技术.md', ROOT/'第二题_海水声速分析.md']):
            if index:
                doc.add_page_break()
            add_markdown(doc, path.read_text(encoding='utf-8'), equation_dir)
        doc.add_page_break()
        doc.add_heading('附录：MATLAB 完整源代码', level=1)
        inline(doc.add_paragraph(), '以下代码与单独提供的 .m 文件内容一致。将两个文件放在同一 matlab 目录下，运行 analyze_sound_speed.m 即可生成图表与数据。')
        for filename in ['seawater_sound_speed.m', 'analyze_sound_speed.m']:
            doc.add_heading(filename, level=2)
            add_code(doc, (ROOT/'matlab'/filename).read_text(encoding='utf-8'))
        doc.save(OUTPUT)
    # Validate structure and ensure both complete source files survived conversion.
    loaded = Document(OUTPUT)
    text = '\n'.join(p.text for p in loaded.paragraphs)
    for filename in ['seawater_sound_speed.m', 'analyze_sound_speed.m']:
        for line in (ROOT/'matlab'/filename).read_text(encoding='utf-8').splitlines():
            assert not line or line in text, (filename, line)
    with zipfile.ZipFile(OUTPUT) as archive:
        media = [name for name in archive.namelist() if name.startswith('word/media/')]
        assert len(media) >= 9, media  # three diagrams and six equations
    print(f'Created {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)')
    print(f'Validated {len(media)} embedded images, 3 source diagrams, and both complete MATLAB files.')


if __name__ == '__main__':
    main()
