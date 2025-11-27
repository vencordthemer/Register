import tkinter as tk
from tkinter import messagebox
import json, os, getpass, threading, time, queue
from datetime import datetime, date

BASE_DIR = "Register"
ATT_DIR = os.path.join(BASE_DIR, "attendance")
CHAT_FILE = os.path.join(BASE_DIR, "chat.json")
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(ATT_DIR, exist_ok=True)

# JSON files
TEACHERS_FILE = os.path.join(BASE_DIR, "teachers.json")
STUDENTS_FILE = os.path.join(BASE_DIR, "students.json")
CLASSES_FILE = os.path.join(BASE_DIR, "classes.json")
ADMINS_FILE = os.path.join(BASE_DIR, "admins.json")

# Ensure files exist
for f in [TEACHERS_FILE, STUDENTS_FILE, CLASSES_FILE, CHAT_FILE, ADMINS_FILE]:
    if not os.path.exists(f):
        with open(f, "w") as file:
            json.dump([], file)

# ---------------- JSON helpers ----------------
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- Chat helpers ----------------
def append_chat(sender, recipient, message):
    chat = load_json(CHAT_FILE)
    chat.append({
        "from": sender,
        "to": recipient,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_json(CHAT_FILE, chat)

# ---------------- Global Notification ----------------
chat_gui_open = False
notify_queue = queue.Queue()
stop_event = threading.Event()

def chat_listener():
    """Background thread to detect new teacher messages for admin."""
    last_seen = 0
    while not stop_event.is_set():
        chat = load_json(CHAT_FILE)
        new_messages = chat[last_seen:]
        for m in new_messages:
            if m["to"] == "admin" and m["from"] != "admin" and not chat_gui_open:
                notify_queue.put((m["from"], m["message"]))
        last_seen = len(chat)
        time.sleep(1)

def poll_notifications(root):
    """Poll the queue for messages and show notifications on main thread."""
    while not notify_queue.empty():
        sender, msg = notify_queue.get()
        messagebox.showinfo(f"New message from {sender}", msg)
    root.after(1000, lambda: poll_notifications(root))

# ---------------- GUI Windows ----------------
def gui_add_teacher(parent):
    win = tk.Toplevel(parent)
    win.title("Add Teacher")

    tk.Label(win, text="Teacher Name").grid(row=0, column=0, pady=5, padx=5)
    name_entry = tk.Entry(win)
    name_entry.grid(row=0, column=1, pady=5, padx=5)

    tk.Label(win, text="Password").grid(row=1, column=0, pady=5, padx=5)
    password_entry = tk.Entry(win, show="*")
    password_entry.grid(row=1, column=1, pady=5, padx=5)

    def save_teacher():
        name = name_entry.get().strip()
        pwd = password_entry.get().strip()
        if not name or not pwd:
            messagebox.showerror("Error", "All fields required")
            return
        teachers = load_json(TEACHERS_FILE)
        teachers.append({"name": name, "password": pwd, "classes": []})
        save_json(TEACHERS_FILE, teachers)
        messagebox.showinfo("Success", f"Teacher '{name}' added!")
        win.destroy()

    tk.Button(win, text="Save", command=save_teacher).grid(row=2, column=0, columnspan=2, pady=10)

def gui_add_student(parent):
    win = tk.Toplevel(parent)
    win.title("Add Student")

    tk.Label(win, text="Student Name").grid(row=0, column=0, pady=5, padx=5)
    name_entry = tk.Entry(win)
    name_entry.grid(row=0, column=1, pady=5, padx=5)

    tk.Label(win, text="Year").grid(row=1, column=0, pady=5, padx=5)
    year_entry = tk.Entry(win)
    year_entry.grid(row=1, column=1, pady=5, padx=5)

    def save_student():
        name = name_entry.get().strip()
        year = year_entry.get().strip()
        if not name or not year:
            messagebox.showerror("Error", "All fields required")
            return
        students = load_json(STUDENTS_FILE)
        students.append({"name": name, "year": year, "classes": []})
        save_json(STUDENTS_FILE, students)
        messagebox.showinfo("Success", f"Student '{name}' added!")
        win.destroy()

    tk.Button(win, text="Save", command=save_student).grid(row=2, column=0, columnspan=2, pady=10)

def gui_add_class(parent):
    win = tk.Toplevel(parent)
    win.title("Add Class")

    tk.Label(win, text="Class Name").grid(row=0, column=0, pady=5, padx=5)
    class_entry = tk.Entry(win)
    class_entry.grid(row=0, column=1, pady=5, padx=5)

    tk.Label(win, text="Assign Teacher").grid(row=1, column=0, pady=5, padx=5)
    teachers = [t["name"] for t in load_json(TEACHERS_FILE)]
    teacher_var = tk.StringVar(win)
    if teachers: teacher_var.set(teachers[0])
    tk.OptionMenu(win, teacher_var, *teachers).grid(row=1, column=1, pady=5, padx=5)

    def save_class():
        cname = class_entry.get().strip()
        tname = teacher_var.get()
        if not cname or not tname:
            messagebox.showerror("Error", "All fields required")
            return
        classes = load_json(CLASSES_FILE)
        classes.append({"name": cname, "teacher": tname, "students": []})
        save_json(CLASSES_FILE, classes)
        # Assign class to teacher
        teachers_data = load_json(TEACHERS_FILE)
        for t in teachers_data:
            if t["name"] == tname:
                t.setdefault("classes", []).append(cname)
        save_json(TEACHERS_FILE, teachers_data)
        messagebox.showinfo("Success", f"Class '{cname}' assigned to {tname}!")
        win.destroy()

    tk.Button(win, text="Save", command=save_class).grid(row=2, column=0, columnspan=2, pady=10)

def gui_assign_student(parent):
    win = tk.Toplevel(parent)
    win.title("Assign Student to Class")

    students = [s["name"] for s in load_json(STUDENTS_FILE)]
    classes = [c["name"] for c in load_json(CLASSES_FILE)]

    tk.Label(win, text="Select Student").grid(row=0, column=0, pady=5, padx=5)
    student_var = tk.StringVar(win)
    if students: student_var.set(students[0])
    tk.OptionMenu(win, student_var, *students).grid(row=0, column=1, pady=5, padx=5)

    tk.Label(win, text="Select Class").grid(row=1, column=0, pady=5, padx=5)
    class_var = tk.StringVar(win)
    if classes: class_var.set(classes[0])
    tk.OptionMenu(win, class_var, *classes).grid(row=1, column=1, pady=5, padx=5)

    def save_assign():
        sname = student_var.get()
        cname = class_var.get()
        if not sname or not cname:
            messagebox.showerror("Error", "All fields required")
            return
        # Add student to class
        classes_data = load_json(CLASSES_FILE)
        for c in classes_data:
            if c["name"] == cname:
                if sname not in c.setdefault("students", []):
                    c["students"].append(sname)
        save_json(CLASSES_FILE, classes_data)
        # Add class to student
        students_data = load_json(STUDENTS_FILE)
        for s in students_data:
            if s["name"] == sname:
                if cname not in s.setdefault("classes", []):
                    s["classes"].append(cname)
        save_json(STUDENTS_FILE, students_data)
        messagebox.showinfo("Success", f"{sname} assigned to {cname}!")
        win.destroy()

    tk.Button(win, text="Save", command=save_assign).grid(row=2, column=0, columnspan=2, pady=10)

def gui_add_absence(parent):
    win = tk.Toplevel(parent)
    win.title("Add Absence for Student")

    all_students = [s["name"] for s in load_json(STUDENTS_FILE)]

    tk.Label(win, text="Search Student").grid(row=0, column=0, pady=5, padx=5)
    search_var = tk.StringVar()
    search_entry = tk.Entry(win, textvariable=search_var)
    search_entry.grid(row=0, column=1, pady=5, padx=5)

    tk.Label(win, text="Select Student").grid(row=1, column=0, pady=5, padx=5)
    student_var = tk.StringVar(win)
    if all_students: student_var.set(all_students[0])
    student_menu = tk.OptionMenu(win, student_var, *all_students)
    student_menu.grid(row=1, column=1, pady=5, padx=5)

    def update_student_list(*args):
        search = search_var.get().lower()
        filtered = [s for s in all_students if search in s.lower()]
        menu = student_menu["menu"]
        menu.delete(0, "end")
        for s in filtered:
            menu.add_command(label=s, command=tk._setit(student_var, s))
        if filtered:
            student_var.set(filtered[0])

    search_var.trace_add("write", update_student_list)

    def save_absence():
        sname = student_var.get()
        if not sname:
            return
        today_file = os.path.join(ATT_DIR, f"{date.today()}.json")
        if os.path.exists(today_file):
            with open(today_file, "r") as f:
                att = json.load(f)
        else:
            att = {}
        students_data = load_json(STUDENTS_FILE)
        student_classes = []
        for s in students_data:
            if s["name"] == sname:
                student_classes = s.get("classes", [])
        for c in student_classes:
            att.setdefault(c, {})[sname] = "absent"
        with open(today_file, "w") as f:
            json.dump(att, f, indent=2)
        messagebox.showinfo("Success", f"{sname} marked absent in all classes today!")
        win.destroy()

    tk.Button(win, text="Save", command=save_absence).grid(row=2, column=0, columnspan=2, pady=10)

# ---------------- Chat GUI ----------------
def gui_reply_teacher(parent):
    global chat_gui_open
    chat_gui_open = True

    win = tk.Toplevel(parent)
    win.title("Chat with Teachers")

    text_area = tk.Text(win, state="disabled", width=60, height=20)
    text_area.pack(pady=5)

    teachers = sorted(set(m["from"] for m in load_json(CHAT_FILE) if m["to"] == "admin"))
    teacher_var = tk.StringVar(win)
    teacher_var.set(teachers[0] if teachers else "")

    teacher_menu = tk.OptionMenu(win, teacher_var, *teachers)
    teacher_menu.pack(pady=5)

    entry = tk.Entry(win, width=50)
    entry.pack(side="left", padx=5)

    def send_message():
        t = teacher_var.get()
        msg = entry.get().strip()
        if not t or not msg:
            return
        append_chat("admin", t, msg)
        entry.delete(0, tk.END)
        messagebox.showinfo("Sent", f"Message sent to {t}!")

    tk.Button(win, text="Send", command=send_message).pack(side="left")

    last_seen = 0

    def refresh():
        nonlocal last_seen
        text_area.config(state="normal")
        chat = load_json(CHAT_FILE)
        new_messages = chat[last_seen:]
        for m in new_messages:
            if m["from"] == "admin" or m["to"] == "admin":
                text_area.insert(tk.END, f"{m['from']} -> {m['to']}: {m['message']}\n")
        last_seen = len(chat)

        menu = teacher_menu["menu"]
        for m in new_messages:
            if m["to"] == "admin" and m["from"] != "admin" and m["from"] not in teachers:
                teachers.append(m["from"])
                menu.add_command(label=m["from"], command=tk._setit(teacher_var, m["from"]))

        text_area.config(state="disabled")
        win.after(1000, refresh)

    def on_close():
        global chat_gui_open
        chat_gui_open = False
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)
    refresh()

# ---------------- Admin CLI ----------------
def admin_menu():
    listener_thread = threading.Thread(target=chat_listener, daemon=True)
    listener_thread.start()

    root = tk.Tk()
    root.withdraw()  # hidden root for notifications
    poll_notifications(root)

    while True:
        print("\n--- Admin Menu ---")
        print("1. Add Teacher")
        print("2. Add Student")
        print("3. Add Class")
        print("4. Assign Student to Class")
        print("5. Add Absence For Student")
        print("6. Reply to Teacher (Chat)")
        print("7. Logout")
        choice = input("Choice: ").strip()
        if choice == "1":
            gui_add_teacher(root)
        elif choice == "2":
            gui_add_student(root)
        elif choice == "3":
            gui_add_class(root)
        elif choice == "4":
            gui_assign_student(root)
        elif choice == "5":
            gui_add_absence(root)
        elif choice == "6":
            gui_reply_teacher(root)
        elif choice == "7":
            stop_event.set()
            break
        else:
            print("Invalid choice!")

def login_admin():
    name = input("Admin Name: ")
    pwd = getpass.getpass("Password: ")
    admins = load_json(ADMINS_FILE)
    for a in admins:
        if a["name"] == name and a["password"] == pwd:
            print(f"Welcome {name}!")
            admin_menu()
            return
    print("Invalid login!")

if __name__ == "__main__":
    login_admin()
