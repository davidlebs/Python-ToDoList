import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

data_file = Path("todo_gui.json")


def load_tasks() -> list[dict]:
    if not data_file.exists():
        return []
    try:
        data = json.loads(data_file.read_text(encoding="utf-8"))
        if isinstance(data, list):
            out = []
            for item in data:
                if isinstance(item, dict) and "text" in item:
                    out.append({"text": str(item["text"]), "done": bool(item.get("done", False))})
            return out
    except Exception:
        pass
    return []


def save_tasks(tasks: list[dict]) -> None:
    data_file.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


class TodoGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("To-Do")
        self.geometry("640x460")
        self.minsize(560, 420)

        # Use a modern ttk theme if available
        try:
            self.style = ttk.Style(self)
            if "clam" in self.style.theme_names():
                self.style.theme_use("clam")
        except Exception:
            self.style = ttk.Style(self)

        self._make_styles()

        self.tasks: list[dict] = load_tasks()

        self._build_ui()
        self._refresh_list()

    def _make_styles(self):
        # Slightly larger default font
        base_font = ("Segoe UI", 11)
        self.option_add("*Font", base_font)

        self.style.configure("Card.TFrame", padding=14)
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"))
        self.style.configure("Subheader.TLabel", font=("Segoe UI", 10))
        self.style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=(12, 8))
        self.style.configure("Ghost.TButton", padding=(12, 8))
        self.style.configure("Danger.TButton", padding=(12, 8))
        # Make danger button stand out a bit (ttk colors are theme-dependent)
        self.style.map("Danger.TButton", foreground=[("active", "white")])

    def _build_ui(self):
        # ---- Outer layout
        outer = ttk.Frame(self, padding=14)
        outer.pack(fill="both", expand=True)

        # ---- Header
        header = ttk.Frame(outer)
        header.pack(fill="x")

        ttk.Label(header, text="To-Do List", style="Header.TLabel").pack(anchor="w")
        self.status = tk.StringVar(value="")
        ttk.Label(header, textvariable=self.status, style="Subheader.TLabel").pack(anchor="w", pady=(2, 0))

        ttk.Separator(outer).pack(fill="x", pady=12)

        # ---- "Card" container
        card = ttk.Frame(outer, style="Card.TFrame")
        card.pack(fill="both", expand=True)

        # ---- Add row
        add_row = ttk.Frame(card)
        add_row.pack(fill="x")

        self.task_var = tk.StringVar()
        self.entry = ttk.Entry(add_row, textvariable=self.task_var)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self.add_task())

        ttk.Button(add_row, text="Add", style="Primary.TButton", command=self.add_task).pack(side="left", padx=(10, 0))

        hint = ttk.Label(
            card,
            text="Tip: Double-click a task to toggle complete. Press Delete to remove.",
            style="Subheader.TLabel",
        )
        hint.pack(anchor="w", pady=(8, 10))

        # ---- List area (framed)
        list_frame = ttk.Frame(card)
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            height=12,
            activestyle="none",
            selectmode="browse",
            borderwidth=0,
            highlightthickness=1,
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scroll.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scroll.set)

        self.listbox.bind("<Double-Button-1>", lambda e: self.toggle_done())
        self.listbox.bind("<Delete>", lambda e: self.delete_task())

        # ---- Actions row
        actions = ttk.Frame(card)
        actions.pack(fill="x", pady=(12, 0))

        ttk.Button(actions, text="Toggle", style="Ghost.TButton", command=self.toggle_done).pack(side="left")
        ttk.Button(actions, text="Clear Completed", style="Ghost.TButton", command=self.clear_completed).pack(
            side="left", padx=8
        )
        ttk.Button(actions, text="Delete", style="Danger.TButton", command=self.delete_task).pack(side="left")

        ttk.Button(actions, text="Save", style="Ghost.TButton", command=self.save).pack(side="right")
        ttk.Button(actions, text="Quit", style="Ghost.TButton", command=self.on_quit).pack(side="right", padx=(0, 8))

        # Focus on entry at start
        self.after(100, self.entry.focus_set)

    def _format_line(self, t: dict) -> str:
        # Nice spacing + emoji status
        return f"{'✅' if t['done'] else '⬜'}  {t['text']}"

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for t in self.tasks:
            self.listbox.insert(tk.END, self._format_line(t))

        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t["done"])
        self.status.set(f"{done}/{total} completed • saved in {data_file.name}")

        # Subtle visual tweak: gray out completed tasks (works on most platforms)
        for i, t in enumerate(self.tasks):
            try:
                if t["done"]:
                    self.listbox.itemconfig(i, fg="gray")
            except tk.TclError:
                pass

    def _selected_index(self) -> int | None:
        sel = self.listbox.curselection()
        return int(sel[0]) if sel else None

    def add_task(self):
        text = self.task_var.get().strip()
        if not text:
            messagebox.showinfo("Empty task", "Type a task first.")
            return
        self.tasks.append({"text": text, "done": False})
        self.task_var.set("")
        self.save()
        self._refresh_list()

    def toggle_done(self):
        idx = self._selected_index()
        if idx is None:
            messagebox.showinfo("No selection", "Select a task to toggle.")
            return
        self.tasks[idx]["done"] = not self.tasks[idx]["done"]
        self.save()
        self._refresh_list()
        self.listbox.selection_set(idx)

    def delete_task(self):
        idx = self._selected_index()
        if idx is None:
            messagebox.showinfo("No selection", "Select a task to delete.")
            return
        text = self.tasks[idx]["text"]
        if not messagebox.askyesno("Delete task", f"Delete this task?\n\n{text}"):
            return
        self.tasks.pop(idx)
        self.save()
        self._refresh_list()

    def clear_completed(self):
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if not t["done"]]
        removed = before - len(self.tasks)
        self.save()
        self._refresh_list()
        messagebox.showinfo("Cleared", f"Removed {removed} completed task(s).")

    def save(self):
        save_tasks(self.tasks)

    def on_quit(self):
        self.save()
        self.destroy()


if __name__ == "__main__":
    TodoGUI().mainloop()
