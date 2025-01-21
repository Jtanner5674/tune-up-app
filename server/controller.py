import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
import uuid
import pyperclip  # For clipboard functionality
from datetime import datetime

# Database connection
def connect_to_db():
    """ Connect to the MariaDB database using connection parameters. """
    conn = pymysql.connect(
        database='licenses',
        user='root',
        password='NTi',
        host='192.168.4.114',
        port=3306
    )
    return conn

def create_license(conn, user_id):
    activation_key = str(uuid.uuid4())
    default_hash = "default_hash_value"
    
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO licenses (id, activation_key, hash, activated_on)
            VALUES (%s, %s, %s, %s)
        """, (user_id, activation_key, default_hash, None))  # Pass None for NULL
    conn.commit()

    return activation_key

# Function to remove a license
def remove_entry(conn, entry_id):
    """ Remove a license by ID """
    with conn.cursor() as cur:
        cur.execute("DELETE FROM licenses WHERE id = %s", (entry_id,))
    conn.commit()

# Function to list all licenses
def list_entries(conn):
    """ List all licenses in the database. """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT * FROM licenses")
        entries = cur.fetchall()
    return entries

# Create the Tkinter GUI for managing licenses
def license_manager():
    # Create main window
    root = tk.Tk()
    root.title("License Manager")

    # Setup database connection
    conn = connect_to_db()

    def create_license_handler():
        """ Handle license creation. """
        user_id = user_id_entry.get()
        if user_id:
            activation_key = create_license(conn, user_id)
            pyperclip.copy(activation_key)  # Copy the activation key to the clipboard
            messagebox.showinfo("License Created", f"License created for {user_id}. Activation Key: {activation_key} (Copied to clipboard)")
            refresh_license_list()  # Refresh the list after creation
        else:
            messagebox.showerror("Error", "User ID is required")

    def remove_license_handler():
        """ Handle license removal via User ID. """
        selected_item = license_tree.selection()  # Get selected row
        if selected_item:
            entry_id = license_tree.item(selected_item)["values"][0]  # Get the ID from the selected row
            remove_entry(conn, entry_id)
            messagebox.showinfo("License Removed", f"License with ID {entry_id} removed.")
            refresh_license_list()  # Refresh the list after removal
        else:
            messagebox.showerror("Error", "Please select a license to remove.")

    def refresh_license_list():
        """ Refresh the list of licenses in the tree view. """
        for row in license_tree.get_children():
            license_tree.delete(row)
        entries = list_entries(conn)
        for entry in entries:
            license_tree.insert("", "end", values=(entry['id'], entry['activation_key'], entry['activated_on']))


    def copy_license_to_clipboard():
        """ Copy the selected license's activation key to the clipboard. """
        selected_item = license_tree.selection()
        if selected_item:
            activation_key = license_tree.item(selected_item)["values"][1]  # Get activation key from selected row
            pyperclip.copy(activation_key)  # Copy it to clipboard
            messagebox.showinfo("License Copied", f"License Activation Key copied to clipboard: {activation_key}")
        else:
            messagebox.showerror("Error", "Please select a license to copy.")

    # Right-click menu for deleting a license
    def show_context_menu(event):
        """ Show the context menu when right-clicking on a row in the treeview. """
        item = license_tree.identify_row(event.y)
        if item:
            license_tree.selection_set(item)  # Select the clicked item
            context_menu.post(event.x_root, event.y_root)  # Show the context menu

    def delete_selected():
        """ Delete the selected license from the context menu. """
        remove_license_handler()

    # Create UI components
    ttk.Label(root, text="Enter User Name:").grid(row=0, column=0, padx=10, pady=10)
    user_id_entry = ttk.Entry(root, width=40)
    user_id_entry.grid(row=0, column=1, padx=10, pady=10)
    create_button = ttk.Button(root, text="Create License", command=create_license_handler)
    create_button.grid(row=0, column=2, padx=10, pady=10)

    # License List Section
    license_tree = ttk.Treeview(root, columns=("ID", "Activation Key", "Activated On"), show="headings", height=10)
    license_tree.heading("ID", text="User ID")
    license_tree.heading("Activation Key", text="Activation Key")
    license_tree.heading("Activated On", text="Activated On")
    license_tree.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

    # Right-click context menu
    context_menu = tk.Menu(root, tearoff=0)
    context_menu.add_command(label="Delete License", command=delete_selected)
    context_menu.add_command(label="Copy License", command=copy_license_to_clipboard)

    # Bind right-click to show the context menu
    license_tree.bind("<Button-3>", show_context_menu)

    # Refresh license list on startup
    refresh_license_list()

    # Start the Tkinter main loop
    root.mainloop()

if __name__ == "__main__":
    license_manager()
