import sys
from time import sleep
from pathlib import Path

import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien

class AlienInvasion:
    """Overall class to manage game assets and behavior."""

    def __init__(self):
        """Initialize the game, and create game resources."""
        pygame.init()
        # Ensure the mixer is initialized (pygame.init() often does this, but be explicit)
        try:
            pygame.mixer.init()
        except Exception:
            # If mixer fails to init, we'll handle missing sounds gracefully below
            pass

        self.settings = Settings()

        # For fullscreen.
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height

        pygame.display.set_caption("Alien Invasion")

        # Create an instance to store game statistics and create a scoreboard.
        # These were missing and caused the AttributeError: 'AlienInvasion' object has no attribute 'stats'
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        # Base directory for resources (this file's directory), so resources are found
        # regardless of the current working directory when the script is launched.
        self.base_dir = Path(__file__).resolve().parent

        # Load the background image (gracefully fall back to a filled color if missing)
        bg_path = (self.base_dir / "images" / "galaxy4_bg.jpg")
        if bg_path.exists():
            try:
                self.bg_image = pygame.image.load(str(bg_path))
                self.bg_image = pygame.transform.scale(
                    self.bg_image, (self.settings.screen_width, self.settings.screen_height)
                )
            except Exception as e:
                print(f"Warning: failed to load background image {bg_path}: {e}")
                self.bg_image = None
        else:
            print(f"Warning: background image not found at {bg_path}")
            self.bg_image = None

        # Helper to safely load sounds
        def load_sound_safe(path: Path):
            if not path.exists():
                print(f"Warning: sound file not found: {path}")
                return None
            try:
                return pygame.mixer.Sound(str(path))
            except Exception as e:
                print(f"Warning: failed to load sound {path}: {e}")
                return None

        # Load the shooting sound
        shoot_path = self.base_dir / "sounds" / "shoot_sound.wav"
        self.shoot_sound = load_sound_safe(shoot_path)

        # Load the hit sound (bullet hitting alien)
        hit_path = self.base_dir / "sounds" / "hit_sound.wav"
        self.hit_sound = load_sound_safe(hit_path)

        # Load background music (if available)
        music_path = self.base_dir / "sounds" / "background_music.mp3"
        if music_path.exists():
            try:
                pygame.mixer.music.load(str(music_path))
                pygame.mixer.music.set_volume(0.5)  # Optional: Set music volume (0.0 to 1.0)
                pygame.mixer.music.play(-1, 0.0)  # Loop the music indefinitely (-1)
            except Exception as e:
                print(f"Warning: failed to load/play background music {music_path}: {e}")
        else:
            print(f"Info: background music not found at {music_path}, continuing without music")

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()

        # Make the Play button.
        self.play_button = Button(self, "START")

    def run_game(self):
        """Start the main loop for the game."""
        while True:
            self._check_events()
            if self.stats.game_active:
                self._update_bullets()
                self._update_aliens()
                self.ship.update()
            self._update_screen()

    def _update_screen(self):
        """Update images on the screen, and flip to the new screen."""
        # Draw the background image or a fallback fill.
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
        else:
            # fallback background color
            self.screen.fill((0, 0, 30))

        # Draw the ship, bullets, and aliens.
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)

        # Draw the score information.
        self.sb.show_score()

        # Draw the play button if the game is inactive.
        if not self.stats.game_active:
            self.play_button.draw_button()

        # Make the most recently drawn screen visible.
        pygame.display.flip()

    def _create_fleet(self):
        """Create the fleet of aliens."""
        # Make spacing between each alien.
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)

        # Determine the number of rows of aliens that fit on the screen.
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - (5 * alien_height) - ship_height)
        number_rows = available_space_y // (3 * alien_height)

        # Create the full fleet of aliens.
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        """Create an alien and place it in the row."""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        # Check alien.x instance variable to make them fit right.
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def _check_fleet_edges(self):
        """Respond appropriately if any aliens have reached an edge."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Drop the entire fleet and change the fleet's direction."""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _check_events(self):
        """Respond to keypresses and the mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self, mouse_pos):
        """Start a new game when the player clicks Play."""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            # Reset the game settings.
            self.settings.initialize_dynamic_settings()

            # Reset the game statistics.
            self.stats.reset_stats()
            self.stats.game_active = True
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            # Get rid of any remaining aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()

            # Create a new fleet and center the ship
            self._create_fleet()
            self.ship.center_ship()

            # Hide the mouse cursor.
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        """Respond to keypresses."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_a:
            self.ship.moving_left = True
        elif event.key == pygame.K_d:
            self.ship.moving_right = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()
            # Play the shooting sound when spacebar is pressed (if loaded)
            if self.shoot_sound:
                try:
                    self.shoot_sound.play()
                except Exception:
                    pass

    def _check_keyup_events(self, event):
        """Respond to key releases."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False
        elif event.key == pygame.K_a:
            self.ship.moving_left = False
        elif event.key == pygame.K_d:
            self.ship.moving_right = False

    def _check_aliens_bottom(self):
        """Check if any aliens have reached the bottom of the screen."""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                # Treat this the same as if the ship got hit.
                self._ship_hit()
                break

    def _fire_bullet(self):
        """Create a new bullet and add it to the bullets group."""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """Update position of bullets and get rid of old bullets."""
        # Update bullet positions.
        self.bullets.update()

        # Get rid of bullets that have disappeared.
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """Respond to bullet-alien collisions."""
        # Remove any bullets and aliens that have collided.
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if collisions:
            # collisions is a dict: bullet -> list_of_aliens_hit_by_that_bullet
            gained = 0
            for aliens in collisions.values():
                gained += self.settings.alien_points * len(aliens)
            self.stats.score += gained
            self.sb.prep_score()
            self.sb.check_high_score()

            # Play the hit sound when a bullet hits an alien (if loaded)
            if self.hit_sound:
                try:
                    self.hit_sound.play()
                except Exception:
                    pass

        if not self.aliens:
            # Destroy existing bullets and create new fleet.
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            # Increase level.
            self.stats.level += 1
            self.sb.prep_level()

    def _ship_hit(self):
        """Respond to the ship being hit by the alien."""
        if self.stats.ships_left > 0:
            # Decrement ships_left, and update scoreboard.
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            # Get rid of any remaining aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()

            # Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()

            # Pause.
            sleep(0.5)

        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _update_aliens(self):
        """Check if the fleet is at an edge, the update the positions of all aliens in the fleet."""
        self._check_fleet_edges()
        self.aliens.update()

        # Look for alien-ship collisions.
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # Look for aliens hitting the bottom of the screen.
        self._check_aliens_bottom()

if __name__ == '__main__':
    # Make a game instance, and run the game.
    ai = AlienInvasion()
    ai.run_game()