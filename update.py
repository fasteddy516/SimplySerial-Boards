"""A SimplySerial helper script to update board.json."""

import json
import os
from datetime import datetime
from pathlib import Path


class Board:
    vid: str = ""
    pid: str = ""
    _make: str = ""
    model: str = ""
    file: str = ""

    @property
    def id(self) -> str:
        return f"{self.vid}:{self.pid}"

    @property
    def make(self) -> str:
        return self._make

    @make.setter
    def make(self, value: str) -> None:
        # Remove various corporate/business designations
        value = value.strip()
        value = value.removesuffix(".")
        for suffix in ("llc", "inc", "ltd"):
            for s in (suffix, suffix.upper(), suffix.lower(), suffix.capitalize()):
                value = value.removesuffix(s)
        value = value.strip()
        value = value.removesuffix(",")

        # Overrides here for variations on manufacturer names
        if value.lower().find("adafruit") >= 0:
            value = "Adafruit"
        elif value.lower() == "bh dynamics":
            value = "BHDynamics"
        elif value.lower() == "blues":
            value = "Blues Wireless"
        elif value.lower() == "electroniccats":
            value = "Electronic Cats"
        elif value.lower() == "oak development technologies":
            value = "Oak Dev Tech"
        elif value.lower().find("sparkfun") >= 0:
            value = "SparkFun"
        self._make = value

    def __init__(
        self,
        vid: str = "",
        pid: str = "",
        make: str = "",
        model: str = "",
        file: str = "",
    ):
        self.vid = vid
        self.pid = pid
        self.make = make
        self.model = model
        self.file = file

    def __str__(self):
        return f"{self.vid}:{self.pid} > [{self.make}] {self.model}"

    def is_complete(self) -> bool:
        return len(self.vid) == 4 and len(self.pid) == 4 and len(self.make) and len(self.model)

    def __eq__(self, other) -> bool:
        return (
            self.vid == other.vid and self.pid == other.pid and self.make == other.make and self.model == other.model
        )


class BoardEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Board):  # Replace with your actual class type
            return {"vid": o.vid, "pid": o.pid, "make": o.make, "model": o.model}
        return super().default(o)  # Let the base class handle other types


cp_url = "https://github.com/adafruit/circuitpython"
cp_path = Path(__file__).parent / "circuitpython"
new_file = Path(__file__).parent / "boards.json"
released_file = Path(__file__).parent / "released_boards.json"
changes_file = Path("changes.txt")

# Overrides will replace the board information for the associated VID/PID only if the
# board is found in the CircuitPython repository. This is useful for boards that are
# already defined in CircuitPython but have incorrect/inconsistent information, or for
# forcing boards marked as duplicate/conflicting to use a specific set of information.
overrides = [
    Board(vid="239A", pid="8019", make="Adafruit", model="CircuitPlayground Express"),
    Board(vid="239A", pid="8023", make="Adafruit", model="Feather M0 Express"),
    Board(vid="239A", pid="8021", make="Adafruit", model="Metro M4 Express"),
    Board(vid="239A", pid="801F", make="Adafruit", model="Trinket M0"),
    Board(vid="1D50", pid="6152", make="JPConstantineau", model="BlueMicro833"),
    Board(vid="1D50", pid="6161", make="JPConstantineau", model="BlueMicro840"),
]

# Manual entries are for boards that are not currentiny defined in the CircuitPython
# repository, but are known to exist and have USB information available.  They will only
# be added to the board.json file if they are not already defined in the CircuitPython
# repository.
manual_entries = [
    Board(vid="2E8A", pid="1028", make="WIZnet", model="WizFi360-EVB-Pico"),
    Board(vid="2E8A", pid="1046", make="WIZnet", model="W6100-EVB-Pico"),
    Board(vid="2E8A", pid="109F", make="WIZnet", model="W5500-EVB-Pico2"),
    Board(vid="2E8A", pid="109F", make="WIZnet", model="W5500-EVB-Pico2"),
    Board(vid="2E8A", pid="10A0", make="WIZnet", model="W6100-EVB-Pico2"),
]

vendors = [
    {"vid": "04D8", "make": "Microchip Technology"},
    {"vid": "054C", "make": "Sony"},
    {"vid": "1209", "make": "Generic"},
    {"vid": "1915", "make": "Nordic Semiconductor"},
    {"vid": "1B4F", "make": "Sparkfun"},
    {"vid": "2341", "make": "Arduino"},
    {"vid": "239A", "make": "Adafruit"},
    {"vid": "2786", "make": "Switch Science, Inc."},
    {"vid": "2886", "make": "Seeed"},
    {"vid": "2B04", "make": "Spark Labs, Inc."},
    {"vid": "2E8A", "make": "Raspberry Pi"},
    {"vid": "303A", "make": "Espressif"},
    {"vid": "30A4", "make": "Blues Wireless"},
    {"vid": "3171", "make": "8086 Consultancy"},
    {"vid": "31E2", "make": "BDMICRO"},
    {"vid": "32BD", "make": "Alorium Technology, LLC"},
]
if not cp_path.exists():
    print(">>> Cloning CircuitPython Repository...")
    os.system(f'git clone {cp_url} "{cp_path}"')
else:
    print(">>> Updating Cloned CircuitPython Repository...")
    os.system(f'git -C "{cp_path}" pull')

if not cp_path.exists() and not cp_path.is_dir():
    raise FileNotFoundError("Unable to clone CircuiyPython repository")

files = Path.glob(cp_path / "ports", "**/boards/**/mpconfigboard.mk")

count: int = 0
boards = list()
board_ids = list()
skipped = list()
duplicates = list()
conflicts = list()
known_conflicts = list()
manual_additions = list()


def find_board(board_list, id) -> int:
    for i in range(len(board_list)):
        if board_list[i].id == id:
            return i
    return -1


for file in files:
    count += 1
    with open(str(file), encoding="utf-8") as f:
        b = Board()
        b.file = str(file)[len(str(cp_path)) + 1 :]
        for line in f.readlines():
            if line.find("USB_VID") >= 0:
                b.vid = line.upper().split("0X")[1].strip()[:4].zfill(4)
            elif line.find("USB_PID") >= 0:
                b.pid = line.upper().split("0X")[1].strip()[:4].zfill(4)
            elif line.find("USB_MANUFACTURER") >= 0:
                b.make = line.split('"')[1].strip()
            elif line.find("USB_PRODUCT") >= 0:
                b.model = line.split('"')[1].strip()
        if b.is_complete():
            if b.id in board_ids:
                if b == boards[find_board(boards, b.id)]:
                    duplicates.append(b)
                else:
                    conflicts.append(b)
            else:
                boards.append(b)
                board_ids.append(b.id)
        else:
            skipped.append(file)

for i in range(len(boards)):
    o = find_board(overrides, boards[i].id)
    if o >= 0:
        boards[i].vid = overrides[o].vid
        boards[i].pid = overrides[o].pid
        boards[i].make = overrides[o].make
        boards[i].model = overrides[o].model

for board in manual_entries:
    if find_board(boards, board.id) < 0:
        boards.append(board)
        manual_additions.append(board)

boards.sort(key=lambda b: b.id)

boardfile = {
    "version": datetime.now().isoformat().replace(":", "-"),
    "vendors": vendors,
    "boards": boards,
}

json_data = json.dumps(boardfile, indent=4, cls=BoardEncoder)

with open(str(new_file), mode="w", encoding="utf-8") as f:
    f.write(json_data)

print("")

for board in boards:
    print(board)

print(f"\nProcessed {count} files")
print(f"Identified {len(boards) + len(duplicates)} boards")
print(f"Ignored {len(duplicates)} duplicate boards:")
for board in duplicates:
    print(f"\t {board.file} (Duplicate of {boards[find_board(boards, board.id)].file})")
print(f"Ignored {len(conflicts)} boards with conflicting IDs:")
for board in conflicts:
    print(f"\t {board.file} (Same ID as {boards[find_board(boards, board.id)].file})")
print(f"Added {len(manual_entries)} manually defined boards:")
for board in manual_entries:
    print(f"\t {board}")
print(f"Skipped {len(skipped)} files with missing/incomplete USB information:")
for file in skipped:
    print(f"\t {file}")

# Determine if running in GitHub Actions
is_github_actions = "GITHUB_ENV" in os.environ
env_file = Path(os.environ["GITHUB_ENV"]) if is_github_actions else None


def set_env_variable(key, value):
    """Writes environment variables in GitHub Actions or prints them locally."""
    if is_github_actions:
        with env_file.open("a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")
    else:
        print(f"Setting environment variable: {key}={value}")  # Local debug output


# Load both JSON files (if released_boards.json exists)
if released_file.exists():
    with released_file.open("r", encoding="utf-8") as f:
        old_data = json.load(f)

    with new_file.open("r", encoding="utf-8") as f:
        new_data = json.load(f)

    # Extract vendors and boards
    old_vendors = {v["vid"]: v for v in old_data.get("vendors", [])}
    new_vendors = {v["vid"]: v for v in new_data.get("vendors", [])}
    old_boards = {f"{b['vid']}:{b['pid']}": b for b in old_data.get("boards", [])}
    new_boards = {f"{b['vid']}:{b['pid']}": b for b in new_data.get("boards", [])}

    # Determine changes
    added_vendors = [v for vid, v in new_vendors.items() if vid not in old_vendors]
    removed_vendors = [v for vid, v in old_vendors.items() if vid not in new_vendors]
    modified_vendors = [v for vid, v in new_vendors.items() if vid in old_vendors and v != old_vendors[vid]]

    added_boards = [b for bid, b in new_boards.items() if bid not in old_boards]
    removed_boards = [b for bid, b in old_boards.items() if bid not in new_boards]
    modified_boards = [b for bid, b in new_boards.items() if bid in old_boards and b != old_boards[bid]]

    # Generate changes.txt
    with changes_file.open("w", encoding="utf-8") as f:
        if added_vendors:
            f.write("Added Vendors:\n")
            for v in added_vendors:
                f.write(f" + {v['vid']}: {v['make']}\n")
            f.write("\n")

        if removed_vendors:
            f.write("Removed Vendors:\n")
            for v in removed_vendors:
                f.write(f" - {v['vid']}: {v['make']}\n")
            f.write("\n")

        if modified_vendors:
            f.write("Modified Vendors:\n")
            for v in modified_vendors:
                f.write(f" * {v['vid']}: {v['make']}\n")
            f.write("\n")

        if added_boards:
            f.write("Added Boards:\n")
            for b in added_boards:
                f.write(f" + {b['vid']}:{b['pid']} [{b['make']}] {b['model']}\n")
            f.write("\n")

        if removed_boards:
            f.write("Removed Boards:\n")
            for b in removed_boards:
                f.write(f" - {b['vid']}:{b['pid']} [{b['make']}] {b['model']}\n")
            f.write("\n")

        if modified_boards:
            f.write("Modified Boards:\n")
            for b in modified_boards:
                f.write(f" * {b['vid']}:{b['pid']} [{b['make']}] {b['model']}\n")
            f.write("\n")

        if not (
            added_vendors or removed_vendors or modified_vendors or added_boards or removed_boards or modified_boards
        ):
            f.write("No significant changes detected.\n")

    # If only version changed, skip release
    if not (added_vendors or removed_vendors or modified_vendors or added_boards or removed_boards or modified_boards):
        print("No changes detected (other than version). Skipping release.")
        set_env_variable("CHANGES_DETECTED", "false")
        exit(0)
else:
    # First-time run: Generate initial changes.txt
    with changes_file.open("w", encoding="utf-8") as f:
        f.write("Initial Release\n")
    print("Initial release detected.")

print("Changes detected or first-time run. Proceeding with release.")
set_env_variable("CHANGES_DETECTED", "true")
