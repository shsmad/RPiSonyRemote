from enum import Enum
from typing import Any, Optional


class ParamType(Enum):
    EXIT = 0
    INT = 1
    FLOAT = 2
    BOOL = 3
    FOLDER = 4


class MenuItem:
    def __init__(
        self,
        title: str,
        type: ParamType,
        storage: Any,
        icon: Optional[str] = None,
        children: Optional[list["MenuItem"]] = None,
        default_value: Optional[Any] = None,
    ):
        self.title = title
        self.type = type
        self.icon = icon
        self.children: list[MenuItem] = children or []
        self.storage = storage
        self.default_value = default_value

    @property
    def value(self) -> Any:
        print(f"in getter {self.title}")
        try:
            from_db = self.storage.get(self.title)
            if not from_db:
                return self.default_value

            if self.type == ParamType.BOOL:
                return bool(from_db)
            elif self.type == ParamType.INT:
                return int(from_db)
            elif self.type == ParamType.FLOAT:
                return float(from_db)
            else:
                return None
        except Exception as e:
            print(e)

        return self.storage.get(self.title, self.default_value)

    @value.setter
    def value(self, v: Any) -> None:
        print(f"in setter {self.title} {v}")
        try:
            if self.type == ParamType.BOOL:
                self.storage[self.title] = "1" if v else ""
            elif self.type in (ParamType.INT, ParamType.FLOAT):
                self.storage[self.title] = str(v)
            else:
                return
        except Exception as e:
            print(e)


def create_menu_tree(storage: Any) -> list[MenuItem]:
    exit_item = MenuItem("Exit", ParamType.EXIT, storage)

    return [
        MenuItem(
            "Trigger",
            ParamType.FOLDER,
            storage,
            icon="bell",
            children=[
                MenuItem("A.Enable", ParamType.BOOL, storage, default_value=False),
                MenuItem("AThreshold", ParamType.INT, storage, default_value=200),
                MenuItem("A.Above", ParamType.BOOL, storage, default_value=False),
                MenuItem("D.Enable", ParamType.BOOL, storage, default_value=True),
                MenuItem("D.Above", ParamType.BOOL, storage, default_value=True),
                MenuItem("Emmitter", ParamType.BOOL, storage, default_value=False),
                exit_item,
            ],
        ),
        MenuItem(
            "Timer",
            ParamType.FOLDER,
            storage,
            icon="stopwatch",
            children=[exit_item],
        ),
        MenuItem(
            "Settings",
            ParamType.FOLDER,
            storage,
            icon="screwdriver-wrench",
            children=[
                MenuItem("Shut.Delay", ParamType.INT, storage, default_value=0),
                MenuItem("Relz.Delay", ParamType.INT, storage, default_value=60),
                MenuItem("Optron Out", ParamType.BOOL, storage, default_value=True),
                MenuItem("Blink Out", ParamType.BOOL, storage, default_value=True),
                MenuItem("ReadTimer", ParamType.INT, storage, default_value=60),
                exit_item,
            ],
        ),
        MenuItem(
            "Bluetooth",
            ParamType.FOLDER,
            storage,
            icon="bluetooth",
            children=[
                MenuItem("Enable BT", ParamType.BOOL, storage, default_value=False),
                exit_item,
            ],
        ),
    ]
