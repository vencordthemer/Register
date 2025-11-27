# === teacher_gui.py ===
import tkinter as tk
from tkinter import messagebox
import json, os
from datetime import date, datetime
import getpass

BASE_DIR = "Register"
ATT_DIR = os.path.join(BASE_DIR, "attendance")
CHAT_FILE = os.path.join(BASE_DIR, "chat.json")
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(ATT_DIR, exist_ok=True)
if not os.path.exists(CHAT_FILE):
    with open(CHAT_FILE, "w") as f:
        json.dump([], f)

# ---------------- JSON Helpers ----------------
def load_json(filename):
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f)
    with open(path, "r") as f:
        return json.load(f)

def save_json(filename, data):
    with open(os.path.join(BASE_DIR, filename), "w") as f:
        json.dump(data, f, indent=2)

def append_chat(sender, recipient, message):
    with open(CHAT_FILE, "r") as f:
        chat = json.load(f)
    chat.append({
        "from": sender,
        "to": recipient,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    with open(CHAT_FILE, "w") as f:
        json.dump(chat, f, indent=2)

# ---------------- Attendance Marking ----------------
def mark_attendance(class_name, students):
    today_file = os.path.join(ATT_DIR, f"{date.today()}.json")
    # Load today's attendance if exists
    if os.path.exists(today_file):
        with open(today_file, "r") as f:
            att = json.load(f)
    else:
        att = {}

    # Ensure this class has an entry
    att[class_name] = att.get(class_name, {})

    att_win = tk.Toplevel()
    att_win.title(f"Attendance for {class_name}")
    text_vars = {}

    for i, student in enumerate(students):
        tk.Label(att_win, text=student).grid(row=i, column=0, padx=5, pady=2)

        # Default to admin-set status or "P"
        current_status = att[class_name].get(student, "present")
        var = tk.StringVar(value=current_status[0].upper())  # "P", "A", "L"
        text_vars[student] = var

        tk.OptionMenu(att_win, var, "P", "A", "L").grid(row=i, column=1)

    def save_att():
        for student, var in text_vars.items():
            val = var.get()
            if val == "P":
                att[class_name][student] = "present"
            elif val == "A":
                att[class_name][student] = "absent"
            elif val == "L":
                att[class_name][student] = "late"
        with open(today_file, "w") as f:
            json.dump(att, f, indent=2)
        messagebox.showinfo("Saved", f"Attendance saved for {class_name}")
        att_win.destroy()

    tk.Button(att_win, text="Save", command=save_att).grid(row=len(students), column=0, columnspan=2, pady=5)

# ---------------- Chat System ----------------
def open_teacher_chat(teacher_name):
    chat_win = tk.Toplevel()
    chat_win.title(f"Chat with Admin - {teacher_name}")
    text_area = tk.Text(chat_win,state="disabled", width=50, height=15)
    text_area.pack(pady=5)
    entry = tk.Entry(chat_win,width=40)
    entry.pack(side="left", padx=5)

    def send_message():
        msg = entry.get().strip()
        if not msg: return
        append_chat(teacher_name,"admin",msg)
        entry.delete(0, tk.END)

    tk.Button(chat_win,text="Send",command=send_message).pack(side="left")

    def refresh():
        text_area.config(state="normal")
        text_area.delete(1.0,tk.END)
        with open(CHAT_FILE,"r") as f:
            chat = json.load(f)
        for m in chat:
            if m["from"]==teacher_name or m["to"]==teacher_name:
                text_area.insert(tk.END,f"{m['from']}: {m['message']}\n")
        text_area.config(state="disabled")
        chat_win.after(1000,refresh)

    def on_close():
        with open(CHAT_FILE,"r") as f:
            chat = json.load(f)
        chat = [m for m in chat if m["from"] != teacher_name]
        with open(CHAT_FILE,"w") as f:
            json.dump(chat, f, indent=2)
        chat_win.destroy()

    chat_win.protocol("WM_DELETE_WINDOW", on_close)
    refresh()

# ---------------- Class Selection Page ----------------
def open_class_window(teacher):
    login_frame.pack_forget()
    class_frame.pack(padx=10,pady=10)
    for w in class_frame.winfo_children(): w.destroy()

    classes = teacher.get("classes",[])
    if not classes:
        tk.Label(class_frame,text="No classes assigned").pack()
        return

    tk.Label(class_frame,text=f"Welcome {teacher['name']}! Select a class:").pack(pady=5)

    for class_name in classes:
        students=[]
        for cls in load_json("classes.json"):
            if cls["name"]==class_name: students=cls.get("students",[])

        f = tk.Frame(class_frame)
        f.pack(pady=4)
        tk.Label(f, text=class_name, font=("Arial", 11, "bold")).pack()

        # Only buttons, no pre-view
        tk.Button(f, text="Take Register",
                  width=25,
                  command=lambda c=class_name, s=students: mark_attendance(c, s)).pack(pady=1)

    tk.Button(class_frame,text="Help / Chat with Admin",
              command=lambda: open_teacher_chat(teacher['name'])).pack(pady=5)

# ---------------- Login ----------------
def login_teacher():
    name=username_entry.get()
    password=password_entry.get()
    for t in load_json("teachers.json"):
        if t["name"]==name and t["password"]==password:
            open_class_window(t)
            return
    messagebox.showerror("Error","Invalid login")

# ---------------- GUI Setup ----------------
root=tk.Tk()
root.title("Teacher Login")

login_frame=tk.Frame(root)
tk.Label(login_frame,text="Username").pack(pady=2)
username_entry=tk.Entry(login_frame)
username_entry.pack(pady=2)
tk.Label(login_frame,text="Password").pack(pady=2)
password_entry=tk.Entry(login_frame,show="*")
password_entry.pack(pady=2)
tk.Button(login_frame,text="Login",command=login_teacher).pack(pady=5)
login_frame.pack(padx=10,pady=10)

class_frame=tk.Frame(root)
root.mainloop()

