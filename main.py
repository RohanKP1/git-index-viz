import customtkinter as ctk
from gui import GitIndexVisualizer

# Set appearance mode and default color theme
ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

def main():
    app = GitIndexVisualizer()
    app.mainloop()

if __name__ == "__main__":
    main()