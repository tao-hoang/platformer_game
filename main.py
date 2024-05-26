import pygame
import sys
import random

pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ninjump")

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
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        if block_type == 'grass':
            block_image = grass_block_image
        elif block_type == 'stone':
            block_image = stone_block_image
        elif block_type == 'dirt':
            block_image = dirt_block_image

        block_image = pygame.transform.scale(block_image, (16, 16))

        for i in range(0, width, 16):
            for j in range(0, height, 16):
                self.image.blit(block_image, (i, j))

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Player(pygame.sprite.Sprite):
    def __init__(self, platforms):
        super().__init__()
        self.idle_spritesheet = [pygame.image.load(f'assets/player/idle/0.png').convert_alpha(), pygame.image.load(f'assets/player/idle/1.png').convert_alpha() ]
        self.running_frames = [pygame.image.load(f'assets/player/running/0.png').convert_alpha(), pygame.image.load(f'assets/player/running/1.png').convert_alpha()]
        self.image = self.get_idle_image(0)
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.y = SCREEN_HEIGHT - self.rect.height - 100
        self.change_x = 0
        self.change_y = 0
        self.gravity = 0.6
        self.jump_speed = -12
        self.platforms = platforms
        self.jumps = 0
        self.max_jumps = 2
        self.dash_speed = 80
        self.dash_duration = 40
        self.dash_cooldown = 30
        self.dashing = False
        self.dash_time = 0
        self.dash_cooldown_time = 0
        self.last_key_time = {'left': 0, 'right': 0}
        self.double_tap_threshold = 200
        self.ghost_trail = []
        self.idle_frame = 0
        self.running_frame = 0
        self.idle_animation_speed = 24
        self.running_animation_speed = 8
        self.idle_animation_counter = 0
        self.running_animation_counter = 0
        self.last_update = pygame.time.get_ticks()
        self.facing_right = True
        self.last_direction = 'right'
        self.acceleration = 0
        self.deceleration = 0
        self.max_speed = 6
        self.moving = False
        self.on_wall = False
        self.wall_sticking = False
        self.health = 100  # Player health
        self.score = 0  # Player score

    def get_idle_image(self, frame):
        idle_frame = pygame.Surface((33, 45), pygame.SRCALPHA).convert_alpha()
        idle_frame.blit(self.idle_spritesheet[frame], (0, 0))
        return idle_frame

    def get_running_image(self, frame):
        running_frame = pygame.Surface((36, 42), pygame.SRCALPHA).convert_alpha()
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
            self.running_animation_counter += 1
            if self.running_animation_counter >= self.running_animation_speed:
                self.running_animation_counter = 0
                self.running_frame = (self.running_frame + 1) % len(self.running_frames)
                self.image = self.get_running_image(self.running_frame)
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.image, True, False)
        else:
            self.running_frame = 0
            self.idle_animation_counter += 1
            if self.idle_animation_counter >= self.idle_animation_speed:
                self.idle_animation_counter = 0
                self.idle_frame = (self.idle_frame + 1) % len(self.idle_spritesheet)
                self.image = self.get_idle_image(self.idle_frame)
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.image, True, False)

        if self.dashing:
            if pygame.time.get_ticks() - self.dash_time >= self.dash_duration:
                self.dashing = False
                self.change_x = 0
                self.ghost_trail = []
            else:
                ghost_image = self.image.copy()
                ghost_image.set_alpha(100)
                self.ghost_trail.append((ghost_image, self.rect.topleft))

        self.calc_gravity()

        self.rect.y += self.change_y
        self.check_collision('y')

        self.rect.x += self.change_x
        self.check_collision('x')

        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        
        if self.rect.top > SCREEN_HEIGHT:
            self.die()

        # Move screen down if player is high enough
        if self.rect.top <= SCREEN_HEIGHT / 3:
            self.move_screen_down()

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
                self.change_x = -self.max_speed
            else:
                self.change_x = self.max_speed
            jump_sound.play()
        elif self.jumps < self.max_jumps:
            self.change_y = self.jump_speed
            self.jumps += 1
            jump_sound.play()

    def move_left(self):
        if not self.dashing:
            self.change_x = -self.max_speed
            self.facing_right = False
            self.moving = True
            if self.last_direction == 'right':
                self.image = pygame.transform.flip(self.image, True, False)
                self.last_direction = 'left'

    def move_right(self):
        if not self.dashing:
            self.change_x = self.max_speed
            self.facing_right = True
            self.moving = True
            if self.last_direction == 'left':
                self.image = pygame.transform.flip(self.image, True, False)
                self.last_direction = 'right'

    def stop(self):
        if not self.dashing:
            self.change_x = 0
            self.moving = False
            self.wall_sticking = False

    def dash(self, direction):
        if pygame.time.get_ticks() - self.dash_cooldown_time >= self.dash_cooldown:
            self.dashing = True
            self.change_x = direction * self.dash_speed
            self.dash_time = pygame.time.get_ticks()
            self.dash_cooldown_time = pygame.time.get_ticks()
            dash_sound.play()

    def check_collision(self, direction):
        if direction == 'x':
            collisions = pygame.sprite.spritecollide(self, self.platforms, False)
            self.on_wall = False
            for platform in collisions:
                if self.change_x > 0:
                    self.rect.right = platform.rect.left
                    self.on_wall = True
                elif self.change_x < 0:
                    self.rect.left = platform.rect.right
                    self.on_wall = True
            if self.on_wall and self.change_y > 0:
                self.wall_stick()
        elif direction == 'y':
            collisions = pygame.sprite.spritecollide(self, self.platforms, False)
            for platform in collisions:
                if self.change_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.change_y = 0
                    self.jumps = 0
                elif self.change_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.change_y = 0

    def wall_stick(self):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_a] and self.change_x < 0) or (keys[pygame.K_d] and self.change_x > 0):
            self.wall_sticking = True
            self.change_y = 0

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.die()

    def die(self):
        print("Player has died")
        pygame.quit()
        sys.exit()

    def move_screen_down(self):
        self.rect.y += 1
        for platform in self.platforms:
            platform.rect.y += 1
            if platform.rect.top > SCREEN_HEIGHT:
                platform.kill()
        self.score += 1
        generate_platforms(self.platforms)

class Cloud(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, image_path):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 0.5

    def update(self):
        self.rect.x += self.speed
        if self.rect.x > SCREEN_WIDTH:
            self.rect.x = -self.rect.width

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

def generate_platforms(platforms):
    while len(platforms) < 10:
        x = random.randint(0, SCREEN_WIDTH - 100)
        y = random.randint(-SCREEN_HEIGHT, 0)
        platform = Platform(x, y, 100, 20, 'grass')
        platforms.add(platform)
        all_sprites.add(platform)

def game_loop():
    global platforms, all_sprites
    platforms = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()

    platform1 = Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40, 'grass')
    platforms.add(platform1)
    all_sprites.add(platform1)

    cloud_images = ['assets/clouds/cloud_1.png', 'assets/clouds/cloud_2.png']
    clouds = generate_random_clouds(10, cloud_images)

    player = Player(platforms)

    all_sprites.add(player)
    all_sprites.add(clouds)

    generate_platforms(platforms)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    player.jump()

                if event.key == pygame.K_a:
                    current_time = pygame.time.get_ticks()
                    if current_time - player.last_key_time['left'] < player.double_tap_threshold:
                        player.dash(-1)
                    player.last_key_time['left'] = current_time

                if event.key == pygame.K_d:
                    current_time = pygame.time.get_ticks()
                    if current_time - player.last_key_time['right'] < player.double_tap_threshold:
                        player.dash(1)
                    player.last_key_time['right'] = current_time

        all_sprites.update()

        screen.blit(background_image, (0, 0))
        clouds.update()
        clouds.draw(screen)
        all_sprites.draw(screen)

        if player.dashing:
            for ghost_image, position in player.ghost_trail:
                screen.blit(ghost_image, position)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()