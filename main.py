import pygame
import sys

pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Platformer Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
GREY = (128, 128, 128)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(GREY)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Player(pygame.sprite.Sprite):
    def __init__(self, platforms):
        super().__init__()
        self.idle_spritesheet = pygame.image.load('assets/idle_spritesheet.png').convert_alpha()
        self.running_spritesheet = pygame.image.load('assets/running_spritesheet.png').convert_alpha()
        self.frame_width = 64
        self.frame_height = 64
        self.image = self.get_idle_image(0)  # Initial frame
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.y = 500
        self.change_x = 0
        self.change_y = 0
        self.jump_speed = -10
        self.gravity = 0.6
        self.platforms = platforms
        self.jumps = 0  # Track the number of jumps performed
        self.max_jumps = 2  # Allow double jump
        self.dash_speed = 80  # Increased dash speed
        self.dash_duration = 40  # Adjusted dash duration
        self.dash_cooldown = 30
        self.dashing = False
        self.dash_time = 0
        self.dash_cooldown_time = 0
        self.last_key_time = {'left': 0, 'right': 0}
        self.double_tap_threshold = 200  # in milliseconds
        self.ghost_trail = []  # List to hold ghost trail images
        self.idle_frame = 0  # Current idle frame
        self.running_frame = 0  # Current running frame
        self.animation_speed = 0.2  # Speed of animation (in seconds)
        self.last_update = pygame.time.get_ticks()
        self.facing_right = True  # Track direction
        self.acceleration = 0.5  # Rate of acceleration
        self.deceleration = 0.2  # Rate of deceleration
        self.max_speed = 6  # Maximum movement speed
        self.moving = False  # Whether the player is moving
        self.on_wall = False  # Whether the player is touching a wall
        self.wall_sticking = False  # Whether the player is sticking to a wall

    def get_idle_image(self, frame):
        rect = pygame.Rect(0, frame * self.frame_height, self.frame_width, self.frame_height)
        image = self.idle_spritesheet.subsurface(rect).copy()
        return image

    def get_running_image(self, frame):
        rect = pygame.Rect(0, frame * self.frame_height, self.frame_width, self.frame_height)
        image = self.running_spritesheet.subsurface(rect).copy()
        return image

    def update(self):
        if self.dashing:
            if pygame.time.get_ticks() - self.dash_time >= self.dash_duration:
                self.dashing = False
                self.change_x = 0
                self.ghost_trail = []  # Clear ghost trail after dashing
            else:
                # Create ghost trail image and add to the list
                ghost_image = self.image.copy()
                ghost_image.set_alpha(100)  # Set alpha for transparency
                self.ghost_trail.append((ghost_image, self.rect.topleft))  # Save position too
        if not self.wall_sticking:
            self.calc_gravity()
        self.rect.x += self.change_x
        self.check_collision('x')
        self.rect.y += self.change_y
        self.check_collision('y')
        # Ensure player doesn't go off the window edges
        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
    
        self.rect.y += self.change_y
        self.check_collision('y')
    
        # Ensure player doesn't go off the window edges
        self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT - self.rect.height))

        # Animation handling
        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed * 1000:  # Convert to milliseconds
            self.last_update = now
            if self.moving:
                self.running_frame = (self.running_frame + 1) % 3  # Assuming 3 frames in the running sprite sheet
                self.image = self.get_running_image(self.running_frame)
            else:
                self.idle_frame = (self.idle_frame + 1) % 2  # Assuming 2 frames in the idle sprite sheet
                self.image = self.get_idle_image(self.idle_frame)
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)  # Flip image if facing left

    def calc_gravity(self):
        if self.change_y == 0:
            self.change_y = 1
        else:
            self.change_y += self.gravity

    def jump(self):
        if self.wall_sticking:
            self.wall_sticking = False
            self.change_y = self.jump_speed
            if self.facing_right:
                self.change_x = -self.max_speed  # Jump left off the wall
            else:
                self.change_x = self.max_speed  # Jump right off the wall
        elif self.jumps < self.max_jumps:
            self.change_y = self.jump_speed
            self.jumps += 1

    def move_left(self):
        if not self.dashing:
            if self.change_x < 0:  # If already moving left
                self.change_x -= self.acceleration  # Accelerate further left
            else:  # If not moving left
                self.change_x = -self.max_speed  # Start moving left at max speed
            self.facing_right = False  # Face left
            self.moving = True  # Set moving to true

    def move_right(self):
        if not self.dashing:
            if self.change_x > 0:  # If already moving right
                self.change_x += self.acceleration  # Accelerate further right
            else:  # If not moving right
                self.change_x = self.max_speed  # Start moving right at max speed
            self.facing_right = True  # Face right
            self.moving = True  # Set moving to true

    def stop(self):
        if not self.dashing:
            self.change_x = 0  # Reset horizontal movement speed to zero when key is released
            self.moving = False  # Set moving to false

    def dash(self, direction):
        if not self.dashing and pygame.time.get_ticks() - self.dash_cooldown_time >= self.dash_cooldown:
            self.dashing = True
            self.dash_time = pygame.time.get_ticks()
            self.dash_cooldown_time = pygame.time.get_ticks()
            self.change_x = self.dash_speed * direction

    def check_collision(self, direction):
        if direction == 'x':
            collisions = pygame.sprite.spritecollide(self, self.platforms, False)
            self.on_wall = False  # Reset wall status
            for platform in collisions:
                if self.change_x > 0:  # Moving right
                    self.rect.right = platform.rect.left
                    self.on_wall = True  # Touching a wall
                elif self.change_x < 0:  # Moving left
                    self.rect.left = platform.rect.right
                    self.on_wall = True  # Touching a wall
            if self.on_wall and self.change_y > 0:
                self.wall_stick()  # Stick to the wall if moving down and pressing against the wall
        elif direction == 'y':
            collisions = pygame.sprite.spritecollide(self, self.platforms, False)
            for platform in collisions:
                if self.change_y > 0:  # Falling down
                    self.rect.bottom = platform.rect.top
                    self.change_y = 0
                    self.jumps = 0  # Reset jumps when landing on a platform
                    self.wall_sticking = False  # Stop wall sticking when landing on a platform
                elif self.change_y < 0:  # Jumping up
                    self.rect.top = platform.rect.bottom
                    self.change_y = 0

    def wall_stick(self):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_a] and self.change_x < 0) or (keys[pygame.K_d] and self.change_x > 0):
            self.wall_sticking = True
            self.change_y = 0  # Stop falling when sticking to the wall

def game_loop():
    platforms = pygame.sprite.Group()
    platform1 = Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40)
    platform2 = Platform(200, 400, 200, 20)
    platform3 = Platform(400, 300, 200, 20)
    wall = Platform(600, 200, 40, 400)  # Adding a wall
    platforms.add(platform1, platform2, platform3, wall)

    player = Player(platforms)

    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)
    all_sprites.add(platform1, platform2, platform3, wall)

    clock = pygame.time.Clock()
    while True:
        current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    if current_time - player.last_key_time['left'] < player.double_tap_threshold:
                        player.dash(-1)
                    else:
                        player.move_left()
                    player.last_key_time['left'] = current_time
                elif event.key == pygame.K_d:
                    if current_time - player.last_key_time['right'] < player.double_tap_threshold:
                        player.dash(1)
                    else:
                        player.move_right()
                    player.last_key_time['right'] = current_time
                elif event.key == pygame.K_w:
                    player.jump()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_a or event.key == pygame.K_d:
                    player.stop()

        all_sprites.update()

        screen.fill(PURPLE)
        all_sprites.draw(screen)

        # Draw ghost trail
        for ghost_image, ghost_pos in player.ghost_trail:
            screen.blit(ghost_image, ghost_pos)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    game_loop()
