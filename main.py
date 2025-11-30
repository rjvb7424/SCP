import pygame
import sys

from staff import Staff
from personnel_profile import draw_personnel_page
from operations import Operations
from operations_page import draw_operations_page
from tasks import TaskManager
from calendar_page import draw_calendar_page
from ui_common import draw_text, draw_menu, draw_anomalies_page


class Game:
    def __init__(self):
        pygame.init()

        self.FPS = 60
        self.MENU_HEIGHT = 40

        # Start fullscreen-sized but resizable
        info = pygame.display.Info()
        self.WIDTH, self.HEIGHT = info.current_w, info.current_h
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("SCP")

        self.clock = pygame.time.Clock()

        # In-game day counter (FM-style)
        self.current_day = 0

        # --- Staff setup ---
        KEY_POSITIONS = [
            "Site Director",
            "Chief of Security",
            "Chief Researcher",
        ]

        self.staff_roster = Staff(key_positions=KEY_POSITIONS, num_random=5)
        self.flag_images = [self.load_flag_image(p.flag_path) for p in self.staff_roster.members]

        # --- Operations setup ---
        self.operations_manager = Operations(num_operations=10)
        self.operation_flag_images = [
            self.load_flag_image(op.flag_path) for op in self.operations_manager.operations
        ]

        try:
            self.world_map_image = pygame.image.load("world_map.jpg").convert()
        except pygame.error as e:
            print(f"Could not load world_map.jpg: {e}")
            self.world_map_image = None

        # --- Task manager / calendar ---
        self.task_manager = TaskManager()

        # Fonts
        self.title_font = pygame.font.Font(None, 32)
        self.body_font = pygame.font.Font(None, 26)
        self.menu_font = pygame.font.Font(None, 24)

        # Menu tabs
        self.menu_items = [
            {"name": "Personnel File", "page": "personnel", "rect": pygame.Rect(20, 5, 150, 30)},
            {"name": "Anomalies",      "page": "anomalies", "rect": pygame.Rect(190, 5, 150, 30)},
            {"name": "Operations",     "page": "operations", "rect": pygame.Rect(360, 5, 150, 30)},
            {"name": "Calendar",       "page": "calendar",  "rect": pygame.Rect(530, 5, 150, 30)},
        ]

        self.current_page = "personnel"

        # Operations UI state
        self.operation_mode = "view"         # "view" or "assign"
        self.selected_team_indices = set()

        # Calendar UI state
        self.calendar_selected_staff_index = None

        # Clickable zones / cached rects
        self.staff_menu_rects = []
        self.operation_marker_rects = []
        self.op_execute_rect = None
        self.op_cancel_rect = None
        self.op_confirm_rect = None
        self.op_staff_item_rects = []
        self.cal_staff_rows = []
        self.cal_task_buttons = []
        self.cal_continue_rect = None

    # ---------- Init helpers ----------

    def load_flag_image(self, path, size=(64, 40)):
        if not path:
            return None
        try:
            flag_img = pygame.image.load(path).convert_alpha()
            flag_img = pygame.transform.smoothscale(flag_img, size)
            return flag_img
        except pygame.error as e:
            print(f"Could not load flag image {path}: {e}")
            return None

    # ---------- Main loop ----------

    def run(self):
        running = True
        while running:
            self.clock.tick(self.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)

            self.draw()

        pygame.quit()
        sys.exit()

    # ---------- Event handling ----------

    def handle_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self.WIDTH, self.HEIGHT = event.w, event.h
            self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)

        elif event.type == pygame.KEYDOWN:
            self.handle_keydown(event)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.handle_mouse_click(event.pos)

    def handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE:
            # ESC: just post a QUIT so the main loop exits
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if event.key == pygame.K_RIGHT:
            if self.current_page == "personnel":
                self.staff_roster.next()
            elif self.current_page == "operations":
                self.operations_manager.next()
                self.operation_mode = "view"
                self.selected_team_indices.clear()

        elif event.key == pygame.K_LEFT:
            if self.current_page == "personnel":
                self.staff_roster.previous()
            elif self.current_page == "operations":
                self.operations_manager.previous()
                self.operation_mode = "view"
                self.selected_team_indices.clear()

    def handle_mouse_click(self, pos):
        mx, my = pos

        # Top menu tabs
        for item in self.menu_items:
            if item["rect"].collidepoint(mx, my):
                self.current_page = item["page"]

                # Reset page-specific modes when leaving them
                if self.current_page != "operations":
                    self.operation_mode = "view"
                    self.selected_team_indices.clear()
                if self.current_page != "calendar":
                    self.calendar_selected_staff_index = None

                return  # don't also click into page content in the same frame

        # Route to page-specific handlers
        if self.current_page == "personnel":
            self.handle_personnel_click(mx, my)
        elif self.current_page == "operations":
            self.handle_operations_click(mx, my)
        elif self.current_page == "calendar":
            self.handle_calendar_click(mx, my)

    # ---------- Per-page mouse handlers ----------

    def handle_personnel_click(self, mx, my):
        for idx, rect in self.staff_menu_rects:
            if rect.collidepoint(mx, my):
                self.staff_roster._current_index = idx
                break

    def handle_operations_click(self, mx, my):
        # Select operation from map
        for idx, rect in self.operation_marker_rects:
            if rect.collidepoint(mx, my):
                self.operations_manager.select(idx)
                self.operation_mode = "view"
                self.selected_team_indices.clear()
                return

        if self.operation_mode == "view":
            # Switch to team assignment
            if self.op_execute_rect and self.op_execute_rect.collidepoint(mx, my):
                op = self.operations_manager.current
                if op and op.status == "Available":
                    any_active = any(
                        getattr(p, "status", "Active") == "Active"
                        for p in self.staff_roster.members
                    )
                    if any_active:
                        self.operation_mode = "assign"
                        self.selected_team_indices.clear()

        elif self.operation_mode == "assign":
            # Toggle team members
            for s_idx, rect in self.op_staff_item_rects:
                if rect.collidepoint(mx, my):
                    person = self.staff_roster.members[s_idx]
                    if getattr(person, "status", "Active") == "Active":
                        if s_idx in self.selected_team_indices:
                            self.selected_team_indices.remove(s_idx)
                        else:
                            self.selected_team_indices.add(s_idx)
                    return

            # Cancel assignment
            if self.op_cancel_rect and self.op_cancel_rect.collidepoint(mx, my):
                self.operation_mode = "view"
                self.selected_team_indices.clear()

            # Confirm and run simulation
            elif self.op_confirm_rect and self.op_confirm_rect.collidepoint(mx, my):
                if self.selected_team_indices:
                    team = []
                    for s_idx in self.selected_team_indices:
                        if 0 <= s_idx < len(self.staff_roster.members):
                            person = self.staff_roster.members[s_idx]
                            if getattr(person, "status", "Active") == "Active":
                                team.append(person)
                    if team:
                        op = self.operations_manager.current
                        if op:
                            op.simulate(team)
                self.operation_mode = "view"
                self.selected_team_indices.clear()

    def handle_calendar_click(self, mx, my):
        # Select staff member on the left list
        for s_idx, rect in self.cal_staff_rows:
            if rect.collidepoint(mx, my):
                self.calendar_selected_staff_index = s_idx
                return

        # Click role-specific task buttons
        if (
            self.calendar_selected_staff_index is not None
            and 0 <= self.calendar_selected_staff_index < len(self.staff_roster.members)
        ):
            person = self.staff_roster.members[self.calendar_selected_staff_index]
            for task_def, rect in self.cal_task_buttons:
                if rect.collidepoint(mx, my):
                    if person.status == "Active" and person.current_task is None:
                        self.task_manager.create_task(
                            task_def["name"],
                            person,
                            self.current_day,
                            task_def["duration"],
                            task_def["description"],
                        )
                    return

        # "Continue" button to advance to next event / day
        if self.cal_continue_rect and self.cal_continue_rect.collidepoint(mx, my):
            self.current_day, finished_tasks = self.task_manager.advance_to_next_event(
                self.current_day
            )
            # later: show finished_tasks somewhere

    # ---------- Drawing ----------

    def draw(self):
        self.screen.fill((30, 30, 30))
        draw_menu(
            self.screen,
            self.menu_items,
            self.current_page,
            self.menu_font,
            self.WIDTH,
            self.MENU_HEIGHT,
        )

        if self.current_page == "personnel":
            self.draw_personnel_page()
        elif self.current_page == "anomalies":
            draw_anomalies_page(self.screen, self.body_font, self.MENU_HEIGHT)
        elif self.current_page == "operations":
            self.draw_operations_page()
        elif self.current_page == "calendar":
            self.draw_calendar_page()

        pygame.display.flip()

    def draw_personnel_page(self):
        if len(self.staff_roster) == 0:
            self.staff_menu_rects = []
            return

        person = self.staff_roster.current
        idx = self.staff_roster.current_index
        flag_image = self.flag_images[idx] if 0 <= idx < len(self.flag_images) else None

        self.staff_menu_rects = draw_personnel_page(
            self.screen,
            person,
            flag_image,
            self.title_font,
            self.body_font,
            self.WIDTH,
            self.HEIGHT,
            self.MENU_HEIGHT,
            idx,
            len(self.staff_roster),
            self.staff_roster.members,
        )

    def draw_operations_page(self):
        (
            self.operation_marker_rects,
            self.op_execute_rect,
            self.op_cancel_rect,
            self.op_confirm_rect,
            self.op_staff_item_rects,
        ) = draw_operations_page(
            self.screen,
            self.world_map_image,
            self.operations_manager,
            self.operation_flag_images,
            self.staff_roster,
            self.operation_mode,
            self.selected_team_indices,
            self.title_font,
            self.body_font,
            self.WIDTH,
            self.HEIGHT,
            self.MENU_HEIGHT,
        )

    def draw_calendar_page(self):
        (
            self.cal_staff_rows,
            self.cal_task_buttons,
            self.cal_continue_rect,
        ) = draw_calendar_page(
            self.screen,
            self.task_manager,
            self.staff_roster,
            self.current_day,
            self.calendar_selected_staff_index,
            self.title_font,
            self.body_font,
            self.WIDTH,
            self.HEIGHT,
            self.MENU_HEIGHT,
        )


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
