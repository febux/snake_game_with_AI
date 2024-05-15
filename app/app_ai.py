import numpy as np
import pygame

from app.ai_modules.agent import Agent
# from app.ai_modules.plot import plot
from app.app import App, Direction, AppLoop
from cells.body_cell import Head


class AppAI(App):

    def __init__(
        self,
        app_height: int = 600,
        app_width: int = 400,
        *,
        block_size: int = 10,
        food_multiplier: int = 1,
        speed: int = 5,
        agents_amount: int = 1,
    ) -> None:
        super(AppAI, self).__init__(
            app_height=app_height,
            app_width=app_width,
            block_size=block_size,
            food_multiplier=food_multiplier,
            speed=speed,
        )
        self.agents = [Agent(food_multiplier=food_multiplier) for _ in range(agents_amount)]
        self.reward = 0

    def start_game(self):
        super(AppAI, self).start_game()
        self.direction = self.changeto = Direction.RIGHT

    def game_over(self) -> None:
        self.direction = self.changeto = Direction.UNKNOWN
        self.app_loop = AppLoop.STOP
        pygame.display.update()

    def check_self_bait(self, head_cell: Head = None) -> bool:
        if head_cell is None:
            head_cell = self.head
        for element in self.body.cells[1:]:
            if head_cell.loc_x == element.loc_x and head_cell.loc_y == element.loc_y:
                self.reward = -100
                return True
        return False

    def check_border_cross(self, head_cell: Head = None) -> bool:
        if head_cell is None:
            head_cell = self.head
        if (head_cell.loc_x > self.app_height or head_cell.loc_x < 0
                or head_cell.loc_y > self.app_width or head_cell.loc_y < 0):
            self.reward = -100
            return True
        return False

    def monitoring_food_bait(self):
        for index, food in enumerate(self.food_array):
            if self.head.loc_x == food.loc_x and self.head.loc_y == food.loc_y:
                self.eat_food(index)
                self.score += 1
                self.reward = 100
                self.increase_body()
                self.add_food()
        else:
            if self.direction != Direction.UNKNOWN and self.changeto != Direction.UNKNOWN:
                self.body.cells.pop()

    def run(self):
        plot_scores = []
        plot_mean_scores = []
        total_score = 0
        record = 0

        while True:
            self.event_listener()
            # get old state
            if self.app_loop is AppLoop.RUN:
                state_old = self.agents[0].get_state(self)

                # get move
                final_move = self.agents[0].get_action(state_old)

                # perform move and get new state
                clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
                idx = clock_wise.index(self.direction)

                if np.array_equal(final_move, [1, 0, 0]):
                    new_dir = clock_wise[idx]  # no change
                elif np.array_equal(final_move, [0, 1, 0]):
                    next_idx = (idx + 1) % 4
                    new_dir = clock_wise[next_idx]  # right turn r -> d -> l -> u
                else:  # [0, 0, 1]
                    next_idx = (idx - 1) % 4
                    new_dir = clock_wise[next_idx]  # left turn r -> u -> l -> d

                self.changeto = new_dir
                self.game_step()
                state_new = self.agents[0].get_state(self)

                # train short memory
                self.agents[0].train_short_memory(state_old, final_move, self.reward, state_new, self.app_loop)

                # remember
                self.agents[0].remember(state_old, final_move, self.reward, state_new, self.app_loop)

                self.reward = 0

                if self.app_loop is AppLoop.STOP:
                    # train long memory, plot result
                    self.agents[0].n_games += 1
                    self.agents[0].train_long_memory()

                    if self.score > record:
                        record = self.score
                        self.agents[0].model.save()

                    print('Game', self.agents[0].n_games, 'Score', self.score, 'Record:', record)

                    plot_scores.append(self.score)
                    # total_score += self.score
                    # mean_score = total_score / self.agents[0].n_games
                    # plot_mean_scores.append(mean_score)
                    # plot(plot_scores, plot_mean_scores)
                    self.start_game()
