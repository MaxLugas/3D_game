import json
import os

from src.maps.editor_config import MAP_FILE


class EditorMapIoMixin:
    def delete_object(self):
        """Удаляет последний размещённый объект | Delete last placed object"""
        if not self.placed:
            return

        entry, node, _, _ = self.placed.pop()
        self.destroy_node(node)
        self.update_ui_text()

    def load_entries(self, data):
        """Разворачивает сгруппированную структуру карты в записи | Expand grouped map data into entries"""
        for model, items in data.get("objects", {}).items():
            for item in items:
                entry = {"model": model}
                entry.update(item)
                yield entry

    def load_map(self):
        """Загружает карту из JSON файла | Load map from JSON file"""
        if not os.path.exists(MAP_FILE):
            self.notice = "no map file"
            self.update_ui_text()
            return

        try:
            with open(MAP_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            self.notice = "failed to load map"
            self.update_ui_text()
            return

        for entry, node, _, _ in self.placed:
            self.destroy_node(node)
        self.placed = []

        for entry in self.load_entries(data):
            node = self.create_world_object(
                entry["model"],
                entry.get("pos", [0, 0, 0]),
                entry.get("heading", 0),
                entry.get("pitch", 0),
                entry.get("scale"),
            )
            bmin, bmax = node.getTightBounds(self.render)
            self.placed.append((entry, node, bmin, bmax))

        self.notice = f"loaded {len(self.placed)} objects"
        self.update_ui_text()
        self.taskMgr.doMethodLater(2.0, self.clear_notice, "clear_notice_map")

    def save_map(self):
        """Сохраняет карту в JSON файл | Save map to JSON file"""
        grouped = {}
        for entry, _, _, _ in self.placed:
            grouped.setdefault(entry["model"], []).append(
                {k: v for k, v in entry.items() if k != "model"}
            )

        data = {"objects": grouped}

        with open(MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        self.notice = f"saved {len(self.placed)} objects"
        self.update_ui_text()
        self.taskMgr.doMethodLater(2.0, self.clear_notice, "clear_notice")
