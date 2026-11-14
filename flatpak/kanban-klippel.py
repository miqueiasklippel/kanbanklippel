#!/usr/bin/env python3
import base64
import json
import os
import sys
import threading
import urllib.error
import urllib.request

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("WebKit", "6.0")
gi.require_version("JavaScriptCore", "6.0")
from gi.repository import Gio, GLib, Gtk, JavaScriptCore, WebKit

APP_ID = "io.github.miqueiasklippel.KanbanKlippel"
APP_NAME = "Kanban Klippel"
VERSION = "1.0.0"


def resource_dir():
    here = os.path.dirname(os.path.realpath(__file__))
    for candidate in (os.environ.get("KANBAN_KLIPPEL_DATA"), "/app/share/kanban-klippel", here):
        if candidate and os.path.isfile(os.path.join(candidate, "index.html")):
            return candidate
    sys.exit("index.html not found")


class Window(Gtk.ApplicationWindow):
    def __init__(self, app, base):
        super().__init__(application=app, title=APP_NAME)
        self.base = base
        self.quitting = False
        self.set_default_size(1320, 840)
        self.set_icon_name(APP_ID)

        data_dir = os.path.join(GLib.get_user_data_dir(), "kanban-klippel")
        cache_dir = os.path.join(GLib.get_user_cache_dir(), "kanban-klippel")
        session = WebKit.NetworkSession.new(data_dir, cache_dir)

        ucm = WebKit.UserContentManager()
        with open(os.path.join(base, "bridge.js"), encoding="utf-8") as fh:
            ucm.add_script(WebKit.UserScript.new(
                fh.read(),
                WebKit.UserContentInjectedFrames.TOP_FRAME,
                WebKit.UserScriptInjectionTime.START,
                None, None))
        ucm.register_script_message_handler_with_reply("kk", None)
        ucm.connect("script-message-with-reply-received::kk", self.on_message)

        self.view = WebKit.WebView(network_session=session, user_content_manager=ucm)
        settings = self.view.get_settings()
        settings.set_allow_file_access_from_file_urls(True)
        settings.set_allow_universal_access_from_file_urls(True)
        settings.set_javascript_can_access_clipboard(True)
        settings.set_enable_developer_extras(bool(os.environ.get("KANBAN_KLIPPEL_DEBUG")))
        settings.set_enable_back_forward_navigation_gestures(False)

        self.view.connect("decide-policy", self.on_decide_policy)
        self.view.connect("create", self.on_create)
        self.view.connect("notify::title", self.on_title)

        self.set_child(self.view)
        self.connect("close-request", self.on_close_request)

        index = Gio.File.new_for_path(os.path.join(base, "index.html"))
        self.view.load_uri(index.get_uri())

    def on_title(self, view, _pspec):
        self.set_title(view.get_title() or APP_NAME)

    def open_external(self, uri):
        Gtk.UriLauncher.new(uri).launch(self, None, None, None)

    def on_decide_policy(self, view, decision, kind):
        if kind == WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            uri = decision.get_navigation_action().get_request().get_uri()
            if uri.startswith(("file:", "about:", "data:", "blob:")):
                return False
            decision.ignore()
            self.open_external(uri)
            return True
        if kind == WebKit.PolicyDecisionType.NEW_WINDOW_ACTION:
            uri = decision.get_navigation_action().get_request().get_uri()
            decision.ignore()
            if uri and not uri.startswith(("file:", "about:", "blob:", "data:")):
                self.open_external(uri)
            return True
        return False

    def on_create(self, view, action):
        uri = action.get_request().get_uri()
        if uri and uri.startswith(("http:", "https:", "mailto:")):
            self.open_external(uri)
        return None

    def on_close_request(self, _win):
        if self.quitting:
            return False
        self.view.evaluate_javascript(
            "typeof pedirSaida === 'function' && window.__KK_OK__ ? (pedirSaida(), true) : false",
            -1, None, None, None, self.on_close_checked)
        return True

    def on_close_checked(self, view, result):
        try:
            handled = view.evaluate_javascript_finish(result).to_boolean()
        except GLib.Error:
            handled = False
        if not handled:
            self.quit()

    def quit(self):
        self.quitting = True
        self.close()

    def on_message(self, _ucm, value, reply):
        ctx = value.get_context()

        def respond(result=None, error=None):
            payload = {"error": error} if error else {"result": result}
            reply.return_value(JavaScriptCore.Value.new_string(ctx, json.dumps(payload)))
            return False

        try:
            msg = json.loads(value.to_string())
            cmd = msg.get("cmd")
            args = msg.get("args") or {}
            if cmd == "read":
                respond(self.read_file(args["path"]))
            elif cmd == "write":
                self.write_file(args["path"], args["contents"])
                respond(True)
            elif cmd == "open":
                self.pick(args, False, respond)
            elif cmd == "save":
                self.pick(args, True, respond)
            elif cmd == "http":
                threading.Thread(target=self.http, args=(args, respond), daemon=True).start()
            elif cmd == "quit":
                respond(True)
                GLib.idle_add(self.quit)
            else:
                respond(error="unknown command: %s" % cmd)
        except Exception as exc:
            respond(error=str(exc))
        return True

    @staticmethod
    def read_file(path):
        ok, data, _etag = Gio.File.new_for_path(path).load_contents(None)
        return data.decode("utf-8")

    @staticmethod
    def write_file(path, contents):
        Gio.File.new_for_path(path).replace_contents(
            contents.encode("utf-8"), None, False, Gio.FileCreateFlags.NONE, None)

    def pick(self, opts, save, respond):
        dialog = Gtk.FileDialog(modal=True)
        filters = Gio.ListStore.new(Gtk.FileFilter)
        for spec in opts.get("filters") or []:
            ff = Gtk.FileFilter(name=spec.get("name") or "")
            for ext in spec.get("extensions") or []:
                ff.add_suffix(ext)
            filters.append(ff)
        if filters.get_n_items():
            any_filter = Gtk.FileFilter(name="Todos os arquivos")
            any_filter.add_pattern("*")
            filters.append(any_filter)
            dialog.set_filters(filters)
            dialog.set_default_filter(filters.get_item(0))

        def done(dlg, result):
            try:
                f = dlg.save_finish(result) if save else dlg.open_finish(result)
                respond(f.get_path() if f else None)
            except GLib.Error as exc:
                if exc.matches(Gtk.DialogError.quark(), Gtk.DialogError.DISMISSED) or \
                   exc.matches(Gtk.DialogError.quark(), Gtk.DialogError.CANCELLED):
                    respond(None)
                else:
                    respond(error=exc.message)

        if save:
            dialog.set_title("Salvar cofre")
            default = opts.get("defaultPath")
            if default:
                dialog.set_initial_name(os.path.basename(default))
            dialog.save(self, None, done)
        else:
            dialog.set_title("Abrir cofre")
            dialog.open(self, None, done)

    @staticmethod
    def http(args, respond):
        body = base64.b64decode(args["body"]) if args.get("body") else None
        req = urllib.request.Request(
            args["url"], data=body, method=args.get("method") or "GET",
            headers={"User-Agent": "%s/%s" % (APP_NAME.replace(" ", ""), VERSION), **(args.get("headers") or {})})
        try:
            try:
                resp = urllib.request.urlopen(req, timeout=60)
            except urllib.error.HTTPError as err:
                resp = err
            with resp:
                result = {
                    "status": resp.status if hasattr(resp, "status") else resp.code,
                    "reason": resp.reason or "",
                    "headers": dict(resp.headers.items()),
                    "body": base64.b64encode(resp.read()).decode("ascii"),
                }
            GLib.idle_add(respond, result)
        except Exception as exc:
            GLib.idle_add(lambda: respond(error=str(getattr(exc, "reason", exc))))


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        GLib.set_application_name(APP_NAME)
        self.base = resource_dir()

    def do_activate(self):
        win = self.get_active_window() or Window(self, self.base)
        win.present()


if __name__ == "__main__":
    sys.exit(App().run(sys.argv))
