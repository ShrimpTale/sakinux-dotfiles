#!/usr/bin/env python3
"""waybar 时钟模块（JSON 输出模式）：
- 默认显示时间，点击切换日期显示（config on-click + signal 刷新）
- 两种视图悬停 tooltip 都是日历（waybar 原版样式，星期/数字已对齐）
"""
import calendar as cal
import json
import locale
from datetime import date, datetime
from pathlib import Path

locale.setlocale(locale.LC_TIME, "")  # 继承系统中文 locale

STATE = Path.home() / ".cache/waybar-clock-mode"


def waybar_style_calendar(today: date) -> str:
    """复刻 waybar clock 模块 {calendar} 的渲染（Monday 起始、3 字符列宽、中文对齐）"""
    y, m = today.year, today.month

    # 标题（waybar: {:L%B %Y}）→ "八月 2026"
    title = today.strftime("%B %Y")

    # 星期表头：中文全角字 1 字 = 数字格 2 半角宽。
    # 数字是右对齐两位（" 3"，字在列内偏右），星期字加前导空格让左边缘对齐
    day_abbr = list(cal.day_abbr)  # zh locale: 一~日，索引 0=周一
    header = " " + " ".join(day_abbr)

    # 日期行（%e 两位右对齐，今天用自定义格式）
    rows = []
    for week in cal.Calendar(firstweekday=0).monthdayscalendar(y, m):
        cells = []
        for d in week:
            if d == 0:
                cells.append("  ")
            elif d == today.day:
                cells.append(f"<span color='#cba6f7'><b>{d}</b></span>")
            else:
                cells.append(f"{d:>2}")
        rows.append(" ".join(cells))

    # 组装 tooltip-format 结构：<big>{:%Y %B}</big>\n<span font='...'>{calendar}</span>
    big_title = today.strftime("%Y %B")  # "2026 八月"
    body = "\n".join([title, header] + rows)
    return (
        f"<big>{big_title}</big>\n"
        f"<span font='Noto Sans Mono CJK SC 12'>{body}</span>"
    )


now = datetime.now()
mode = "date" if STATE.exists() and STATE.read_text().strip() == "date" else "time"
text = now.strftime("%Y-%m-%d") if mode == "date" else now.strftime("%H:%M ")
tooltip = waybar_style_calendar(now.date())
print(json.dumps({"text": text, "tooltip": tooltip}))
