import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import paramiko
import threading
import yaml
from PIL import Image, ImageTk  # Make sure to install Pillow

# Default values
DEFAULT_IP = "10.100.0.187"
DEFAULT_USER = "mcarr"
DEFAULT_PASSWORD = "12345"
TIMEOUT = 10  # Timeout for SSH connection in seconds

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Configuration App")
        self.root.geometry("800x800+100+100")  # Set size and position

        # Ensure the window is focused
        self.root.deiconify()  # Make sure the window is shown
        self.root.focus_force()  # Bring the window to the front

        # Load the image
        self.image = Image.open("images/openipc.png")
        self.photo = ImageTk.PhotoImage(self.image)
        # Create a label to display the image
        self.image_label = tk.Label(self.root, image=self.photo)
        self.image_label.pack()

        self.ip = tk.StringVar(value=DEFAULT_IP)
        self.username = tk.StringVar(value=DEFAULT_USER)
        self.password = tk.StringVar(value=DEFAULT_PASSWORD)
        self.timeout = tk.IntVar(value=TIMEOUT)

        self.create_widgets()

    def create_widgets(self):
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Create tabs
        self.wfb_conf_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.wfb_conf_frame, text="wfb.conf")

        self.majestic_yaml_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.majestic_yaml_frame, text="majestic.yaml")

        self.gs_conf_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.gs_conf_frame, text="gs.conf")

        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="Application Logs")

        # Create scrollable frame for wfb.conf
        self.create_scrollable_frame(self.wfb_conf_frame, "wfb")

        # Create scrollable frame for majestic.yaml
        self.create_scrollable_frame(self.majestic_yaml_frame, "majestic")

        # Create scrollable frame for gs.conf
        self.gs_conf_canvas = tk.Canvas(self.gs_conf_frame)
        self.gs_conf_scrollbar = ttk.Scrollbar(self.gs_conf_frame, orient="vertical", command=self.gs_conf_canvas.yview)
        self.gs_conf_scrollable_frame = ttk.Frame(self.gs_conf_canvas)

        self.gs_conf_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.gs_conf_canvas.configure(
                scrollregion=self.gs_conf_canvas.bbox("all")
            )
        )

        self.gs_conf_canvas.create_window((0, 0), window=self.gs_conf_scrollable_frame, anchor="nw")
        self.gs_conf_scrollbar.config(command=self.gs_conf_canvas.yview)

        self.gs_conf_canvas.pack(side="left", fill="both", expand=True)
        self.gs_conf_scrollbar.pack(side="right", fill="y")

        # Create logs area
        self.logs_text = scrolledtext.ScrolledText(self.logs_frame, wrap="word", height=20)
        self.logs_text.pack(fill="both", expand=True)

        # Add Save Log button to logs tab
        self.save_log_button = ttk.Button(self.logs_frame, text="Save Log", command=self.save_log)
        self.save_log_button.pack(pady=10)

        # Add connection form
        self.connection_frame = ttk.Frame(self.root)
        self.connection_frame.pack(pady=10)

        self.create_connection_form(self.connection_frame)

    def create_scrollable_frame(self, frame, type_):
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollbar.config(command=canvas.yview)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if type_ == "wfb":
            self.wfb_conf_canvas = canvas
            self.wfb_conf_scrollable_frame = scrollable_frame
        elif type_ == "majestic":
            self.majestic_yaml_canvas = canvas
            self.majestic_yaml_scrollable_frame = scrollable_frame

    def create_connection_form(self, parent):
        # IP Address
        ttk.Label(parent, text="IP Address:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.ip_entry = ttk.Entry(parent, textvariable=self.ip)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Username
        ttk.Label(parent, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.username_entry = ttk.Entry(parent, textvariable=self.username)
        self.username_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Password
        ttk.Label(parent, text="Password:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.password_entry = ttk.Entry(parent, textvariable=self.password, show="*")
        self.password_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Timeout
        ttk.Label(parent, text="Timeout (s):").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.timeout_entry = ttk.Entry(parent, textvariable=self.timeout)
        self.timeout_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Connect Button
        self.connect_button = ttk.Button(parent, text="Connect", command=self.connect)
        self.connect_button.grid(row=4, column=0, columnspan=2, pady=10)

    def connect(self):
        # Disable connect button
        self.connect_button.config(state="disabled")

        # Start SSH connection in a separate thread
        self.ssh_thread = threading.Thread(target=self.ssh_connect)
        self.ssh_thread.start()

    def ssh_connect(self):
        try:
            ip = self.ip.get()
            user = self.username.get()
            password = self.password.get()
            timeout = self.timeout.get()

            self.append_log(f"Connecting to {ip} as {user}")

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect with timeout
            ssh.connect(ip, username=user, password=password, timeout=timeout)

            # Run commands and read files
            stdin, stdout, stderr = ssh.exec_command("cat /etc/wfb.conf")
            wfb_conf_output = stdout.read().decode()
            self.append_log("Output of /etc/wfb.conf:\n" + wfb_conf_output)
            self.update_wfb_conf_tab(wfb_conf_output)

            stdin, stdout, stderr = ssh.exec_command("cat /etc/majestic.yaml")
            majestic_yaml_output = stdout.read().decode()
            self.append_log("Output of /etc/majestic.yaml:\n" + majestic_yaml_output)
            self.update_majestic_yaml_tab(majestic_yaml_output)

            stdin, stdout, stderr = ssh.exec_command("cat /etc/gs.conf")
            gs_conf_output = stdout.read().decode()
            self.append_log("Output of /etc/gs.conf:\n" + gs_conf_output)
            self.update_gs_conf_tab(gs_conf_output)

            # Close connection
            ssh.close()
        except Exception as e:
            self.append_log(f"Error: {str(e)}")

        # Re-enable connect button
        self.connect_button.config(state="normal")

    def update_wfb_conf_tab(self, content):
        # Clear existing widgets
        for widget in self.wfb_conf_scrollable_frame.winfo_children():
            widget.destroy()

        # Parse and display the content
        lines = content.splitlines()
        row_number = 0
        for line in lines:
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Create new entry for each key-value pair
                ttk.Label(self.wfb_conf_scrollable_frame, text=key).grid(row=row_number, column=0, padx=5, pady=2, sticky="e")
                entry = tk.Entry(self.wfb_conf_scrollable_frame, width=40)
                entry.grid(row=row_number, column=1, padx=5, pady=2, sticky="w")
                entry.insert(0, value)
                row_number += 1

        # Update the scroll region of the canvas
        self.wfb_conf_canvas.update_idletasks()
        self.wfb_conf_canvas.config(scrollregion=self.wfb_conf_canvas.bbox("all"))

     # Update the majestic_yaml_tab method to ensure the scrollable frame is populated
    def update_majestic_yaml_tab(self, yaml_content):
        if yaml_content:
            try:
                data = yaml.safe_load(yaml_content)
                if data:
                    # Clear the previous widgets in the tab
                    for widget in self.majestic_yaml_frame.winfo_children():
                        widget.destroy()

                    # Create a canvas and add a scrollbar for the frame
                    canvas = tk.Canvas(self.majestic_yaml_frame)
                    scrollbar = tk.Scrollbar(self.majestic_yaml_frame, orient="vertical", command=canvas.yview)
                    scrollable_frame = tk.Frame(canvas)

                    scrollable_frame.bind(
                        "<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                    )

                    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                    canvas.configure(yscrollcommand=scrollbar.set)

                    # Use grid to place the canvas and scrollbar
                    canvas.pack(side="left", fill="both", expand=True)
                    scrollbar.pack(side="right", fill="y")

                    # Create a vertical form layout for YAML content in the scrollable frame
                    row = 0
                    for key, value in data.items():
                        if isinstance(value, dict):
                            label = tk.Label(scrollable_frame, text=f"{key}:")
                            label.grid(row=row, column=0, sticky='w')
                            row += 1

                            for sub_key, sub_value in value.items():
                                sub_label = tk.Label(scrollable_frame, text=f"  {sub_key}:")
                                sub_label.grid(row=row, column=0, sticky='w')

                                text_box = tk.Entry(scrollable_frame, width=70)  # Wider text box
                                text_box.grid(row=row, column=1, sticky='w')
                                text_box.insert(0, str(sub_value))

                                row += 1
                        else:
                            label = tk.Label(scrollable_frame, text=f"{key}:")
                            label.grid(row=row, column=0, sticky='w')

                            text_box = tk.Entry(scrollable_frame, width=70)  # Wider text box
                            text_box.grid(row=row, column=1, sticky='w')
                            text_box.insert(0, str(value))

                            row += 1
                    # Add Save button here
                    self.save_button = ttk.Button(self.majestic_yaml_frame, text="Save", command=self.save_majestic_yaml)
                    self.save_button.pack(pady=10)
                else:
                    print("No data found in YAML content.")
            except yaml.YAMLError as e:
                print(f"Error parsing YAML: {e}")
        else:
            print("YAML content is empty or None.")


    def update_gs_conf_tab(self, content):
        # Clear existing widgets
        for widget in self.gs_conf_scrollable_frame.winfo_children():
            widget.destroy()

        # Parse and display the content
        lines = content.splitlines()
        row_number = 0
        for line in lines:
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Create new entry for each key-value pair
                ttk.Label(self.gs_conf_scrollable_frame, text=key).grid(row=row_number, column=0, padx=5, pady=5, sticky="e")
                entry = tk.Entry(self.gs_conf_scrollable_frame, width=60)  # Adjust width for better visibility
                entry.grid(row=row_number, column=1, padx=5, pady=5, sticky="w")
                entry.insert(0, value)
                row_number += 1

        # Add a Save button for this tab if needed
        self.save_button_gs = ttk.Button(self.gs_conf_scrollable_frame, text="Save", command=self.save_gs_conf)
        self.save_button_gs.grid(row=row_number, column=0, columnspan=2, pady=10)

        # Update the scroll region of the canvas
        self.gs_conf_canvas.update_idletasks()
        self.gs_conf_canvas.config(scrollregion=self.gs_conf_canvas.bbox("all"))


    def append_log(self, message):
        self.logs_text.insert(tk.END, message + "\n")
        self.logs_text.yview(tk.END)  # Auto-scroll to the end

    def save_majestic_yaml(self):
        updated_data = {}
        for widget in self.majestic_yaml_frame.winfo_children():
            if isinstance(widget, tk.Label):
                key = widget.cget("text")[:-1]  # Get the key name from label
            elif isinstance(widget, tk.Entry):
                value = widget.get()  # Get the value from entry
                updated_data[key] = value
        
        # Convert updated_data back to YAML and save it
        try:
            with open('/path/to/majestic.yaml', 'w') as yaml_file:
                yaml.dump(updated_data, yaml_file)
            print("Changes saved successfully.")
        except Exception as e:
            print(f"Error saving YAML: {e}")

    def save_log(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write(self.logs_text.get("1.0", tk.END))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
