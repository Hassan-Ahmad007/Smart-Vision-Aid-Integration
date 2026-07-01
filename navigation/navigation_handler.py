# =======================================
# navigation/navigation_handler.py
# =======================================

class NavigationHandler:
    def __init__(self):
        self.last_nav_msg = ""

    def handle_navigation(self, nav_cmd, obstacle_just_cleared):
        """
        Processes navigation instructions.
        """
        if not nav_cmd:
            return None

        # 🟢 PRIORITY 1: Obstacle just cleared. Force navigation.
        if obstacle_just_cleared:
            self.last_nav_msg = nav_cmd
            return f"Path clear. {nav_cmd}"

        # 🟢 PRIORITY 2: New instruction
        if nav_cmd != self.last_nav_msg:
            self.last_nav_msg = nav_cmd
            return nav_cmd

        return None

    def reset_nav_memory(self):
        """Wipes the memory so the navigation will repeat its next command."""
        self.last_nav_msg = ""