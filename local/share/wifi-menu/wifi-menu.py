#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wifi-menu — 用 GTK4 + libnm 重做的 waybar 网络菜单（Catppuccin Mocha）。

只依赖 libnm(GI) / NetworkManager，不把密码放进命令行参数。
"""
import os

# 这个菜单只要 2D 绘制：cairo 渲染器把常驻内存从 ~300MB 压到 ~90MB
os.environ.setdefault("GSK_RENDERER", "cairo")

import signal
import sys
import time

_T0 = time.perf_counter()
_DEBUG = bool(os.environ.get("WIFI_MENU_DEBUG"))


def dbg(msg):
    if _DEBUG:
        print(f"[{1000*(time.perf_counter()-_T0):6.0f}ms] {msg}", file=sys.stderr, flush=True)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("NM", "1.0")
from gi.repository import Gtk, Gdk, GLib, NM  # noqa: E402

_AP_FLAGS = getattr(NM, "80211ApFlags")
_AP_SEC = getattr(NM, "80211ApSecurityFlags")
_SEC_SETTING = getattr(NM, "SETTING_WIRELESS_SECURITY_SETTING_NAME")

APP_ID = "dev.xxhjppx.wifimenu"
CSS = """
@define-color base      #1e1e2e;
@define-color mantle    #181825;
@define-color crust     #11111b;
@define-color surface0  #313244;
@define-color surface1  #303242;
@define-color surface2  #585b70;
@define-color overlay0  #6c7086;
@define-color overlay1  #7f849c;
@define-color text      #cdd6f4;
@define-color mauve     #cba6f7;
@define-color green     #a6e3a1;
@define-color red       #f38ba8;
@define-color peach     #fab387;
@define-color yellow    #f9e2af;

window.panel-window { background-color: transparent; background-image: none; }
.panel {
  background-color: alpha(mix(@base, @mauve, 0.06), 0.985);
  border-radius: 10px;
  box-shadow: inset 0 0 0 1px alpha(@mauve, 0.22),
              inset 0 1px 0 alpha(#ffffff, 0.08);
}
.header-title { font-size: 19px; font-weight: 800; color: @text; }
.header-sub   { font-size: 11px; color: @overlay1; }
.section { font-size: 10px; font-weight: 700; color: @overlay0; letter-spacing: 1.1px; }
.card { background-color: alpha(@mantle, 0.72); border-radius: 10px;
        border: 1px solid alpha(@surface1, 0.9); }
.row { padding: 7px 14px; border-radius: 10px; }
.row:hover { background-color: alpha(@surface0, 0.75); }
.row-on { background-color: alpha(@green, 0.06); }
.ssid { font-size: 14px; color: @text; }
.meta { font-size: 10px; color: @overlay0; }
.pct  { font-size: 11px; color: @overlay1; }
.chip { font-size: 10px; color: @green; background-color: alpha(@green, 0.12);
        border-radius: 999px; padding: 2px 8px; }
.chip-saved { color: @mauve; background-color: alpha(@mauve, 0.12); }
.lock { color: @overlay1; }
button.flat { background: transparent; border: none; box-shadow: none; border-radius: 8px;
              color: @subtext0; padding: 5px 9px; }
button.flat:hover { background-color: alpha(@surface0, 0.9); color: @text; }
button.ghost { background-color: @surface0; border: none; border-radius: 9px;
               color: @text; padding: 6px 12px; font-size: 12px; }
button.ghost:hover { background-color: @surface2; }
switch { background-color: @surface0; border-radius: 999px; }
switch:checked { background-color: alpha(@mauve, 0.85); }
switch slider { background-color: @text; border-radius: 999px; }
entry { background-color: @surface0; border-radius: 9px; padding: 7px 10px; color: @text; }
.icon { font-family: "JetBrainsMono Nerd Font"; font-size: 16px; color: @overlay1; }
.icon-on { color: @green; }
.lock { font-family: "JetBrainsMono Nerd Font"; font-size: 12px; }
scrollbar slider { background-color: alpha(@surface2, 0.75); border-radius: 999px;
                   min-width: 4px; min-height: 36px; }
scrollbar trough { background: transparent; }
.status { font-size: 11px; color: @overlay0; }
.status-ok { color: @green; } .status-err { color: @red; }
.spinner { color: @mauve; }
"""


def sstr(ssid_bytes) -> str:
    try:
        return bytes(ssid_bytes.get_data()).decode("utf-8", "replace")
    except Exception:
        return ""


def strength_icon(s: int) -> str:
    if s >= 81:
        return "󰤨"
    if s >= 61:
        return "󰤥"
    if s >= 41:
        return "󰤢"
    if s >= 21:
        return "󰤟"
    return "󰤯"


class WifiMenu:
    def __init__(self, app: Gtk.Application, serve: bool = False):
        self.app = app
        self.serve = serve
        self.client = None
        self.dev = None
        self.win = Gtk.ApplicationWindow(application=app)
        self.win.add_css_class("panel-window")
        self.win.set_decorated(False)
        self.win.set_default_size(520, 660)
        self.win.set_title("网络")

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.add_css_class("panel")
        self.win.set_child(root)
        root.append(self._header())

        self.switch = Gtk.Switch()
        self.switch.set_valign(Gtk.Align.CENTER)
        self.switch.set_sensitive(False)
        self.switch.connect("notify::active", self._on_wifi_toggle)
        root.append(self._switch_row(self.switch))

        root.append(self._label("可用网络", "section"))

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.add_css_class("card")
        self.listbox.connect("row-activated", self._on_row)
        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_child(self.listbox)
        wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        wrap.set_margin_start(16)
        wrap.set_margin_end(16)
        wrap.append(scroller)
        root.append(wrap)

        root.append(self._footer())

        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self._on_key)
        self.win.add_controller(key)

        self.win.connect("close-request", self._on_close_request)

        # 对话框登记（关主窗时一起收掉）
        self._open_dialogs = []

    def _on_close_request(self, *_):
        if self.serve:
            self.win.set_visible(False)
            return True          # 常驻模式：关窗=藏起来
        self.app.quit()
        return False

    def toggle(self):
        if self.win.get_visible():
            self.win.set_visible(False)
            return
        if self.client is None:
            self.prime()
        else:
            self.reload()
        self.win.present()

    # ---------- nm helpers ----------
    def _wifi_device(self):
        for d in self.client.get_devices():
            if d.get_device_type() == NM.DeviceType.WIFI:
                return d
        return None

    def _wifi_enabled(self) -> bool:
        try:
            return bool(self.client.wireless_get_enabled())
        except Exception:
            return True

    def _ipv4(self) -> str:
        try:
            cfg = self.dev.get_ip4_config() if self.dev else None
            addrs = cfg.get_addresses() if cfg else []
            return addrs[0].get_address() if addrs else ""
        except Exception:
            return ""

    def _active_ssid(self) -> str:
        if self.dev is None:
            return ""
        ap = self.dev.get_active_access_point()
        return sstr(ap.get_ssid()) if ap else ""

    def _saved_ssids(self) -> set:
        out = set()
        for c in self.client.get_connections():
            if c.get_connection_type() != "802-11-wireless":
                continue
            s = c.get_setting_wireless()
            if s is not None:
                name = sstr(s.get_ssid())
                if name:
                    out.add(name)
        return out

    def _networks(self):
        """[(ssid, strength, secure, connected)] 按信号降序去重"""
        best = {}
        if self.dev is None:
            return []
        active = self._active_ssid()
        for ap in self.dev.get_access_points():
            ssid = sstr(ap.get_ssid())
            if not ssid:
                continue
            strength = ap.get_strength()
            secure = bool(ap.get_flags() & _AP_FLAGS.PRIVACY) or \
                ap.get_wpa_flags() != _AP_SEC.NONE or \
                ap.get_rsn_flags() != _AP_SEC.NONE
            old = best.get(ssid)
            if old is None or strength > old[1]:
                best[ssid] = (ssid, strength, secure, ssid == active)
            elif ssid == active:
                best[ssid] = (ssid, old[1], old[2], True)
        return sorted(best.values(), key=lambda n: (not n[3], -n[1]))

    # ---------- ui ----------
    def _header(self):
        handle = Gtk.WindowHandle()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(16)
        box.set_margin_start(18)
        box.set_margin_end(14)
        box.set_margin_bottom(4)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        t = Gtk.Label(label="网络", xalign=0)
        t.add_css_class("header-title")
        self.sub = Gtk.Label(label="", xalign=0)
        self.sub.add_css_class("header-sub")
        titles.append(t)
        titles.append(self.sub)
        top.append(titles)
        top.append(Gtk.Box(hexpand=True))

        refresh = Gtk.Button(label="󰑐")
        refresh.add_css_class("flat")
        refresh.add_css_class("icon")
        refresh.set_tooltip_text("重新扫描")
        refresh.set_can_focus(False)   # 不让它抢键盘焦点（避免开窗就出现焦点框）
        refresh.connect("clicked", lambda *_: self.rescan())
        top.append(refresh)
        box.append(top)
        handle.set_child(box)
        return handle

    def _label(self, text, cls):
        lbl = Gtk.Label(label=text, xalign=0)
        lbl.add_css_class(cls)
        lbl.set_margin_start(20)
        lbl.set_margin_top(10)
        lbl.set_margin_bottom(4)
        return lbl

    def _switch_row(self, sw):
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        card.add_css_class("card")
        card.set_margin_start(16)
        card.set_margin_end(16)
        card.set_margin_top(4)
        card.set_margin_bottom(2)
        inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        inner.set_margin_top(8)
        inner.set_margin_bottom(8)
        inner.set_margin_start(14)
        inner.set_margin_end(14)
        lab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        t = Gtk.Label(label="Wi-Fi", xalign=0)
        t.add_css_class("ssid")
        self.radio_sub = Gtk.Label(label="", xalign=0)
        self.radio_sub.add_css_class("meta")
        lab.append(t)
        lab.append(self.radio_sub)
        inner.append(lab)
        inner.append(Gtk.Box(hexpand=True))
        inner.append(sw)
        card.append(inner)
        return card

    def _footer(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(8)
        box.set_margin_bottom(14)
        self.status = Gtk.Label(label="", xalign=0)
        self.status.add_css_class("status")
        self.status.set_ellipsize(3)
        box.append(self.status)
        box.append(Gtk.Box(hexpand=True))

        hidden = Gtk.Button(label="隐藏网络")
        hidden.add_css_class("ghost")
        hidden.connect("clicked", lambda *_: self._hidden_dialog())
        saved = Gtk.Button(label="已保存")
        saved.add_css_class("ghost")
        saved.connect("clicked", lambda *_: self._saved_dialog())
        settings = Gtk.Button(label="设置")
        settings.add_css_class("ghost")
        settings.connect("clicked", lambda *_: self._open_settings())
        for b in (hidden, saved, settings):
            box.append(b)
        return box

    def _row_widget(self, ssid, strength, secure, connected, saved):
        row = Gtk.ListBoxRow()
        row.ssid = ssid
        row.secure = secure
        row.connected = connected
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.add_css_class("row")
        if connected:
            box.add_css_class("row-on")
        icon = Gtk.Label(label=strength_icon(strength))
        icon.set_size_request(22, -1)
        icon.add_css_class("icon")
        if connected:
            icon.add_css_class("icon-on")
        texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        texts.set_hexpand(True)
        name = Gtk.Label(label=ssid, xalign=0)
        name.add_css_class("ssid")
        if connected:
            ip = self._ipv4()
            meta_text = f"当前网络 · {ip}" if ip else "当前网络"
        else:
            meta_text = "已保存" if saved else ("需要密码" if secure else "开放网络")
        meta = Gtk.Label(label=meta_text, xalign=0)
        meta.add_css_class("meta")
        texts.append(name)
        texts.append(meta)
        box.append(icon)
        box.append(texts)
        if secure:
            lock = Gtk.Label(label="󰌾")
            lock.add_css_class("lock")
            box.append(lock)
        pct = Gtk.Label(label=f"{strength}%")
        pct.add_css_class("pct")
        box.append(pct)
        if connected:
            chip = Gtk.Label(label="已连接")
            chip.add_css_class("chip")
            box.append(chip)
        elif saved:
            chip = Gtk.Label(label="已保存")
            chip.add_css_class("chip")
            chip.add_css_class("chip-saved")
            box.append(chip)
        row.set_child(box)
        return row

    def prime(self):
        """窗口已经画出来之后再连 NM、扫网络"""
        dbg("prime start")
        self.client = NM.Client.new(None)
        self.dev = self._wifi_device()
        self.switch.set_sensitive(True)
        self.switch.set_active(self._wifi_enabled())
        self.reload()
        GLib.timeout_add_seconds(8, self._tick)
        dbg("prime done")
        return False

    def reload(self):
        if self.client is None:
            self._status("正在连接 NetworkManager…")
            return
        while (child := self.listbox.get_first_child()) is not None:
            self.listbox.remove(child)
        enabled = self._wifi_enabled()
        self.switch.set_active(enabled)
        active = self._active_ssid()
        self.sub.set_label(f"已连接 {active}" if active else ("Wi-Fi 已关闭" if not enabled else "未连接"))
        self.radio_sub.set_label("已开启" if enabled else "已关闭")
        if not enabled:
            self._status("Wi-Fi 已关闭")
            return
        saved = self._saved_ssids()
        nets = self._networks()
        if not nets:
            self._status("没有扫描到网络，点右上角刷新")
            return
        for ssid, strength, secure, connected in nets:
            self.listbox.append(self._row_widget(ssid, strength, secure, connected, ssid in saved))
        self._status(f"{len(nets)} 个网络")

    # ---------- actions ----------
    def _status(self, text, err=False):
        self.status.set_label(text)
        for c in ("status-ok", "status-err"):
            self.status.remove_css_class(c)
        self.status.add_css_class("status-err" if err else "status-ok")

    def _on_key(self, _c, keyval, _code, _state):
        if keyval == Gdk.KEY_Escape:
            self.win.close()
            return True
        return False

    def _on_wifi_toggle(self, sw, _pspec):
        want = sw.get_active()
        if want == self._wifi_enabled():
            return
        self.client.wireless_set_enabled(want)
        GLib.timeout_add(700, self._after_radio, want)

    def _after_radio(self, want):
        self.reload()
        self._status("Wi-Fi 已开启" if want else "Wi-Fi 已关闭")
        return False

    def rescan(self):
        if self.dev is None:
            return
        self._status("正在扫描…")
        self.dev.request_scan_async(None, self._scan_done)

    def _scan_done(self, dev, res):
        try:
            dev.request_scan_finish(res)
        except Exception:
            pass
        GLib.timeout_add(400, self._after_scan)

    def _after_scan(self):
        self.reload()
        return False

    def _tick(self):
        if not self.win.get_visible():
            return False
        self.reload()
        return True

    def _on_row(self, _lb, row):
        ssid = row.ssid
        if row.connected:
            self._details_dialog(ssid)
            return
        if ssid in self._saved_ssids():
            self._activate_saved(ssid)
        elif not row.secure:
            self._connect_new(ssid, None)
        else:
            self._password_dialog(ssid)

    # --- 连接 ---
    def _activate_saved(self, ssid):
        for c in self.client.get_connections():
            if c.get_connection_type() != "802-11-wireless":
                continue
            ws = c.get_setting_wireless()
            if ws is not None and sstr(ws.get_ssid()) == ssid:
                self._status(f"正在连接 {ssid}…")
                self.client.activate_connection_async(c, self.dev, None, None, self._activated, ssid)
                return
        self._status("找不到已保存的配置", err=True)

    def _activated(self, client, res, ssid):
        try:
            client.activate_connection_finish(res)
            self._status(f"已连接 {ssid}")
        except Exception as exc:
            self._status(f"连接失败：{str(exc)[:60]}", err=True)
        GLib.timeout_add(1200, self._after_scan)

    def _build_conn(self, ssid, password):
        conn = NM.SimpleConnection.new()
        sc = NM.SettingConnection.new()
        sc.set_property(NM.SETTING_CONNECTION_ID, ssid)
        sc.set_property(NM.SETTING_CONNECTION_TYPE, "802-11-wireless")
        sc.set_property(NM.SETTING_CONNECTION_AUTOCONNECT, True)
        sw = NM.SettingWireless.new()
        sw.set_property(NM.SETTING_WIRELESS_SSID, GLib.Bytes.new(ssid.encode()))
        sw.set_property(NM.SETTING_WIRELESS_MODE, "infrastructure")
        conn.add_setting(sc)
        conn.add_setting(sw)
        if password:
            sec = NM.SettingWirelessSecurity.new()
            sec.set_property(NM.SETTING_WIRELESS_SECURITY_KEY_MGMT, "wpa-psk")
            sec.set_property(NM.SETTING_WIRELESS_SECURITY_PSK, password)
            conn.add_setting(sec)
            sw.add_security(_SEC_SETTING)
        return conn

    def _find_ap(self, ssid):
        if self.dev is None:
            return None
        for ap in self.dev.get_access_points():
            if sstr(ap.get_ssid()) == ssid:
                return ap
        return None

    def _connect_new(self, ssid, password, hidden=False):
        self._status(f"正在连接 {ssid}…")
        conn = self._build_conn(ssid, password)
        if hidden:
            sw = conn.get_setting_wireless()
            sw.set_property(NM.SETTING_WIRELESS_HIDDEN, True)
            self.client.add_and_activate_connection_async(conn, self.dev, None, None,
                                                          self._activated, ssid)
            return
        ap = self._find_ap(ssid)
        path = ap.get_path() if ap is not None else None
        self.client.add_and_activate_connection_async(conn, self.dev, path, None,
                                                      self._activated, ssid)

    # --- 对话框 ---
    def _dialog(self, title, body_widget, ok_label):
        win = Gtk.Window(transient_for=self.win, modal=True)
        win.add_css_class("panel-window")
        win.set_decorated(False)
        win.set_title(title)
        win.set_default_size(400, -1)
        win.set_resizable(False)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.add_css_class("panel")
        box.set_margin_top(18)
        box.set_margin_bottom(16)
        box.set_margin_start(20)
        box.set_margin_end(20)
        t = Gtk.Label(label=title, xalign=0)
        t.add_css_class("header-title")
        box.append(t)
        box.append(body_widget)
        btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btns.set_halign(Gtk.Align.END)
        cancel = Gtk.Button(label="取消")
        cancel.add_css_class("ghost")
        cancel.connect("clicked", lambda *_: win.close())
        ok = Gtk.Button(label=ok_label)
        ok.add_css_class("ghost")
        btns.append(cancel)
        btns.append(ok)
        box.append(btns)
        win.set_child(box)
        self._open_dialogs.append(win)
        win.connect("destroy", lambda w: self._open_dialogs.remove(w)
                    if w in self._open_dialogs else None)
        key = Gtk.EventControllerKey()
        key.connect("key-pressed", lambda _c, kv, _k, _s:
                    (win.close(), True)[1] if kv == Gdk.KEY_Escape else False)
        win.add_controller(key)
        win.present()
        return win, ok

    def _password_dialog(self, ssid):
        entry = Gtk.PasswordEntry()
        entry.set_show_peek_icon(True)
        entry.set_property("placeholder-text", "密码")
        win, ok = self._dialog(f"连接到 {ssid}", entry, "连接")

        def go(*_):
            pw = entry.get_text()
            if not pw:
                return
            win.close()
            self._connect_new(ssid, pw)

        ok.connect("clicked", go)
        keyc = Gtk.EventControllerKey()
        keyc.connect("key-pressed", lambda _c, kv, _k, _s: (go(), True)[1]
                     if kv in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) else False)
        entry.add_controller(keyc)
        entry.grab_focus()

    def _hidden_dialog(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        name = Gtk.Entry()
        name.set_placeholder_text("网络名称 (SSID)")
        pw = Gtk.PasswordEntry()
        pw.set_show_peek_icon(True)
        pw.set_property("placeholder-text", "密码（开放网络留空）")
        box.append(name)
        box.append(pw)
        win, ok = self._dialog("连接隐藏网络", box, "连接")

        def go(*_):
            ssid = name.get_text().strip()
            if not ssid:
                return
            win.close()
            self._connect_new(ssid, pw.get_text() or None, hidden=True)

        ok.connect("clicked", go)
        name.grab_focus()

    def _saved_dialog(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        lb = Gtk.ListBox()
        lb.set_selection_mode(Gtk.SelectionMode.NONE)
        lb.add_css_class("card")
        for c in self.client.get_connections():
            if c.get_connection_type() != "802-11-wireless":
                continue
            ws = c.get_setting_wireless()
            ssid = sstr(ws.get_ssid()) if ws is not None else c.get_id()
            row = Gtk.ListBoxRow()
            lab = Gtk.Label(label=ssid, xalign=0)
            lab.add_css_class("row")
            row.set_child(lab)
            lb.append(row)
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_min_content_height(220)
        scroller.set_child(lb)
        box.append(scroller)
        win, _ok = self._dialog("已保存的网络", box, "关闭")

        def activate(_lb, row):
            ssid = row.get_child().get_label()
            win.close()
            self._activate_saved(ssid)

        lb.connect("row-activated", activate)

    def _details_dialog(self, ssid):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        ip = "—"
        gw = "—"
        if self.dev is not None:
            cfg = self.dev.get_ip4_config()
            if cfg is not None:
                addrs = cfg.get_addresses()
                if addrs:
                    ip = f"{addrs[0].get_address()}/{addrs[0].get_prefix()}"
                gw = cfg.get_gateway() or "—"
        for k, v in (("网络", ssid), ("IP", ip), ("网关", gw),
                     ("接口", self.dev.get_iface() if self.dev else "—")):
            line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            a = Gtk.Label(label=k, xalign=0)
            a.add_css_class("meta")
            a.set_size_request(60, -1)
            b = Gtk.Label(label=v, xalign=0)
            b.add_css_class("ssid")
            line.append(a)
            line.append(b)
            box.append(line)
        win, ok = self._dialog(f"{ssid}", box, "断开")
        ok.connect("clicked", lambda *_: (win.close(), self._disconnect()))

    def _disconnect(self):
        if self.dev is None:
            return
        self._status("正在断开…")
        self.dev.disconnect_async(None, self._disconnected)

    def _disconnected(self, dev, res):
        try:
            dev.disconnect_finish(res)
            self._status("已断开")
        except Exception as exc:
            self._status(f"断开失败：{str(exc)[:50]}", err=True)
        GLib.timeout_add(800, self._after_scan)

    def _demo(self, kind):
        if kind == "password":
            self._password_dialog("CMCC-bh3m")
        elif kind == "hidden":
            self._hidden_dialog()
        elif kind == "saved":
            self._saved_dialog()
        elif kind == "details":
            self._details_dialog(self._active_ssid())

    def _open_settings(self):
        GLib.spawn_async(["/usr/bin/nm-connection-editor"], flags=GLib.SpawnFlags.SEARCH_PATH)
        self.win.close()


LOCK = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "wifi-menu.pid")


def main():
    dbg("main start")
    GLib.set_prgname("wifi-menu")
    app = Gtk.Application(application_id=APP_ID)
    menu = None
    demo = None
    serve = "--serve" in sys.argv
    show = "--show" in sys.argv
    argv = [a for a in sys.argv if a not in ("--serve", "--show")]
    if "--demo" in argv:
        i = argv.index("--demo")
        demo = argv[i + 1] if i + 1 < len(argv) else ""
        del argv[i:i + 2]

    def activate(a):
        nonlocal menu
        dbg("activate")
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode())
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        if menu is None:
            menu = WifiMenu(a, serve=serve)
            if serve and not show:
                dbg("serve: warm, hidden")
                return
        elif menu.win.get_visible() and not demo:
            menu.win.set_visible(False)
            return
        menu.win.present()
        dbg("presented")
        GLib.idle_add(menu.prime)
        if demo:
            GLib.timeout_add(600, lambda: (menu._demo(demo), False)[1])

    app.connect("activate", activate)

    def _bye(*_):
        app.quit()
        return False

    GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGUSR1,
                         lambda: (menu and menu.toggle(), True)[1])

    for sig in (signal.SIGTERM, signal.SIGINT):
        GLib.unix_signal_add(GLib.PRIORITY_HIGH, sig, _bye)
    try:
        with open(LOCK, "w") as fh:
            fh.write(str(os.getpid()))
    except OSError:
        pass
    try:
        return app.run([argv[0]] if argv else [])
    finally:
        try:
            os.unlink(LOCK)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
