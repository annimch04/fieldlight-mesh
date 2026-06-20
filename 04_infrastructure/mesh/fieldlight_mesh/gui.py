"""Peer-facing macOS desktop application for Fieldlight Mesh."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Callable

from .client import send_sil_message
from .inbox import list_messages
from .peer_registry import load_registry, merge_registry, resolve_sil_address
from .routing import load_route_schema
from .server import SILMeshServer, load_trusted_peers
from .state import default_home, default_node_id, initialize, load_config, load_yaml, paths, write_yaml


class MeshApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Fieldlight Mesh")
        self.geometry("820x620")
        self.minsize(720, 520)
        self.home = default_home()
        self.server: SILMeshServer | None = None
        self.server_thread: threading.Thread | None = None
        self.zeroconf: Any | None = None
        self.service_info: Any | None = None
        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._configure_style()
        self.after(100, self._drain_events)
        if paths(self.home)["config"].exists():
            self._build_main()
        else:
            self._build_welcome()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        if "aqua" in style.theme_names():
            style.theme_use("aqua")
        style.configure("Title.TLabel", font=("Helvetica Neue", 24, "bold"))
        style.configure("Heading.TLabel", font=("Helvetica Neue", 15, "bold"))
        style.configure("Status.TLabel", font=("Helvetica Neue", 12))

    def _clear(self) -> None:
        for child in self.winfo_children():
            child.destroy()

    def _build_welcome(self) -> None:
        self._clear()
        frame = ttk.Frame(self, padding=36)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Fieldlight Mesh", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            frame,
            text="Create a local identity, connect a trusted peer, and exchange messages.",
        ).pack(anchor="w", pady=(8, 24))
        warning = ttk.LabelFrame(frame, text="Alpha security boundary", padding=14)
        warning.pack(fill="x", pady=(0, 24))
        ttk.Label(
            warning,
            text="Messages use plaintext TCP. Use harmless content on a trusted LAN or encrypted overlay.",
            wraplength=680,
        ).pack(anchor="w")
        form = ttk.Frame(frame)
        form.pack(fill="x")
        ttk.Label(form, text="Node name").grid(row=0, column=0, sticky="w", pady=6)
        self.setup_name = tk.StringVar(value="peer")
        ttk.Entry(form, textvariable=self.setup_name, width=36).grid(row=0, column=1, sticky="ew", padx=12)
        ttk.Label(form, text="Mesh identity").grid(row=1, column=0, sticky="w", pady=6)
        self.setup_id = tk.StringVar(value=default_node_id())
        ttk.Entry(form, textvariable=self.setup_id, width=50).grid(row=1, column=1, sticky="ew", padx=12)
        form.columnconfigure(1, weight=1)
        ttk.Button(frame, text="Create Node", command=self._finish_setup).pack(anchor="e", pady=28)

    def _finish_setup(self) -> None:
        name = self.setup_name.get().strip()
        node_id = self.setup_id.get().strip()
        if not name or not node_id.startswith("mesh://"):
            messagebox.showerror("Invalid identity", "Enter a name and a mesh:// identity.")
            return
        try:
            initialize(self.home, node_id=node_id, node_name=name, port=7750)
        except Exception as exc:
            messagebox.showerror("Setup failed", str(exc))
            return
        self._build_main()

    def _build_main(self) -> None:
        self._clear()
        cfg = load_config(self.home)
        top = ttk.Frame(self, padding=(22, 16))
        top.pack(fill="x")
        ttk.Label(top, text="Fieldlight Mesh", style="Title.TLabel").pack(side="left")
        ttk.Label(top, text=str(cfg["node_id"])).pack(side="right")
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        self.home_tab = ttk.Frame(self.notebook, padding=20)
        self.messages_tab = ttk.Frame(self.notebook, padding=20)
        self.peers_tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(self.home_tab, text="Node")
        self.notebook.add(self.messages_tab, text="Messages")
        self.notebook.add(self.peers_tab, text="Peers")
        self._build_node_tab(cfg)
        self._build_messages_tab()
        self._build_peers_tab()

    def _build_node_tab(self, cfg: dict[str, Any]) -> None:
        ttk.Label(self.home_tab, text="Local Node", style="Heading.TLabel").pack(anchor="w")
        self.node_status = tk.StringVar(value="Stopped")
        ttk.Label(self.home_tab, textvariable=self.node_status, style="Status.TLabel").pack(anchor="w", pady=(8, 20))
        controls = ttk.Frame(self.home_tab)
        controls.pack(anchor="w")
        self.start_button = ttk.Button(controls, text="Start Node", command=self._start_node)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(controls, text="Stop", command=self._stop_node, state="disabled")
        self.stop_button.pack(side="left", padx=10)
        self.advertise = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, text="Advertise on local network", variable=self.advertise).pack(side="left", padx=14)
        details = ttk.LabelFrame(self.home_tab, text="Connection", padding=14)
        details.pack(fill="x", pady=28)
        ttk.Label(details, text=f"Listen port: {cfg.get('port', 7750)}").pack(anchor="w")
        ttk.Label(details, text=f"State: {self.home}", wraplength=700).pack(anchor="w", pady=4)
        ttk.Label(
            details,
            text="Public internet exposure is disabled by design. Use a trusted LAN or an encrypted overlay.",
            wraplength=700,
        ).pack(anchor="w", pady=4)

    def _server_config(self, cfg: dict[str, Any]) -> dict[str, Any]:
        p = paths(self.home)
        return {
            "routes": load_route_schema(p["routes"]),
            "node_id": cfg["node_id"],
            "node_short": str(cfg.get("node_name", "node")).upper(),
            "trusted_peers": load_trusted_peers(p["trusted"]),
            "routing_log_path": p["routing_log"],
            "audit_log_path": p["audit_log"],
            "inbox_path": p["inbox"],
            "log_writes": True,
            "socket_timeout": 10.0,
        }

    def _start_node(self) -> None:
        if self.server:
            return
        cfg = load_config(self.home)
        try:
            self.server = SILMeshServer((str(cfg.get("host", "0.0.0.0")), int(cfg.get("port", 7750))), self._server_config(cfg))
            if self.advertise.get():
                from zeroconf import Zeroconf
                from .lan_mdns import build_fieldlight_service

                self.service_info = build_fieldlight_service(
                    instance=f"fieldlight-{cfg.get('node_name', 'node')}",
                    port=int(cfg.get("port", 7750)),
                    mesh_uri=str(cfg["node_id"]),
                )
                self.zeroconf = Zeroconf()
                self.zeroconf.register_service(self.service_info)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
        except Exception as exc:
            if self.server:
                self.server.server_close()
                self.server = None
            messagebox.showerror("Node failed to start", str(exc))
            return
        self.node_status.set(f"Running as {cfg['node_id']}")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

    def _stop_node(self) -> None:
        server = self.server
        if not server:
            return
        self.node_status.set("Stopping...")

        def stop() -> None:
            server.shutdown()
            server.server_close()
            if self.zeroconf and self.service_info:
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
            self.events.put(("stopped", None))

        threading.Thread(target=stop, daemon=True).start()

    def _build_messages_tab(self) -> None:
        compose = ttk.LabelFrame(self.messages_tab, text="New Message", padding=14)
        compose.pack(fill="x")
        ttk.Label(compose, text="To").grid(row=0, column=0, sticky="w")
        self.message_to = tk.StringVar()
        self.message_to_box = ttk.Combobox(compose, textvariable=self.message_to)
        self.message_to_box.grid(row=0, column=1, sticky="ew", padx=10)
        ttk.Label(compose, text="Message").grid(row=1, column=0, sticky="nw", pady=10)
        self.message_body = tk.Text(compose, height=5, wrap="word")
        self.message_body.grid(row=1, column=1, sticky="ew", padx=10, pady=10)
        self.send_button = ttk.Button(compose, text="Send", command=self._send_message)
        self.send_button.grid(row=2, column=1, sticky="e", padx=10)
        compose.columnconfigure(1, weight=1)
        self.send_status = tk.StringVar()
        ttk.Label(compose, textvariable=self.send_status).grid(row=3, column=1, sticky="w", padx=10, pady=6)
        inbox_header = ttk.Frame(self.messages_tab)
        inbox_header.pack(fill="x", pady=(22, 6))
        ttk.Label(inbox_header, text="Inbox", style="Heading.TLabel").pack(side="left")
        ttk.Button(inbox_header, text="Refresh", command=self._refresh_inbox).pack(side="right")
        self.inbox_tree = ttk.Treeview(self.messages_tab, columns=("time", "from", "message"), show="headings", height=10)
        self.inbox_tree.heading("time", text="Received")
        self.inbox_tree.heading("from", text="From")
        self.inbox_tree.heading("message", text="Message")
        self.inbox_tree.column("time", width=150)
        self.inbox_tree.column("from", width=220)
        self.inbox_tree.column("message", width=360)
        self.inbox_tree.pack(fill="both", expand=True)
        self._refresh_peer_choices()
        self._refresh_inbox()

    def _send_message(self) -> None:
        target = self.message_to.get().strip()
        text = self.message_body.get("1.0", "end").strip()
        if not target or not text:
            messagebox.showerror("Message incomplete", "Choose a peer and enter a message.")
            return
        address = resolve_sil_address(load_registry(paths(self.home)["registry"])["entries"], target)
        if not address:
            messagebox.showerror("No address", "Add an address for this peer first.")
            return
        cfg = load_config(self.home)
        p = paths(self.home)
        self.send_button.configure(state="disabled")
        self.send_status.set("Sending...")

        def send() -> None:
            try:
                response = send_sil_message(
                    host=address[0], port=address[1],
                    msg={"message_type": "message", "from": cfg["node_id"], "to": target,
                         "intent": "human_message", "body": text},
                    node_short=str(cfg.get("node_name", "node")).upper(),
                    routing_log_path=p["routing_log"], audit_log_path=p["audit_log"], log_writes=True,
                )
                self.events.put(("sent", response))
            except Exception as exc:
                self.events.put(("send_error", str(exc)))

        threading.Thread(target=send, daemon=True).start()

    def _refresh_inbox(self) -> None:
        if not hasattr(self, "inbox_tree"):
            return
        for item in self.inbox_tree.get_children():
            self.inbox_tree.delete(item)
        for row in list_messages(paths(self.home)["inbox"], limit=100):
            msg = row["message"]
            self.inbox_tree.insert("", "end", values=(row["received_at"], row["from"], msg.get("body", "")))

    def _build_peers_tab(self) -> None:
        ttk.Label(self.peers_tab, text="Trusted Peers", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            self.peers_tab,
            text="Discovery finds connection hints. Only you can grant trust.",
        ).pack(anchor="w", pady=(4, 14))
        self.peer_tree = ttk.Treeview(self.peers_tab, columns=("identity", "address", "trust"), show="headings", height=10)
        self.peer_tree.heading("identity", text="Identity")
        self.peer_tree.heading("address", text="Address")
        self.peer_tree.heading("trust", text="Trust")
        self.peer_tree.column("identity", width=320)
        self.peer_tree.column("address", width=220)
        self.peer_tree.column("trust", width=100)
        self.peer_tree.pack(fill="both", expand=True)
        actions = ttk.Frame(self.peers_tab)
        actions.pack(fill="x", pady=12)
        ttk.Button(actions, text="Add Peer", command=self._add_peer_dialog).pack(side="left")
        ttk.Button(actions, text="Discover", command=self._discover_peers).pack(side="left", padx=8)
        ttk.Button(actions, text="Trust Selected", command=lambda: self._set_selected_trust(True)).pack(side="right")
        ttk.Button(actions, text="Remove Trust", command=lambda: self._set_selected_trust(False)).pack(side="right", padx=8)
        self.peer_status = tk.StringVar()
        ttk.Label(self.peers_tab, textvariable=self.peer_status).pack(anchor="w")
        self._refresh_peers()

    def _add_peer_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Add Peer")
        dialog.transient(self)
        dialog.grab_set()
        body = ttk.Frame(dialog, padding=18)
        body.pack(fill="both", expand=True)
        uri = tk.StringVar(value="mesh://")
        host = tk.StringVar()
        port = tk.StringVar(value="7750")
        for row, (label, variable) in enumerate((("Identity", uri), ("Host or IP", host), ("Port", port))):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", pady=5)
            ttk.Entry(body, textvariable=variable, width=42).grid(row=row, column=1, padx=10, pady=5)

        def save() -> None:
            try:
                port_value = int(port.get())
                if not uri.get().startswith("mesh://") or not host.get().strip():
                    raise ValueError("Identity and host are required")
                p = paths(self.home)
                reg = load_registry(p["registry"])
                reg["entries"] = [e for e in reg["entries"] if e.get("mesh_uri") != uri.get().strip()]
                reg["entries"].append({"mesh_uri": uri.get().strip(), "host": host.get().strip(),
                                       "port": port_value, "source": "manual"})
                write_yaml(p["registry"], reg)
            except Exception as exc:
                messagebox.showerror("Invalid peer", str(exc), parent=dialog)
                return
            dialog.destroy()
            self._refresh_peers()
            self._refresh_peer_choices()

        ttk.Button(body, text="Add", command=save).grid(row=3, column=1, sticky="e", pady=12)

    def _discover_peers(self) -> None:
        self.peer_status.set("Discovering for 5 seconds...")

        def discover() -> None:
            try:
                from .lan_mdns import collect_lan_advertisements
                p = paths(self.home)
                rows = collect_lan_advertisements(duration=5.0)
                merged = merge_registry(load_registry(p["registry"]), rows)
                write_yaml(p["registry"], merged)
                self.events.put(("discovered", len(rows)))
            except Exception as exc:
                self.events.put(("discover_error", str(exc)))

        threading.Thread(target=discover, daemon=True).start()

    def _set_selected_trust(self, trusted: bool) -> None:
        selection = self.peer_tree.selection()
        if not selection:
            return
        uri = str(self.peer_tree.item(selection[0], "values")[0])
        p = paths(self.home)
        data = load_yaml(p["trusted"], {"peers": []})
        peers = {str(x) for x in data.get("peers", [])}
        if trusted:
            peers.add(uri)
        else:
            peers.discard(uri)
        write_yaml(p["trusted"], {"peers": sorted(peers)})
        if self.server:
            self.server.cfg["trusted_peers"] = set(peers)
        self._refresh_peers()

    def _refresh_peers(self) -> None:
        if not hasattr(self, "peer_tree"):
            return
        for item in self.peer_tree.get_children():
            self.peer_tree.delete(item)
        p = paths(self.home)
        trusted = load_trusted_peers(p["trusted"]) or set()
        for entry in load_registry(p["registry"])["entries"]:
            uri = str(entry.get("mesh_uri", ""))
            address = f"{entry.get('host')}:{entry.get('port')}"
            self.peer_tree.insert("", "end", values=(uri, address, "trusted" if uri in trusted else "untrusted"))

    def _refresh_peer_choices(self) -> None:
        if not hasattr(self, "message_to_box"):
            return
        entries = load_registry(paths(self.home)["registry"])["entries"]
        self.message_to_box["values"] = [str(e.get("mesh_uri")) for e in entries if e.get("mesh_uri")]

    def _drain_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "stopped":
                    self.server = None
                    self.server_thread = None
                    self.zeroconf = None
                    self.service_info = None
                    self.node_status.set("Stopped")
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                elif event == "sent":
                    self.send_status.set(f"Delivered: {payload.get('status')} {payload.get('intent')}")
                    self.message_body.delete("1.0", "end")
                    self.send_button.configure(state="normal")
                elif event == "send_error":
                    self.send_status.set(f"Send failed: {payload}")
                    self.send_button.configure(state="normal")
                elif event == "discovered":
                    self.peer_status.set(f"Found {payload} advertisement(s). Trust was not changed.")
                    self._refresh_peers()
                    self._refresh_peer_choices()
                elif event == "discover_error":
                    self.peer_status.set(f"Discovery failed: {payload}")
        except queue.Empty:
            pass
        self.after(100, self._drain_events)

    def _close(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.zeroconf and self.service_info:
            self.zeroconf.unregister_service(self.service_info)
            self.zeroconf.close()
        self.destroy()


def main() -> None:
    MeshApp().mainloop()


if __name__ == "__main__":
    main()
