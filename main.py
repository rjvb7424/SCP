import pygame
import sys

from staff import Staff
from personnel_profile import draw_personnel_page
from tasks import TaskManager
from calendar_page import draw_calendar_page
from ui_common import draw_menu, draw_anomalies_page
from facility import Facility, BuildOrder
from facility_page import draw_facility_page

from operation import Operations, OperationRun
from operations_page import draw_operations_page, draw_operation_execution_page


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

        # In-game day counter
        self.current_day = 0

        # --- Staff setup ---
        KEY_POSITIONS = [
            "Site Director",
            "Chief of Security",
            "Chief Researcher",
        ]

        self.staff_roster = Staff(key_positions=KEY_POSITIONS, num_random=5)
        self.flag_images = [self.load_flag_image(p.flag_path) for p in self.staff_roster.members]

        # --- Operations setup (disabled for now) ---
        # self.operations_manager = Operations(num_operations=10)
        # self.operation_flag_images = [
        #     self.load_flag_image(op.flag_path) for op in self.operations_manager.operations
        # ]

        # Operation runtime (cinematic execution)
        self.active_operation_run: OperationRun | None = None

        # World map (used by operations originally; safe to keep loaded)
        try:
            self.world_map_image = pygame.image.load("world_map.jpg").convert()
        except pygame.error as e:
            print(f"Could not load world_map.jpg: {e}")
            self.world_map_image = None

        # --- Task manager / calendar ---
        self.task_manager = TaskManager()

        # --- Facility (Fallout Shelter-style base) ---
        self.facility = Facility()
        self.facility_build_orders: list[BuildOrder] = []

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
            {"name": "Facility",       "page": "facility",  "rect": pygame.Rect(700, 5, 150, 30)},
        ]

        self.current_page = "personnel"

        # Operations UI state
        self.operation_mode = "view"         # "view" or "assign"
        self.selected_team_indices = set()

        # Calendar UI state
        self.calendar_selected_staff_index = None

        # Facility UI state
        self.facility_mode = "view"  # "view" or "build"
        self.facility_selected_room_type = None
        self.facility_selected_cell = None
        self.facility_selected_builder_index = None

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

        self.facility_cell_rects = []
        self.facility_roomtype_buttons = []
        self.facility_builder_buttons = []
        self.facility_cancel_build_rect = None

    # ---------- Update ----------

    def update(self, dt: float):
        # Only thing we need to update for now is an active operation run
        if self.current_page == "operations" and self.active_operation_run is not None:
            self.active_operation_run.update(dt)

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
            dt = self.clock.tick(self.FPS) / 1000.0  # seconds since last frame

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)

            self.update(dt)
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
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        # If we are in the cinematic operation view, SPACE/ENTER exits when finished.
        if self.current_page == "operations" and self.active_operation_run is not None:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self.active_operation_run.finished:
                    self.active_operation_run = None
            # Don't do left/right switching etc while cinematic is active
            return

        if event.key == pygame.K_RIGHT:
            if self.current_page == "personnel":
                self.staff_roster.next()
            elif self.current_page == "operations":
                # self.operations_manager.next()
                self.operation_mode = "view"
                self.selected_team_indices.clear()

        elif event.key == pygame.K_LEFT:
            if self.current_page == "personnel":
                self.staff_roster.previous()
            elif self.current_page == "operations":
                # self.operations_manager.previous()
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
                    self.active_operation_run = None
                if self.current_page != "calendar":
                    self.calendar_selected_staff_index = None
                if self.current_page != "facility":
                    self.facility_mode = "view"
                    self.facility_selected_room_type = None
                    self.facility_selected_builder_index = None
                    self.facility_selected_cell = None

                return

        # Route to page-specific handlers
        if self.current_page == "personnel":
            self.handle_personnel_click(mx, my)
        elif self.current_page == "operations":
            self.handle_operations_click(mx, my)
        elif self.current_page == "calendar":
            self.handle_calendar_click(mx, my)
        elif self.current_page == "facility":
            self.handle_facility_click(mx, my)

    # ---------- Per-page mouse handlers ----------

    def handle_personnel_click(self, mx, my):
        for idx, rect in self.staff_menu_rects:
            if rect.collidepoint(mx, my):
                self.staff_roster._current_index = idx
                break

    def handle_operations_click(self, mx, my):
        # Operations are temporarily disabled while refactoring
        return

    def handle_calendar_click(self, mx, my):
        # Select staff row
        for s_idx, rect in self.cal_staff_rows:
            if rect.collidepoint(mx, my):
                self.calendar_selected_staff_index = s_idx
                return

        # Assign task to selected staff
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

        # Advance time
        if self.cal_continue_rect and self.cal_continue_rect.collidepoint(mx, my):
            self.current_day, finished_tasks = self.task_manager.advance_to_next_event(
                self.current_day
            )
            self.process_finished_tasks(finished_tasks)

    def handle_facility_click(self, mx, my):
        # Builder selection
        for idx, rect in self.facility_builder_buttons:
            if rect.collidepoint(mx, my):
                person = self.staff_roster.members[idx]
                if getattr(person, "status", "Active") == "Active":
                    self.facility_selected_builder_index = idx
                return

        # Room type selection
        for room_type, rect in self.facility_roomtype_buttons:
            if rect.collidepoint(mx, my):
                self.facility_mode = "build"
                self.facility_selected_room_type = room_type
                return

        # Cancel build mode
        if (
            self.facility_mode == "build"
            and self.facility_cancel_build_rect
            and self.facility_cancel_build_rect.collidepoint(mx, my)
        ):
            self.facility_mode = "view"
            self.facility_selected_room_type = None
            return

        # Click on a grid cell
        clicked = None
        for row, col, rect in self.facility_cell_rects:
            if rect.collidepoint(mx, my):
                clicked = (row, col)
                break

        if clicked is None:
            return

        row, col = clicked
        self.facility_selected_cell = clicked

        # If not in build mode, just viewing
        if self.facility_mode != "build":
            return

        # Build mode: need room type + builder
        if (
            self.facility_selected_room_type is None
            or self.facility_selected_builder_index is None
        ):
            return

        if self.facility.get_room(row, col) is not None:
            return  # occupied, can't build here

        if any(bo.row == row and bo.col == col for bo in self.facility_build_orders):
            return  # already under construction

        builder = self.staff_roster.members[self.facility_selected_builder_index]
        if getattr(builder, "status", "Active") != "Active":
            return
        if getattr(builder, "current_task", None) is not None:
            return  # already busy

        # Construction duration per room type
        build_durations = {
            "Command Center": 4,
            "Research Lab": 3,
            "Infirmary": 3,
            "Security Station": 3,
            "Dormitory": 2,
            "Common Room": 2,
        }
        duration = build_durations.get(self.facility_selected_room_type, 2)

        task = self.task_manager.create_task(
            name=f"Build {self.facility_selected_room_type}",
            assignee=builder,
            start_day=self.current_day,
            duration_days=duration,
            description=f"Construction of {self.facility_selected_room_type} at row {row+1}, col {col+1}.",
        )

        order = BuildOrder(
            row=row,
            col=col,
            room_type=self.facility_selected_room_type,
            task=task,
            builder=builder,
        )
        self.facility_build_orders.append(order)

    # ---------- Finished tasks hook (calendar) ----------

    def process_finished_tasks(self, finished_tasks):
        """
        Handle any special outcomes when tasks complete
        (e.g., finishing facility construction).
        """
        for t in finished_tasks:
            # Check for completed construction
            for order in list(self.facility_build_orders):
                if order.task is t:
                    built = self.facility.build_room(order.row, order.col, order.room_type)
                    if not built:
                        print(f"Failed to place room {order.room_type} at {order.row},{order.col}")
                    self.facility_build_orders.remove(order)

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
        elif self.current_page == "facility":
            self.draw_facility_page()

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
        # Operations drawing disabled for now
        # You could draw a simple placeholder text here if you want
        return

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

    def draw_facility_page(self):
        (
            self.facility_cell_rects,
            self.facility_roomtype_buttons,
            self.facility_builder_buttons,
            self.facility_cancel_build_rect,
        ) = draw_facility_page(
            self.screen,
            self.facility,
            self.staff_roster,
            self.facility_build_orders,
            self.current_day,
            self.title_font,
            self.body_font,
            self.WIDTH,
            self.HEIGHT,
            self.MENU_HEIGHT,
            self.facility_mode,
            self.facility_selected_room_type,
            self.facility_selected_cell,
            self.facility_selected_builder_index,
        )


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
