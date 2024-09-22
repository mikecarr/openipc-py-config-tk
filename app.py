import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import paramiko
import threading
import yaml

# Default values
DEFAULT_IP = "10.100.0.187"
DEFAULT_USER = "mcarr"
DEFAULT_PASSWORD = "12345"
TIMEOUT = 10  # Timeout for SSH connection in seconds

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Configuration App")
        self.root.geometry("800x600")

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
        print("Majestic tab created")  # Debug message

        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="Application Logs")


        # Create scrollable frame for wfb.conf
        self.wfb_conf_canvas = tk.Canvas(self.wfb_conf_frame)
        self.wfb_conf_scrollbar = ttk.Scrollbar(self.wfb_conf_frame, orient="vertical", command=self.wfb_conf_canvas.yview)
        self.wfb_conf_scrollable_frame = ttk.Frame(self.wfb_conf_canvas)

        self.wfb_conf_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.wfb_conf_canvas.configure(
                scrollregion=self.wfb_conf_canvas.bbox("all")
            )
        )

        self.wfb_conf_canvas.create_window((0, 0), window=self.wfb_conf_scrollable_frame, anchor="nw")
        self.wfb_conf_scrollbar.config(command=self.wfb_conf_canvas.yview)

        self.wfb_conf_canvas.pack(side="left", fill="both", expand=True)
        self.wfb_conf_scrollbar.pack(side="right", fill="y")

        # Create scrollable frame for majestic.yaml
        self.majestic_yaml_canvas = tk.Canvas(self.majestic_yaml_frame)
        self.majestic_yaml_scrollbar = ttk.Scrollbar(self.majestic_yaml_frame, orient="vertical", command=self.majestic_yaml_canvas.yview)
        self.majestic_yaml_scrollable_frame = ttk.Frame(self.majestic_yaml_canvas)

        # Inside the create_widgets method, after updating the majestic YAML tab
        self.update_majestic_yaml_tab("")  # Ensure this is called to populate the tab

        # Add Save button to the majestic.yaml tab
        self.save_button = ttk.Button(self.majestic_yaml_frame, text="Save", command=self.save_majestic_yaml)
        self.save_button.pack(pady=10)


        self.majestic_yaml_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.majestic_yaml_canvas.configure(
                scrollregion=self.majestic_yaml_canvas.bbox("all")
            )
        )

        self.majestic_yaml_canvas.create_window((0, 0), window=self.majestic_yaml_scrollable_frame, anchor="nw")
        self.majestic_yaml_scrollbar.config(command=self.majestic_yaml_canvas.yview)

        self.majestic_yaml_canvas.pack(side="left", fill="both", expand=True)
        self.majestic_yaml_scrollbar.pack(side="right", fill="y")

        # Create logs area
        self.logs_text = scrolledtext.ScrolledText(self.logs_frame, wrap="word", height=20)
        self.logs_text.pack(fill="both", expand=True)

        # Add Save Log button to logs tab
        self.save_log_button = ttk.Button(self.logs_frame, text="Save Log", command=self.save_log)
        self.save_log_button.pack(pady=10)

        # Add form elements to wfb.conf tab
        self.wfb_entries = {}
        self.update_wfb_conf_tab("")

        # Add form elements to majestic.yaml tab
        self.majestic_entries = {}
        self.update_majestic_yaml_tab("")

        # Add connection form
        self.connection_frame = ttk.Frame(self.root)
        self.connection_frame.pack(pady=10)

        self.create_connection_form(self.connection_frame)

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

            stdin, stdout, stderr = ssh.exec_command("cat /etc/majestic.yaml")
            majestic_yaml_output = stdout.read().decode()
            self.append_log("Output of /etc/majestic.yaml:\n" + majestic_yaml_output)

            # Update tabs with the content
            self.update_wfb_conf_tab(wfb_conf_output)
            self.update_majestic_yaml_tab(majestic_yaml_output)

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
                self.wfb_entries[key] = entry
                row_number += 1

        # Update the scroll region of the canvas
        self.wfb_conf_canvas.update_idletasks()
        self.wfb_conf_canvas.config(scrollregion=self.wfb_conf_canvas.bbox("all"))

    # def update_majestic_yaml_tab(self, yaml_content):
    #     if yaml_content:
    #         try:
    #             data = yaml.safe_load(yaml_content)
    #             if data:
    #                 # Clear the previous widgets in the tab
    #                 for widget in self.majestic_yaml_frame.winfo_children():
    #                     widget.destroy()

    #                 # Create a vertical form layout for YAML content
    #                 row = 0
    #                 for key, value in data.items():
    #                     label = tk.Label(self.majestic_yaml_frame, text=f"{key}:")
    #                     label.grid(row=row, column=0, sticky='w')

    #                     text_box = tk.Entry(self.majestic_yaml_frame, width=50)
    #                     text_box.grid(row=row, column=1, sticky='w')
    #                     text_box.insert(0, str(value))

    #                     row += 1
    #             else:
    #                 print("No data found in YAML content.")
    #         except yaml.YAMLError as e:
    #             print(f"Error parsing YAML: {e}")
    #     else:
    #         print("YAML content is empty or None.")

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

    def save_log(self):
        # Ask the user where to save the log file
        log_content = self.logs_text.get("1.0", tk.END)  # Get all text from the logs
        if not log_content.strip():
            print("No logs to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Log"
        )

        if file_path:  # Proceed if a valid path is provided
            try:
                with open(file_path, 'w') as file:
                    file.write(log_content)
                print(f"Log saved successfully to {file_path}.")
            except Exception as e:
                print(f"Error saving log: {e}")

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

    def append_log(self, message):
        self.logs_text.insert("end", message + "\n")
        self.logs_text.yview("end")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
