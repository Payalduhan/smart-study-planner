import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
from tkcalendar import Calendar

# ========================= DATABASE ==========================

def pick_exam_date(root):
    def save_date():
        exam_date = cal.get_date()
        print("Selected Exam Date:", exam_date)
        date_window.destroy()

    date_window = tk.Toplevel(root)
    cal = Calendar(date_window, selectmode='day')
    cal.pack(pady=20)

    tk.Button(date_window, text="Save Date", command=save_date).pack()

class DB:
    def __init__(self):
        self.conn = sqlite3.connect("study_planner.db")
        self.cursor = self.conn.cursor()
        # Create subjects table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects(
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT,
               weight INTEGER
             )
         """)
        # Create history table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS history(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                subject TEXT,
                status TEXT
            )
        """)
        self.conn.commit()

    def get_subjects(self):
        self.cursor.execute("SELECT name, weight FROM subjects")
        return self.cursor.fetchall()

    def add_subject(self, name, weight):
        self.cursor.execute("INSERT INTO subjects(name, weight) VALUES (?, ?)", (name, weight))
        self.conn.commit()

    def remove_subject(self, name):
        self.cursor.execute("DELETE FROM subjects WHERE name=?", (name,))
        self.conn.commit()

    def save_history(self, date, subject, status):
        self.cursor.execute("INSERT INTO history(date, subject, status) VALUES (?, ?, ?)", (date, subject, status))
        self.conn.commit()

    def get_history(self):
        self.cursor.execute("SELECT date, subject, status FROM history ORDER BY id DESC")
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

# ========================= MAIN APP ==========================

class StudyPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📘 Study Planner - Timetable Generator")
        self.root.geometry("950x700")
        self.root.config(bg="#f0f8ff")

        self.db = DB()
        self.checkbox_vars = {}  # Initialize here to avoid attribute errors

        title = tk.Label(root, text="📚 Smart Study Planner 📚",
                         font=("Arial", 26, "bold"), bg="#4682b4", fg="white", pady=15)
        title.pack(fill="x")

        # ---------------- Subjects Frame ----------------
        frame1 = tk.Frame(root, bg="#f0f8ff", pady=10)
        frame1.pack()

        tk.Label(frame1, text="Subject:", font=("Arial", 14, "bold"), bg="#f0f8ff").grid(row=0, column=0, padx=5)
        self.subject_entry = tk.Entry(frame1, font=("Arial", 14))
        self.subject_entry.grid(row=0, column=1, padx=5)

        tk.Label(frame1, text="Weight:", font=("Arial", 14, "bold"), bg="#f0f8ff").grid(row=0, column=2, padx=5)
        self.weight_entry = tk.Entry(frame1, font=("Arial", 14))
        self.weight_entry.grid(row=0, column=3, padx=5)

        ttk.Button(frame1, text="➕ Add Subject", command=self.add_subject).grid(row=0, column=4, padx=10)
        ttk.Button(frame1, text="❌ Remove Subject", command=self.remove_subject).grid(row=0, column=5, padx=10)

        # ---------------- Subject List ----------------
        self.subject_listbox = tk.Listbox(root, font=("Arial", 13), height=6, width=40, bg="#faf0e6", fg="black")
        self.subject_listbox.pack(pady=10)

        # ---------------- Timetable ----------------
        ttk.Button(root, text="📅 Generate Timetable", command=self.generate_timetable).pack(pady=10)

        self.tree = ttk.Treeview(root, columns=("Day", "Tasks"), show="headings", height=7)
        self.tree.heading("Day", text="Day")
        self.tree.heading("Tasks", text="Tasks")
        self.tree.column("Day", width=150, anchor="center")
        self.tree.column("Tasks", width=700, anchor="center")
        self.tree.pack(pady=10)

        # ------------ Calendar Button -------------------
        exam_btn = tk.Button(root, text="Pick Exam Date", command=lambda: pick_exam_date(root))
        exam_btn.pack(pady=10)

        # ---------------- Checkboxes ----------------
        tk.Label(root, text="☑ Daily Progress Tracker", font=("Arial", 18, "bold"),
                 bg="#f0f8ff", fg="#2e8b57").pack(pady=10)

        self.checkboxes_frame = tk.Frame(root, bg="#f0f8ff")
        self.checkboxes_frame.pack()

        ttk.Button(root, text="💾 Save Today's Progress", command=self.save_progress).pack(pady=10)
        ttk.Button(root, text="📜 View Study History", command=self.view_history).pack(pady=10)

        # ---------------- Load Subjects ----------------
        self.load_subjects()

    # ---------- Subject Functions ----------
    def add_subject(self):
        name = self.subject_entry.get().strip()
        weight = self.weight_entry.get().strip()
        if name and weight.isdigit():
            self.db.add_subject(name, int(weight))
            self.load_subjects()
            self.subject_entry.delete(0, "end")
            self.weight_entry.delete(0, "end")
        else:
            messagebox.showerror("Error", "Enter valid subject and weight (number).")

    def remove_subject(self):
        selected = self.subject_listbox.curselection()
        if selected:
            name = self.subject_listbox.get(selected[0]).split(" (")[0]
            self.db.remove_subject(name)
            self.load_subjects()
        else:
            messagebox.showerror("Error", "Select a subject to remove.")

    def load_subjects(self):
        self.subject_listbox.delete(0, "end")
        subjects = self.db.get_subjects()
        for sub in subjects:
            self.subject_listbox.insert("end", f"{sub[0]} (Weight: {sub[1]})")

    # ---------- Timetable ----------
    def generate_timetable(self):
        subjects = self.db.get_subjects()
        if not subjects:
            messagebox.showerror("Error", "Add subjects first!")
            return

        self.tree.delete(*self.tree.get_children())
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for i, day in enumerate(days):
            tasks = ", ".join([subjects[(i + j) % len(subjects)][0] for j in range(3)])
            self.tree.insert("", "end", values=(day, tasks))

        # Create checkboxes for progress
        for widget in self.checkboxes_frame.winfo_children():
            widget.destroy()

        self.checkbox_vars = {}
        for subject, _ in subjects:
            var = tk.IntVar()
            cb = tk.Checkbutton(self.checkboxes_frame, text=subject, variable=var,
                                font=("Arial", 14), bg="#f0f8ff", fg="black")
            cb.pack(anchor="w")
            self.checkbox_vars[subject] = var

        messagebox.showinfo("Success", "Timetable generated and shown below ✅")

    # ---------- Save Progress ----------
    def save_progress(self):
        if not self.checkbox_vars:
            messagebox.showerror("Error", "Generate timetable first to save progress.")
            return

        today = datetime.date.today().strftime("%Y-%m-%d")
        for subject, var in self.checkbox_vars.items():
            status = "Done" if var.get() else "Not Done"
            self.db.save_history(today, subject, status)
        messagebox.showinfo("Saved", "Today's progress has been saved ✅")

    # ---------- View History ----------
    def view_history(self):
        history = self.db.get_history()
        if not history:
            messagebox.showinfo("History", "No history found yet!")
            return

        history_win = tk.Toplevel(self.root)
        history_win.title("📜 Study History")
        history_win.geometry("600x400")

        tree = ttk.Treeview(history_win, columns=("Date", "Subject", "Status"), show="headings")
        tree.heading("Date", text="Date")
        tree.heading("Subject", text="Subject")
        tree.heading("Status", text="Status")
        tree.pack(fill="both", expand=True)

        for row in history:
            tree.insert("", "end", values=row)
    

# ========================= RUN ==========================
if __name__ == "__main__":
    root = tk.Tk()
    app = StudyPlannerApp(root)
    root.mainloop()
