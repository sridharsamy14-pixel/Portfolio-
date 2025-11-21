import json
import os
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import calendar
from tkcalendar import Calendar  # We'll use this for calendar functionality

class TodoList:
    def __init__(self, filename="todos.json"):
        self.filename = filename
        self.todos = self.load_todos()
    
    def load_todos(self):
        """Load todos from JSON file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def save_todos(self):
        """Save todos to JSON file"""
        with open(self.filename, 'w') as f:
            json.dump(self.todos, f, indent=4)
    
    def add_todo(self, title, description="", priority="Medium", due_date=None, reminder=None):
        """Add a new todo item"""
        todo = {
            "id": len(self.todos) + 1,
            "title": title,
            "description": description,
            "priority": priority,
            "due_date": due_date.strftime("%Y-%m-%d") if due_date else None,
            "reminder": reminder.strftime("%Y-%m-%d %H:%M") if reminder else None,
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "completed_at": None
        }
        self.todos.append(todo)
        self.save_todos()
        return todo
    
    def get_todos(self, completed=None, priority=None):
        """Get todos with optional filters"""
        filtered_todos = self.todos
        
        if completed is not None:
            filtered_todos = [todo for todo in filtered_todos if todo["completed"] == completed]
            
        if priority is not None and priority != "All":
            filtered_todos = [todo for todo in filtered_todos if todo["priority"] == priority]
            
        return filtered_todos
    
    def get_upcoming_todos(self, days=7):
        """Get todos with due dates in the next specified days"""
        today = date.today()
        future_date = today + timedelta(days=days)
        
        upcoming = []
        for todo in self.todos:
            if todo["due_date"] and not todo["completed"]:
                due_date = datetime.strptime(todo["due_date"], "%Y-%m-%d").date()
                if today <= due_date <= future_date:
                    upcoming.append(todo)
        
        return sorted(upcoming, key=lambda x: x["due_date"])
    
    def get_todos_by_date(self, target_date):
        """Get todos for a specific date"""
        target_date_str = target_date.strftime("%Y-%m-%d")
        return [todo for todo in self.todos if todo["due_date"] == target_date_str]
    
    def check_reminders(self):
        """Check for reminders that need to be shown"""
        now = datetime.now()
        reminders = []
        
        for todo in self.todos:
            if todo["reminder"] and not todo["completed"]:
                reminder_time = datetime.strptime(todo["reminder"], "%Y-%m-%d %H:%M")
                if reminder_time <= now:
                    reminders.append(todo)
        
        return reminders
    
    def update_todo(self, todo_id, **kwargs):
        """Update a todo item"""
        for todo in self.todos:
            if todo["id"] == todo_id:
                for key, value in kwargs.items():
                    if key in todo and value is not None:
                        if key in ["due_date", "reminder"] and value:
                            if key == "due_date":
                                todo[key] = value.strftime("%Y-%m-%d")
                            else:
                                todo[key] = value.strftime("%Y-%m-%d %H:%M")
                        else:
                            todo[key] = value
                self.save_todos()
                return True
        return False
    
    def delete_todo(self, todo_id):
        """Delete a todo item"""
        for i, todo in enumerate(self.todos):
            if todo["id"] == todo_id:
                del self.todos[i]
                self.save_todos()
                return True
        return False
    
    def get_stats(self):
        """Get statistics about todos"""
        total = len(self.todos)
        completed = len([todo for todo in self.todos if todo["completed"]])
        pending = total - completed
        
        # Count by priority
        high_priority = len([todo for todo in self.todos if todo["priority"] == "High"])
        medium_priority = len([todo for todo in self.todos if todo["priority"] == "Medium"])
        low_priority = len([todo for todo in self.todos if todo["priority"] == "Low"])
        
        # Count overdue tasks
        today = date.today()
        overdue = 0
        for todo in self.todos:
            if todo["due_date"] and not todo["completed"]:
                due_date = datetime.strptime(todo["due_date"], "%Y-%m-%d").date()
                if due_date < today:
                    overdue += 1
        
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority,
            "overdue": overdue
        }

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python To-Do List with Calendar")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f5f5f5")
        
        # Initialize todo list
        self.todo_list = TodoList()
        
        # Setup UI
        self.setup_ui()
        
        # Load initial data
        self.refresh_list()
        
        # Check for reminders
        self.check_reminders()
        
        # Schedule reminder checks every minute
        self.root.after(60000, self.check_reminders_periodically)
    
    def setup_ui(self):
        # Configure style
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Arial", 16, "bold"), background="#4CAF50", foreground="white")
        style.configure("Filter.TButton", font=("Arial", 10))
        style.configure("Action.TButton", font=("Arial", 10))
        
        # Create main panels
        main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for todo list
        left_frame = ttk.Frame(main_panel)
        main_panel.add(left_frame, weight=2)
        
        # Right panel for calendar
        right_frame = ttk.Frame(main_panel)
        main_panel.add(right_frame, weight=1)
        
        # Header frame
        header_frame = ttk.Frame(left_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(header_frame, text="Python To-Do List", style="Header.TLabel")
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Add task button
        add_button = ttk.Button(header_frame, text="+ Add Task", command=self.add_todo)
        add_button.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Filter frame
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Filter by:").pack(side=tk.LEFT, padx=5)
        
        # Status filter
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var, 
                                   values=["All", "Active", "Completed"], width=10)
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Priority filter
        self.priority_var = tk.StringVar(value="All")
        priority_combo = ttk.Combobox(filter_frame, textvariable=self.priority_var, 
                                     values=["All", "High", "Medium", "Low"], width=10)
        priority_combo.pack(side=tk.LEFT, padx=5)
        priority_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Date filter
        ttk.Button(filter_frame, text="Today's Tasks", command=self.show_todays_tasks).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Upcoming Week", command=self.show_upcoming_week).pack(side=tk.LEFT, padx=5)
        
        # Search box
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", self.on_search_changed)
        
        # Treeview for todos
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview with scrollbar
        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Title", "Priority", "Due Date", "Status", "Created"), show="headings")
        
        # Define headings
        self.tree.heading("ID", text="ID")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Priority", text="Priority")
        self.tree.heading("Due Date", text="Due Date")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Created", text="Created")
        
        # Define columns
        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("Title", width=200, anchor=tk.W)
        self.tree.column("Priority", width=80, anchor=tk.CENTER)
        self.tree.column("Due Date", width=100, anchor=tk.CENTER)
        self.tree.column("Status", width=80, anchor=tk.CENTER)
        self.tree.column("Created", width=120, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double click event
        self.tree.bind("<Double-1>", self.on_item_double_click)
        
        # Action buttons frame
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Mark Complete/Incomplete", command=self.toggle_complete).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit", command=self.edit_todo).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=self.delete_todo).pack(side=tk.LEFT, padx=5)
        
        # Calendar frame
        calendar_frame = ttk.LabelFrame(right_frame, text="Calendar")
        calendar_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create calendar
        self.cal = Calendar(calendar_frame, selectmode='day', 
                           year=datetime.now().year, 
                           month=datetime.now().month, 
                           day=datetime.now().day)
        self.cal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.cal.bind("<<CalendarSelected>>", self.on_calendar_select)
        
        # Calendar controls
        cal_control_frame = ttk.Frame(right_frame)
        cal_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(cal_control_frame, text="View Selected Date", command=self.view_selected_date).pack(side=tk.LEFT, padx=5)
        ttk.Button(cal_control_frame, text="Today", command=self.show_today).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Stats frame
        stats_frame = ttk.Frame(self.root)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_var = tk.StringVar()
        stats_label = ttk.Label(stats_frame, textvariable=self.stats_var)
        stats_label.pack(side=tk.LEFT)
    
    def refresh_list(self):
        """Refresh the todo list display"""
        # Clear current items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get filter values
        status_filter = self.status_var.get()
        priority_filter = self.priority_var.get()
        search_text = self.search_var.get().lower()
        
        # Convert status filter
        completed_filter = None
        if status_filter == "Active":
            completed_filter = False
        elif status_filter == "Completed":
            completed_filter = True
        
        # Get filtered todos
        todos = self.todo_list.get_todos(completed_filter)
        
        # Apply priority filter
        if priority_filter != "All":
            todos = [todo for todo in todos if todo["priority"] == priority_filter]
        
        # Apply search filter
        if search_text:
            todos = [todo for todo in todos if search_text in todo["title"].lower() or 
                     (todo["description"] and search_text in todo["description"].lower())]
        
        # Add todos to treeview
        for todo in todos:
            status = "Completed" if todo["completed"] else "Active"
            due_date = todo["due_date"] if todo["due_date"] else "No due date"
            
            item_id = self.tree.insert("", "end", values=(
                todo["id"],
                todo["title"],
                todo["priority"],
                due_date,
                status,
                todo["created_at"]
            ))
            
            # Color code based on priority and overdue status
            if todo["priority"] == "High":
                self.tree.set(item_id, "Priority", "High")
            
            # Mark overdue tasks
            if todo["due_date"] and not todo["completed"]:
                due = datetime.strptime(todo["due_date"], "%Y-%m-%d").date()
                if due < date.today():
                    self.tree.set(item_id, "Due Date", f"OVERDUE: {due_date}")
        
        # Update status
        stats = self.todo_list.get_stats()
        self.status_var.set(f"Total tasks: {stats['total']} | Completed: {stats['completed']} | Pending: {stats['pending']} | Overdue: {stats['overdue']}")
        self.stats_var.set(f"High: {stats['high_priority']} | Medium: {stats['medium_priority']} | Low: {stats['low_priority']}")
        
        # Update calendar with task dates
        self.update_calendar()
    
    def update_calendar(self):
        """Update calendar to highlight dates with tasks"""
        # Get all due dates
        due_dates = {}
        for todo in self.todo_list.todos:
            if todo["due_date"]:
                if todo["due_date"] in due_dates:
                    due_dates[todo["due_date"]] += 1
                else:
                    due_dates[todo["due_date"]] = 1
        
        # Highlight dates with tasks
        for date_str, count in due_dates.items():
            year, month, day = map(int, date_str.split('-'))
            self.cal.calevent_create(date(year, month, day), f"{count} task(s)", "task")
        
        # Configure calendar tags
        self.cal.tag_config("task", background="lightblue", foreground="black")
    
    def on_filter_changed(self, event):
        """Handle filter changes"""
        self.refresh_list()
    
    def on_search_changed(self, event):
        """Handle search changes"""
        self.refresh_list()
    
    def on_calendar_select(self, event):
        """Handle calendar selection"""
        selected_date = self.cal.selection_get()
        self.view_tasks_for_date(selected_date)
    
    def view_tasks_for_date(self, target_date):
        """View tasks for a specific date"""
        tasks = self.todo_list.get_todos_by_date(target_date)
        
        if not tasks:
            messagebox.showinfo("Tasks", f"No tasks found for {target_date.strftime('%Y-%m-%d')}")
            return
        
        task_list = f"Tasks for {target_date.strftime('%Y-%m-%d')}:\n\n"
        for i, task in enumerate(tasks, 1):
            status = "✓" if task["completed"] else "◯"
            task_list += f"{i}. {status} {task['title']} ({task['priority']})\n"
        
        messagebox.showinfo("Tasks", task_list)
    
    def view_selected_date(self):
        """View tasks for the selected calendar date"""
        selected_date = self.cal.selection_get()
        self.view_tasks_for_date(selected_date)
    
    def show_today(self):
        """Show today's date in calendar"""
        today = date.today()
        self.cal.selection_set(today)
        self.view_tasks_for_date(today)
    
    def show_todays_tasks(self):
        """Show today's tasks"""
        today = date.today()
        self.view_tasks_for_date(today)
    
    def show_upcoming_week(self):
        """Show upcoming tasks for the next week"""
        upcoming = self.todo_list.get_upcoming_todos(7)
        
        if not upcoming:
            messagebox.showinfo("Upcoming Tasks", "No upcoming tasks for the next week")
            return
        
        task_list = "Upcoming tasks for the next week:\n\n"
        for i, task in enumerate(upcoming, 1):
            status = "✓" if task["completed"] else "◯"
            task_list += f"{i}. {status} {task['title']} - Due: {task['due_date']} ({task['priority']})\n"
        
        messagebox.showinfo("Upcoming Tasks", task_list)
    
    def get_selected_todo(self):
        """Get the currently selected todo"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task first")
            return None
        
        item = self.tree.item(selection[0])
        todo_id = item["values"][0]
        
        for todo in self.todo_list.todos:
            if todo["id"] == todo_id:
                return todo
        
        return None
    
    def on_item_double_click(self, event):
        """Handle double click on todo item"""
        self.edit_todo()
    
    def add_todo(self):
        """Add a new todo"""
        dialog = TodoDialog(self.root, "Add New Task")
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            title, description, priority, due_date, reminder = dialog.result
            self.todo_list.add_todo(title, description, priority, due_date, reminder)
            self.refresh_list()
    
    def edit_todo(self):
        """Edit selected todo"""
        todo = self.get_selected_todo()
        if not todo:
            return
        
        # Convert string dates back to datetime objects for editing
        due_date = None
        if todo["due_date"]:
            due_date = datetime.strptime(todo["due_date"], "%Y-%m-%d").date()
        
        reminder = None
        if todo["reminder"]:
            reminder = datetime.strptime(todo["reminder"], "%Y-%m-%d %H:%M")
        
        dialog = TodoDialog(
            self.root, 
            "Edit Task", 
            title=todo["title"],
            description=todo["description"],
            priority=todo["priority"],
            due_date=due_date,
            reminder=reminder
        )
        
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            title, description, priority, due_date, reminder = dialog.result
            self.todo_list.update_todo(
                todo["id"],
                title=title,
                description=description,
                priority=priority,
                due_date=due_date,
                reminder=reminder
            )
            self.refresh_list()
    
    def toggle_complete(self):
        """Toggle complete status of selected todo"""
        todo = self.get_selected_todo()
        if not todo:
            return
        
        completed = not todo["completed"]
        completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if completed else None
        
        self.todo_list.update_todo(
            todo["id"],
            completed=completed,
            completed_at=completed_at
        )
        self.refresh_list()
    
    def delete_todo(self):
        """Delete selected todo"""
        todo = self.get_selected_todo()
        if not todo:
            return
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{todo['title']}'?"):
            self.todo_list.delete_todo(todo["id"])
            self.refresh_list()
    
    def check_reminders(self):
        """Check for reminders and show notifications"""
        reminders = self.todo_list.check_reminders()
        
        for todo in reminders:
            messagebox.showinfo("Reminder", f"Reminder for: {todo['title']}\n\n{todo['description']}")
    
    def check_reminders_periodically(self):
        """Check for reminders periodically"""
        self.check_reminders()
        # Schedule next check in 1 minute
        self.root.after(60000, self.check_reminders_periodically)

class TodoDialog:
    def __init__(self, parent, title, title_text="", description="", priority="Medium", due_date=None, reminder=None):
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.geometry("500x600")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.result = None
        
        # Title
        ttk.Label(self.top, text="Title:").pack(padx=10, pady=(10, 0), anchor=tk.W)
        self.title_var = tk.StringVar(value=title_text)
        title_entry = ttk.Entry(self.top, textvariable=self.title_var, width=50)
        title_entry.pack(padx=10, pady=(0, 10), fill=tk.X)
        
        # Description
        ttk.Label(self.top, text="Description:").pack(padx=10, pady=(10, 0), anchor=tk.W)
        self.desc_text = tk.Text(self.top, height=5, width=50)
        self.desc_text.pack(padx=10, pady=(0, 10), fill=tk.X)
        self.desc_text.insert("1.0", description)
        
        # Priority
        ttk.Label(self.top, text="Priority:").pack(padx=10, pady=(10, 0), anchor=tk.W)
        self.priority_var = tk.StringVar(value=priority)
        priority_combo = ttk.Combobox(self.top, textvariable=self.priority_var, 
                                     values=["High", "Medium", "Low"])
        priority_combo.pack(padx=10, pady=(0, 10), anchor=tk.W)
        
        # Due Date
        ttk.Label(self.top, text="Due Date:").pack(padx=10, pady=(10, 0), anchor=tk.W)
        
        date_frame = ttk.Frame(self.top)
        date_frame.pack(padx=10, pady=(0, 10), fill=tk.X)
        
        self.due_date_var = tk.StringVar()
        self.due_date_entry = ttk.Entry(date_frame, textvariable=self.due_date_var, width=15)
        self.due_date_entry.pack(side=tk.LEFT)
        
        if due_date:
            self.due_date_var.set(due_date.strftime("%Y-%m-%d"))
        
        ttk.Button(date_frame, text="Select Date", command=self.select_date).pack(side=tk.LEFT, padx=5)
        ttk.Button(date_frame, text="Clear", command=self.clear_date).pack(side=tk.LEFT, padx=5)
        
        # Reminder
        ttk.Label(self.top, text="Set Reminder:").pack(padx=10, pady=(10, 0), anchor=tk.W)
        
        reminder_frame = ttk.Frame(self.top)
        reminder_frame.pack(padx=10, pady=(0, 10), fill=tk.X)
        
        # Date selection for reminder
        ttk.Label(reminder_frame, text="Date:").grid(row=0, column=0, sticky=tk.W)
        self.reminder_date_var = tk.StringVar()
        self.reminder_date_entry = ttk.Entry(reminder_frame, textvariable=self.reminder_date_var, width=12)
        self.reminder_date_entry.grid(row=0, column=1, padx=5)
        
        if reminder:
            self.reminder_date_var.set(reminder.strftime("%Y-%m-%d"))
        
        ttk.Button(reminder_frame, text="Select", command=self.select_reminder_date).grid(row=0, column=2, padx=5)
        
        # Time selection for reminder
        time_frame = ttk.Frame(reminder_frame)
        time_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Label(time_frame, text="Time:").pack(side=tk.LEFT)
        
        # Hour selection
        self.hour_var = tk.StringVar(value="12")
        hour_combo = ttk.Combobox(time_frame, textvariable=self.hour_var, width=3, 
                                 values=[f"{i:02d}" for i in range(1, 13)])
        hour_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        
        # Minute selection
        self.minute_var = tk.StringVar(value="00")
        minute_combo = ttk.Combobox(time_frame, textvariable=self.minute_var, width=3,
                                   values=[f"{i:02d}" for i in range(0, 60, 5)])
        minute_combo.pack(side=tk.LEFT, padx=5)
        
        # AM/PM selection
        self.ampm_var = tk.StringVar(value="AM")
        ampm_combo = ttk.Combobox(time_frame, textvariable=self.ampm_var, width=3,
                                 values=["AM", "PM"])
        ampm_combo.pack(side=tk.LEFT, padx=5)
        
        # Set initial values if editing existing reminder
        if reminder:
            self.hour_var.set(reminder.strftime("%I"))
            self.minute_var.set(reminder.strftime("%M"))
            self.ampm_var.set(reminder.strftime("%p"))
        
        ttk.Button(reminder_frame, text="Clear Reminder", command=self.clear_reminder).grid(row=2, column=0, columnspan=3, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.top)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=10)
    
    def select_date(self):
        """Open calendar to select due date"""
        date_dialog = DateDialog(self.top, "Select Due Date")
        self.top.wait_window(date_dialog.top)
        
        if date_dialog.selected_date:
            self.due_date_var.set(date_dialog.selected_date.strftime("%Y-%m-%d"))
    
    def select_reminder_date(self):
        """Open calendar to select reminder date"""
        date_dialog = DateDialog(self.top, "Select Reminder Date")
        self.top.wait_window(date_dialog.top)
        
        if date_dialog.selected_date:
            self.reminder_date_var.set(date_dialog.selected_date.strftime("%Y-%m-%d"))
    
    def clear_date(self):
        """Clear the due date"""
        self.due_date_var.set("")
    
    def clear_reminder(self):
        """Clear the reminder"""
        self.reminder_date_var.set("")
        self.hour_var.set("12")
        self.minute_var.set("00")
        self.ampm_var.set("AM")
    
    def ok(self):
        """Handle OK button"""
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("Warning", "Title is required")
            return
        
        description = self.desc_text.get("1.0", tk.END).strip()
        priority = self.priority_var.get()
        
        # Parse due date
        due_date_str = self.due_date_var.get().strip()
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showwarning("Warning", "Invalid due date format. Use YYYY-MM-DD")
                return
        
        # Parse reminder
        reminder_date_str = self.reminder_date_var.get().strip()
        reminder = None
        if reminder_date_str:
            try:
                # Convert 12-hour time to 24-hour time
                hour = int(self.hour_var.get())
                if self.ampm_var.get() == "PM" and hour < 12:
                    hour += 12
                elif self.ampm_var.get() == "AM" and hour == 12:
                    hour = 0
                
                minute = int(self.minute_var.get())
                
                reminder = datetime.strptime(reminder_date_str, "%Y-%m-%d").replace(
                    hour=hour, minute=minute
                )
                
                # Check if reminder is in the past
                if reminder < datetime.now():
                    messagebox.showwarning("Warning", "Reminder must be in the future")
                    return
                    
            except ValueError:
                messagebox.showwarning("Warning", "Invalid reminder date or time")
                return
        
        self.result = (title, description, priority, due_date, reminder)
        self.top.destroy()
    
    def cancel(self):
        """Handle Cancel button"""
        self.top.destroy()

class DateDialog:
    def __init__(self, parent, title):
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.transient(parent)
        self.top.grab_set()
        
        self.selected_date = None
        
        # Create calendar
        self.cal = Calendar(self.top, selectmode='day', 
                           year=datetime.now().year, 
                           month=datetime.now().month, 
                           day=datetime.now().day)
        self.cal.pack(padx=10, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(self.top)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=10)
    
    def ok(self):
        """Handle OK button"""
        self.selected_date = self.cal.selection_get()
        self.top.destroy()
    
    def cancel(self):
        """Handle Cancel button"""
        self.top.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()