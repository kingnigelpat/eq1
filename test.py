# Task Manager in Python

# Initialize an empty list to store tasks
tasks = []

# Function to display the menu
def display_menu():
    print("\n--- Task Manager ---")
    print("1. Add Task")
    print("2. View Tasks")
    print("3. Mark Task as Complete")
    print("4. Delete Task")
    print("5. Exit")

# Function to add a task (CREATE)
def add_task():
    task = input("Enter the task: ")
    tasks.append({"text": task, "completed": False})
    print(f"Task '{task}' added!")

# Function to view all tasks (READ)
def view_tasks():
    if not tasks:
        print("No tasks yet!")
    else:
        print("\n--- Your Tasks ---")
        for i, task in enumerate(tasks, start=1):
            status = "✓" if task["completed"] else "✗"
            print(f"{i}. [{status}] {task['text']}")

# Function to mark a task as complete (UPDATE)
def mark_complete():
    view_tasks()
    if tasks:
        try:
            task_num = int(input("Enter the task number to mark as complete: ")) - 1
            if 0 <= task_num < len(tasks):
                tasks[task_num]["completed"] = True
                print(f"Task '{tasks[task_num]['text']}' marked as complete!")
            else:
                print("Invalid task number!")
        except ValueError:
            print("Please enter a valid number!")

# Function to delete a task (DELETE)
def delete_task():
    view_tasks()
    if tasks:
        try:
            task_num = int(input("Enter the task number to delete: ")) - 1
            if 0 <= task_num < len(tasks):
                deleted_task = tasks.pop(task_num)
                print(f"Task '{deleted_task['text']}' deleted!")
            else:
                print("Invalid task number!")
        except ValueError:
            print("Please enter a valid number!")

# Main loop to run the task manager
while True:
    display_menu()
    choice = input("Enter your choice (1-5): ")

    if choice == "1":
        add_task()
    elif choice == "2":
        view_tasks()
    elif choice == "3":
        mark_complete()
    elif choice == "4":
        delete_task()
    elif choice == "5":
        print("Goodbye!")
        break
    else:
        print("Invalid choice. Please try again.")
