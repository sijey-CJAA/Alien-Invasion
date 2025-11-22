import pygame.font
from pygame.sprite import Group
from ship import Ship

class Scoreboard:
    """A class to report scoring information."""
    def __init__(self, ai_game):
        """Initialize scorekeeping attributes."""
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.screen_rect = self.screen.get_rect()
        self.settings = ai_game.settings
        self.stats = ai_game.stats

        # Font settings for scoring information.
        self.text_color = (0, 222, 255)
        self.font = pygame.font.SysFont(None, 48)
        self.label_font = pygame.font.SysFont(None, 36)  # Smaller font for labels

        # Prepare the initial score images.
        self.prep_score()
        self.prep_high_score()
        self.prep_level()
        self.prep_ships()

    def prep_ships(self):
        """Show how many ships are left."""
        self.ships = Group()

        for ship_number in range(self.stats.ships_left):
            ship = Ship(self.ai_game)
            ship.rect.x = 10 + ship_number * ship.rect.width
            ship.rect.y = 10
            self.ships.add(ship)

    def prep_score(self):
        """Turn the score into a rendered image."""
        rounded_score = round(self.stats.score, -1)
        score_str = "{:,}".format(rounded_score)
        score_str = str(self.stats.score)
        self.score_image = self.font.render(score_str, True, self.text_color)

        # Set the transparency (alpha value) of the score image
        self.score_image.set_alpha(200)  # Adjust alpha for transparency

        # Display the score at the top right of the screen.
        self.score_rect = self.score_image.get_rect()
        self.score_rect.right = self.screen_rect.right - 20
        self.score_rect.top = 60  # Move down a little for the label

        # Label for Score
        self.score_label_image = self.label_font.render("Score:", True, self.text_color)
        self.score_label_rect = self.score_label_image.get_rect()
        self.score_label_rect.right = self.score_rect.left - 10
        self.score_label_rect.top = self.score_rect.top

    def prep_level(self):
        """Turn the level into a rendered image."""
        level_str = str(self.stats.level)
        self.level_image = self.font.render(level_str, True, self.text_color)

        # Set the transparency (alpha value) of the level image
        self.level_image.set_alpha(200)  # Adjust alpha for transparency

        # Position the level below the score.
        self.level_rect = self.level_image.get_rect()
        self.level_rect.right = self.score_rect.right
        self.level_rect.top = self.score_rect.bottom + 10

        # Label for Level
        self.level_label_image = self.label_font.render("Level:", True, self.text_color)
        self.level_label_rect = self.level_label_image.get_rect()
        self.level_label_rect.right = self.level_rect.left - 10
        self.level_label_rect.top = self.level_rect.top

    def prep_high_score(self):
        """Turn the high score into a rendered image."""
        high_score = round(self.stats.high_score, -1)
        high_score_str = "{:,}".format(high_score)
        high_score_str = str(self.stats.high_score)
        self.high_score_image = self.font.render(high_score_str, True, self.text_color)

        # Set the transparency (alpha value) of the high score image
        self.high_score_image.set_alpha(200)  # Adjust alpha for transparency

        # Label for High Score
        self.high_score_label_image = self.label_font.render("Highest score:", True, self.text_color)
        self.high_score_label_rect = self.high_score_label_image.get_rect()
        self.high_score_label_rect.centerx = self.screen_rect.centerx  # Center the label at the top
        self.high_score_label_rect.top = 20  # Position the label at the top

        # Position the high score below the label
        self.high_score_rect = self.high_score_image.get_rect()
        self.high_score_rect.centerx = self.screen_rect.centerx
        self.high_score_rect.top = self.high_score_label_rect.bottom + 5  # Slightly below the label

    def show_score(self):
        """Draw score, level, and ships to the screen."""
        self.screen.blit(self.high_score_label_image, self.high_score_label_rect)
        self.screen.blit(self.high_score_image, self.high_score_rect)

        self.screen.blit(self.score_label_image, self.score_label_rect)
        self.screen.blit(self.score_image, self.score_rect)

        self.screen.blit(self.level_label_image, self.level_label_rect)
        self.screen.blit(self.level_image, self.level_rect)

        self.ships.draw(self.screen)

    def check_high_score(self):
        """Check to see if there's a new high score."""
        if self.stats.score > self.stats.high_score:
            self.stats.high_score = self.stats.score
            self.prep_high_score()
