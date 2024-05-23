import pygame
import sys
import random

pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Platformer Game")

# Load background image
background_image = pygame.image.load('assets/background.png')
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Load block images
grass_block_image = pygame.image.load('assets/grass/1.png').convert_alpha()
stone_block_image = pygame.image.load('assets/stone/1.png').convert_alpha()
dirt_block_image = pygame.image.load('assets/grass/5.png').convert_alpha()

# Load sound effects
jump_sound = pygame.mixer.Sound('assets/sfx/jump.wav')
dash_sound = pygame.mixer.Sound('assets/sfx/dash.wav')

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, block_type):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)  # Allow transparency
        if block_type == 'grass':
            block_image = grass_block_image
        elif block_type == 'stone':
            block_image = stone_block_image
        elif block_type == 'dirt':
            block_image = dirt_block_image
        
        block_image = pygame.transform.scale(block_image, (16, 16))  # Scale the block image to 16x16

        # Fill the platform with the block image
        for i in range(0, width, 16):
            for j in range(0, height, 16):
                self.image.blit(block_image, (i, j))
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        if block_type == 'grass':
            self.create_dirt_underneath()
            self.add_decor()

    def create_dirt_underneath(self):
        dirt = Platform(self.rect.x, self.rect.y + self.rect.height, self.rect.width, 16, 'dirt')
        platforms.add(dirt)
        all_sprites.add(dirt)

    def add_decor(self):
        # Load decor images
        decor_images = ['assets/large_decor/0.png', 'assets/large_decor/1.png', 'assets/large_decor/2.png']
        for _ in range(random.randint(1, 3)):  # Add 1 to 3 decor elements per grass platform
            decor_image = random.choice(decor_images)
            decor_surface = pygame.image.load(decor_image).convert_alpha()
            decor_width = decor_surface.get_width()
            decor_height = decor_surface.get_height()

            # Ensure decor is placed within the boundaries of the grass block
            decor_x = self.rect.x + random.randint(0, self.rect.width - decor_width)
            decor_y = self.rect.y - decor_height  # Place decor on top of the grass block

            decor = Decor(decor_x, decor_y, decor_image)
            all_sprites.add(decor)
            decor_group.add(decor)

class Cloud(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, image_path):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed

    def update(self):
        self.rect.x += self.speed
        if self.rect.x > SCREEN_WIDTH:
            self.rect.x = -self.rect.width

class Decor(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Player(pygame.sprite.Sprite):
    def __init__(self, platforms):
        super().__init__()
        self.idle_spritesheet = [pygame.image.load('assets/player/idle/0.png').convert_alpha(),
                                 pygame.image.load('assets/player/idle/1.png').convert_alpha()]
        self.running_frames = [pygame.image.load('assets/player/running/0.png').convert_alpha(), 
                               pygame.image.load('assets/player/running/1.png').convert_alpha(),
                               pygame.image.load('assets/player/running/2.png').convert_alpha()]
        # Define the dimensions of the frames
        self.idle_frame_width = 33
        self.idle_frame_height = 45
        self.running_frame_width = 36
        self.running_frame_height = 42
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
        self.idle_animation_speed = 24  # Number of frames per idle image
        self.running_animation_speed = 8  # Number of frames per running image
        self.idle_animation_counter = 0  # Frame counter for idle animation speed
        self.running_animation_counter = 0  # Frame counter for running animation speed
        self.last_update = pygame.time.get_ticks()
        self.facing_right = True  # Track direction
        self.last_direction = 'right'  # Track the last direction the player was facing
        self.acceleration = 0.  # Rate of acceleration
        self.deceleration = 0.2  # Rate of deceleration
        self.max_speed = 6  # Maximum movement speed
        self.moving = False  # Whether the player is moving
        self.on_wall = False  # Whether the player is touching a wall
        self.wall_sticking = False  # Whether the player is sticking to a wall

    def get_idle_image(self, frame):
        # Adjust the idle frame dimensions
        idle_frame = pygame.Surface((self.idle_frame_width, self.idle_frame_height), pygame.SRCALPHA).convert_alpha()
        idle_frame.blit(self.idle_spritesheet[frame], (0, 0))
        return idle_frame

    def get_running_image(self, frame):
        # Adjust the running frame dimensions
        running_frame = pygame.Surface((self.running_frame_width, self.running_frame_height), pygame.SRCALPHA).convert_alpha()
        running_frame.blit(self.running_frames[frame], (0, 0))
        return running_frame

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.move_left()
        elif keys[pygame.K_d]:
            self.move_right()
        else:
            self.stop()

        if self.moving:
            # Update frame index to cycle through the running frames
            self.running_animation_counter += 1
            if self.running_animation_counter >= self.running_animation_speed:
                self.running_animation_counter = 0
                self.running_frame = (self.running_frame + 1) % len(self.running_frames)
                self.image = self.get_running_image(self.running_frame)
        else:
            # If not moving, reset frame index to 0 for next movement
            self.running_frame = 0
            self.idle_animation_counter += 1
            if self.idle_animation_counter >= self.idle_animation_speed:
                self.idle_animation_counter = 0
                self.idle_frame = (self.idle_frame + 1) % len(self.idle_spritesheet)
                self.image = self.get_idle_image(self.idle_frame)
        
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
        self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT - self.rect.height))

        # Handle facing direction
        if self.facing_right and self.last_direction != 'right':
            self.image = pygame.transform.flip(self.image, True, False)  # Flip image if facing left
            self.last_direction = 'right'
        elif not self.facing_right and self.last_direction != 'left':
            self.image = pygame.transform.flip(self.image, True, False)  # Flip image if facing right
            self.last_direction = 'left'

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
            jump_sound.play()  # Play jump sound
        elif self.jumps < self.max_jumps:
            self.change_y = self.jump_speed
            self.jumps += 1
            jump_sound.play()  # Play jump sound

    def move_left(self):
        if not self.dashing:
            if self.change_x < 0:  # If already moving left
                self.change_x -= self.acceleration  # Accelerate further left
            else:  # If not moving left
                self.change_x = -self.max_speed  # Start moving left at max speed
            self.facing_right = False  # Face left
            self.moving = True  # Set moving to true
            if self.last_direction == 'right':
                self.image = pygame.transform.flip(self.image, True, False)  # Flip image if previously facing right
                self.last_direction = 'left'

    def move_right(self):
        if not self.dashing:
            if self.change_x > 0:  # If already moving right
                self.change_x += self.acceleration  # Accelerate further right
            else:  # If not moving right
                self.change_x = self.max_speed  # Start moving right at max speed
            self.facing_right = True  # Face right
            self.moving = True  # Set moving to true
            if self.last_direction == 'left':
                self.image = pygame.transform.flip(self.image, True, False)  # Flip image if previously facing left
                self.last_direction = 'right'

    def stop(self):
        if not self.dashing:
            self.change_x = 0  # Reset horizontal movement speed to zero when key is released
            self.moving = False  # Set moving to false
            self.wall_sticking = False  # Stop sticking to the wall when key is released

    def dash(self, direction):
        if pygame.time.get_ticks() - self.dash_cooldown_time >= self.dash_cooldown:
            self.dashing = True
            self.change_x = direction * self.dash_speed
            self.dash_time = pygame.time.get_ticks()
            self.dash_cooldown_time = pygame.time.get_ticks()
            dash_sound.play()  # Play dash sound

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
                elif self.change_y < 0:  # Jumping up
                    self.rect.top = platform.rect.bottom
                    self.change_y = 0

    def wall_stick(self):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_a] and self.change_x < 0) or (keys[pygame.K_d] and self.change_x > 0):
            self.wall_sticking = True
            self.change_y = 0  # Stop falling

def generate_random_clouds(num_clouds, cloud_images):
    clouds = pygame.sprite.Group()
    for _ in range(num_clouds):
        x = random.randint(-SCREEN_WIDTH, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT // 2)
        speed = random.uniform(0.5, 2)
        image_path = random.choice(cloud_images)
        cloud = Cloud(x, y, speed, image_path)
        clouds.add(cloud)
    return clouds

def game_loop():
    global platforms, all_sprites, decor_group
    platforms = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()
    decor_group = pygame.sprite.Group()

    platform1 = Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40, 'grass')
    platform2 = Platform(200, 400, 200, 20, 'grass')
    platform3 = Platform(400, 300, 200, 20, 'grass')
    wall = Platform(600, 200, 40, 400, 'stone')  # Adding a wall
    platforms.add(platform1, platform2, platform3, wall)

    cloud_images = ['assets/clouds/cloud_1.png', 'assets/clouds/cloud_2.png']
    clouds = generate_random_clouds(10, cloud_images)

    player = Player(platforms)

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
                    player.last_key_time['left'] = current_time
                elif event.key == pygame.K_d:
                    if current_time - player.last_key_time['right'] < player.double_tap_threshold:
                        player.dash(1)
                    player.last_key_time['right'] = current_time
                elif event.key == pygame.K_w:
                    player.jump()

        all_sprites.update()
        clouds.update()

        # Draw the background image
        screen.blit(background_image, (0, 0))

        # Draw clouds
        clouds.draw(screen)

        all_sprites.draw(screen)
        decor_group.draw(screen)  # Draw decor elements separately

        # Draw ghost trail
        for ghost_image, ghost_pos in player.ghost_trail:
            screen.blit(ghost_image, ghost_pos)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    game_loop()
